import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from geometry_msgs.msg import Twist
import time
from tello_msgs.srv import TelloAction
from tello_msgs.msg import TelloResponse

class DroneController(Node):

    def __init__(self):
        super().__init__('drone_controller')
        self.cli = self.create_client(TelloAction, 'tello_action')
        self.vel_publisher = self.create_publisher(Twist, "cmd_vel", 1)
        self.response_subscriber = self.create_subscription(TelloResponse, "tello_response", self.response_callback, 1)

        self.takeoff_complete = False
        self.landing = False
        self.i = 0

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for tello_action service...')
        
        #Crank my hog
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
        if self.takeoff_complete:
            move_time = 20
            if self.i < move_time:
                self.move_forward()
            elif not self.landing:
                self.landing = True
                self.land()
            
            self.i += 1


    def response_callback(self, msg: TelloResponse):
        if msg.rc == 1:
            self.takeoff_complete = True

    def takeoff_timer_callback(self):
        if not self.takeoff_complete:
            self.takeoff_complete = True
            self.get_logger().info("Takeoff Complete")

            self.i = 0
            self.landed = False

    def move_forward(self):
        msg = Twist()
        msg.linear.x = 1.0
        self.vel_publisher.publish(msg)
        self.get_logger().info("Forward")
    
    def land(self):
        self.stop()
        time.sleep(1.0)
        self.landed = True
        req = TelloAction.Request()
        req.cmd = "land"
        self.cli.call_async(req)
        self.get_logger().info("Landing")

    def takeoff(self):
        req = TelloAction.Request()
        req.cmd = "takeoff"
        future = self.cli.call_async(req)
        self.get_logger().info("Takeoff")
    
    def stop(self):
        req = TelloAction.Request()
        req.cmd = "stop"
        future = self.cli.call_async(req)
        self.get_logger().info("Stop")

    def callback_response(self, future):
        try:
            response = future.result()
            self.get_logger().info(f"Response received: {response}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")


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