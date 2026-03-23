import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from std_msgs.msg import String
import time
from tello_msgs.srv import TelloAction

class DroneController(Node):

    def __init__(self):
        super().__init__('drone_controller')
        self.cli = self.create_client(TelloAction, 'tello_action')
        self.req = TelloAction.Request()
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.timer_time: int = 0


    def timer_callback(self):
        self.timer_time += 1

        if self.timer_time == 2:
            self.req.cmd = 'takeoff'
            self.cli.call_async(self.req)
            print("takeoff")
        
        if self.timer_time == 7:
            self.req.cmd = 'land'
            self.cli.call_async(self.req)
            print("land")



def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = DroneController()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()