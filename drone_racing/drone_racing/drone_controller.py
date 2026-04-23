import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from geometry_msgs.msg import Twist
import time
from tello_msgs.srv import TelloAction
from tello_msgs.msg import TelloResponse
from tello_msgs.msg import FlightData
from drone_racing_msgs.msg import GateTarget
from simple_pid import PID
from enum import Enum
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

class States(Enum):
    SEARCHING = 0
    CENTERING_FAR = 1
    CENTERING_TRANSITION = 2
    STOPPING = 3
    CENTERING_CLOSE = 4
    GATE_FLYTHROUGH = 5

class DroneController(Node):

    def __init__(self):

        #Initialize ros class thingy
        super().__init__('drone_controller')
        
        is_in_gazebo = False

        custom_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        # Connect to drone
        self.cli = self.create_client(TelloAction, 'tello_action')
        #cmd_vel publisher
        self.vel_publisher = self.create_publisher(Twist, "cmd_vel", custom_qos)
        #TelloAction response subscriber
        self.response_subscriber = self.create_subscription(TelloResponse, "tello_response", self.command_response_callback, 1)
        #FlightData Drone info subscriber (TOF)
        self.response_subscriber = self.create_subscription(FlightData, "flight_data", self.flight_data_callback, custom_qos)
        #GateTarget response subscriber
        self.gate_subscriber = self.create_subscription(GateTarget, "target", self.gate_callback, 1)
        #Stop response subscriber
        self.stop_subscriber = self.create_subscription(GateTarget, "stop", self.stop_callback, 1)
        #Takeoff and landing flags
        self.takeoff_complete: bool = False
        self.landing: bool = False
        
        #TelloAction response vars
        self.sending_command: bool = False
        self.sent_command: str = ""
        
        #Tick counter
        self.i: int = 0

        #Altitude
        self.tof: int = 0

        #Centered once
        self.centered_x: bool = False
        self.centered_ticks: int = 0

        #Detected gate
        self.gate: GateTarget | None = None
        self.gate_timer: int = 0
        self.gate_max_lose_time: int = 30
        self.gate_counter: int = 0
        self.stop: GateTarget | None = None
        self.stop_lose_timer: int = 0
        self.stop_max_lose_time: int = 30

        # PID controller
        self.pid_altitude_gate = PID(0.002, 0.0, 0.0, setpoint=235, output_limits=(-1.0, 1.0))
        self.pid_altitude_tof = PID(0.02, 0.0, 0.0, setpoint=110, output_limits=(-1.0, 1.0))
        self.pid_rotation = PID(0.0015, 0.0, 0.0, setpoint=480, output_limits=(-1.0, 1.0))

        
        #State machine
        self.state = States.SEARCHING
        self.previous_state = States.SEARCHING
        self.flythrough_time: int = 0

        #Wait for drone to be ready
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for tello_action service...')
        
        #Reset cmd_vel just in case
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        msg.angular.x = 0.0
        msg.angular.y = 0.0
        msg.angular.z = 0.0
        self.vel_publisher.publish(msg)

        self.takeoff()
        
        #Start tick timer
        self.tick_timer = self.create_timer(0.03, self.tick)
    
    def tick(self):
        if not self.takeoff_complete:
            return
        self.i += 1
        self.get_logger().info(str(self.state))

        #self.rotate(-0.3)
        self.handle_state_machine()


    def move(self, forward: float = 0.0, left: float = 0.0, up: float = 0.0, rotation: float = 0.0):
        msg = Twist()
        msg.linear.x = forward
        msg.linear.y = left
        msg.linear.z = up
        msg.angular.z = rotation
        self.vel_publisher.publish(msg)

    
    def zero_velocity(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.linear.z = 0.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Reset")
    
    
    def land(self):
        self.move()
        time.sleep(1.0)
        self.send_command("land")
        self.landing = True

    def takeoff(self):
        self.send_command("takeoff")

    #Returns if the command was sent, only one command can be sent at a time!
    def send_command(self, command: str) -> bool:
        if self.sending_command: # return if already sending command
            return False
        self.sent_command = command
        req = TelloAction.Request()
        req.cmd = command
        self.cli.call_async(req)
        self.get_logger().info(f"Sending command {command}")
        return True
    
    #Handles TelloResponse from TelloAction commands
    def command_response_callback(self, msg: TelloResponse):
        if msg.rc == 3:
            self.get_logger().info(f"Drone failed to respond to command \"{self.sent_command}\". rc={msg.rc}")
        if msg.rc == 2:
            self.get_logger().info(f"Response to command \"{self.sent_command}\" was an error. rc={msg.rc}")
        if msg.rc == 1:
            match self.sent_command:
                case "takeoff": 
                    self.get_logger().info("Takeoff and stabilization complete.")
                    self.takeoff_complete = True
                case "land":
                    self.get_logger().info("Landing complete.")
        self.sending_command = False
    
    def flight_data_callback(self, msg: FlightData):
        self.tof = msg.tof

    def gate_callback(self, msg: GateTarget):
        if (self.gate_counter == 2 and msg.size < 250):
            return
        self.gate = msg
        self.gate_timer = 0
        self.centered_ticks += 1
    
    def stop_callback(self, msg: GateTarget):
        self.stop = msg
        self.stop_lose_timer = 0


    ##################################################################################################################
    #State Machine
    ##################################################################################################################
    def handle_state_machine(self):
        if self.previous_state != self.state:
            self.centered_x = False
            self.flythrough_time = 0
            self.centered_ticks = 0
        
        self.previous_state = self.state
        match self.state:
            case States.SEARCHING:              self.searching()
            case States.CENTERING_FAR:          self.centering_far()
            case States.CENTERING_CLOSE:        self.centering_close()
            case States.GATE_FLYTHROUGH:        self.gate_flythrough()
            case States.STOPPING:               self.stopping()
    

    def searching(self):
        self.get_logger().info("State: SEARCHING")

        # Altitude control
        offset_y = self.tof #-(110.0 - float(self.tof)) / 110.0
        z = self.pid_altitude_tof(offset_y) # Up / Down
        self.get_logger().info(f"TOF = {offset_y}")

        self.move(up=z, rotation=-0.5)
        if self.gate_counter > 3:
            self.state = States.STOPPING
        if self.gate is not None and self.gate_timer < self.gate_max_lose_time:
            self.state = States.CENTERING_FAR


    def centering_close(self):
        self.get_logger().info("State: Centering Close")
        #0,0 is upper left
        camera_size_x = 960
        camera_size_y = 720
        target_offset_y = 125
        # Send the current offset into the PID controller and keep setpoint at 0.
        # simple_pid expects the process variable, not a precomputed error.
        offset_x = self.gate.x #(self.gate.x - (camera_size_x / 2)) / (camera_size_x / 2)
        offset_y = self.gate.y #(self.gate.y - (camera_size_y / 2 - target_offset_y)) / (camera_size_y / 2)
        
        self.gate_timer += 1
        if self.gate_timer >= self.gate_max_lose_time:
            self.state = States.SEARCHING
        
        self.get_logger().info(f"Gate Size: {self.gate.size}")
        if self.gate.size < 400:
            self.state = States.CENTERING_FAR

        z = self.pid_altitude_gate(offset_y) # Up / Down
        rotation = self.pid_rotation(offset_x) # Rotation

        #if self.gate.size < 500:
        #    z = 0.0

        #self.get_logger().info(f"pid sides={rotation:.3f}, pid altitude={z:.3f}")
        self.get_logger().info(f"horizonal ok: {abs(offset_x - 480) < 50}\nvertical ok: {abs(offset_y - 235) < 50}")

        # Fly through gate only when both x and y are centered
        if abs(offset_x - 480) < 30 and abs(offset_y - 235) < 35:
            if self.centered_ticks >= 2:
                self.state = States.GATE_FLYTHROUGH
        else:
            self.centered_ticks = 0

        # Actual movement
        self.move(0.0, 0.0, z, rotation)


    def centering_far(self):
        self.get_logger().info("State: Centering Far")
        # Check if close
        if self.gate.size > 500 and self.gate_counter != 2 and self.gate_counter != 1:
            self.state = States.CENTERING_CLOSE
        elif self.gate.size > 440 and (self.gate_counter == 2 or self.gate_counter == 1):
            self.state = States.CENTERING_CLOSE

        #0,0 is upper left
        camera_size_x = 960
        camera_size_y = 720
        target_offset_y = 125
        # Send the current offset into the PID controller and keep setpoint at 0.
        # simple_pid expects the process variable, not a precomputed error.
        offset_x = self.gate.x #(self.gate.x - (camera_size_x / 2)) / (camera_size_x / 2)
        offset_y = self.tof #-(110.0 - float(self.tof)) / 110.0
        
        self.gate_timer += 1
        if self.gate_timer >= self.gate_max_lose_time:
            self.state = States.SEARCHING
            

        z = self.pid_altitude_tof(offset_y) # Up / Down
        rotation = self.pid_rotation(offset_x) # Rotation
        forward = 0.0

        if self.gate_counter == 3:
            z = 0.0

        self.get_logger().info(f"pid sides={rotation:.3f}, pid altitude={z:.3f}, tof={self.tof}, Offset_y={offset_y}, Offset_x={offset_x}")

        # Move if rotated towards
        if (abs(offset_x - 480) < 50 or                         # Not centered once
            (abs(offset_x - 480) < 100 and self.centered_x)):     # Have centered and is moving

            self.centered_x = True
            match self.gate_counter:
                case 0: forward = 0.3
                case 1: forward = 0.3
                case 2: forward = 0.1
                case 3: forward = 0.3

        # Actual movement
        self.move(forward, 0.0, z, rotation)


    def gate_flythrough(self):
        self.get_logger().info("State: Gate Flythrough")
        self.gate = None
        self.flythrough_time += 1
        
        fly_time: int = 0

        match self.gate_counter:
            case 0: fly_time = 70
            case 1: fly_time = 45
            case 2: fly_time = 45
            case 3: fly_time = 35

        
        if self.flythrough_time >= fly_time:
            self.move()
        else:
            self.move(forward=1.0)

        if self.flythrough_time >= fly_time * 1.5:
            self.gate_counter += 1
            self.state = States.SEARCHING

    def stopping(self):
        self.get_logger().info("State: Stopping")
        offset_y = self.tof - 30
        self.stop_lose_timer += 1

        if self.stop_lose_timer >= self.stop_max_lose_time:
            self.stop = None

        z = self.pid_altitude_tof(offset_y) # Up / Down
        self.get_logger().info(f"TOF with offset = {offset_y}")

        if self.stop is None:
            self.get_logger().info("State: Looking for stop")
            self.move(up=z, rotation=-0.3)
        else:
            self.get_logger().info("State: Rotating to stop")
            offset_x = self.stop.x
            rotation = self.pid_rotation(offset_x) # Rotation
            self.move(rotation=rotation, forward=0.1, up=z)
        
        if self.stop is not None and self.stop.size > 200:
            #STOP
            self.get_logger().info("State: Landing")
            self.move()
            self.land()
            self.state = 10 #Shut down state machine


def main(args=None):
    rclpy.init(args=args)

    drone_controller = DroneController()

    rclpy.spin(drone_controller)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    drone_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()