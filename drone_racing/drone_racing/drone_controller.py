import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from geometry_msgs.msg import Twist
import time
from tello_msgs.srv import TelloAction
from tello_msgs.msg import TelloResponse

class DroneController(Node):

    def __init__(self):

        #Init ros class thingy
        super().__init__('drone_controller')

        #TelloAction service client
        self.cli = self.create_client(TelloAction, 'tello_action')
        #cmd_vel publisher
        self.vel_publisher = self.create_publisher(Twist, "cmd_vel", 1)
        #TelloAction response subscriber
        self.response_subscriber = self.create_subscription(TelloResponse, "tello_response", self.command_response_callback, 1)
        
        #Takeoff and landing flags
        self.takeoff_complete: bool = False
        self.landing: bool = False
        
        #TelloAction response vars
        self.sending_command: bool = False
        self.sent_command: str = ""
        
        #Tick counter
        self.i: int = 0

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
        self.tick_timer = self.create_timer(0.1, self.tick)
    
    def tick(self):
        if not self.takeoff_complete:
            return
        self.i += 1

        #Code here :)
        

    def move(self, forward: int = 0, left: int = 0, up: int = 0):
        msg = Twist()
        msg.linear.x = forward
        msg.linear.y = left
        msg.linear.z = up

    def move_forward(self):
        msg = Twist()
        msg.linear.x = 1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Forward")
    
    def move_backward(self):
        msg = Twist()
        msg.linear.x = -1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Backward")
    
    def move_left(self):
        msg = Twist()
        msg.linear.y = 1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Left")

    def move_right(self):
        msg = Twist()
        msg.linear.y = -1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Right")
    
    def move_up(self):
        msg = Twist()
        msg.linear.z = 1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Up")
    
    def move_down(self):
        msg = Twist()
        msg.linear.z = -1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Down")
    
    def zero_velocity(self):
        msg = Twist()
        msg.linear.x = 0
        msg.linear.y = 0
        msg.linear.z = 0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Velocity Reset")
    
    def land(self):
        self.stop()
        time.sleep(1.0)
        self.send_command("land")
        self.landing = True

    def takeoff(self):
        self.send_command("takeoff")
    
    def stop(self):
        self.send_command("stop")

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