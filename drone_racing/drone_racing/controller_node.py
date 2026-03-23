import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
from tello_ros.tello_msgs.srv import TelloAction

class DroneController(Node):

    def __init__(self):
        super().__init__('drone_controller')
        self.cli = self.create_client(TelloAction, 'tello_action')
        self.req = TelloAction.Request()
        time.sleep(2)
        self.req.cmd = 'takeoff'
        self.cli.call(self.req)
        time.sleep(5)
        self.req.cmd = 'land'
        self.cli.call(self.req)
    
    def send_request(self, a, b):
        self.req.a = a
        self.req.b = b
        return self.cli.call_async(self.req)



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