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

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for tello_action service...')

        self.timer = self.create_timer(1.0, self.timer_callback)
        self.timer_time: int = 0
        self.landed = False

    def timer_callback(self):
        self.timer_time += 1

        # Step 1: enter SDK mode
        if self.timer_time == 1:
            req = TelloAction.Request()
            req.cmd = 'command'
            future = self.cli.call_async(req)
            future.add_done_callback(self.callback_response)
            self.get_logger().info("command mode")

        # Step 2: takeoff
        if self.timer_time == 5:
            req = TelloAction.Request()
            req.cmd = 'takeoff'
            future = self.cli.call_async(req)
            future.add_done_callback(self.callback_response)
            self.get_logger().info("takeoff")
            self.landed = False

        if self.timer_time == 15:
            req = TelloAction.Request()
            req.cmd = 'cw 360'
            future = self.cli.call_async(req)
            future.add_done_callback(self.callback_response)
            self.get_logger().info("turn")

        # Step 3: land
        if self.timer_time > 20 and not self.landed:
            req = TelloAction.Request()
            req.cmd = 'land'
            future = self.cli.call_async(req)
            future.add_done_callback(self.callback_response)
            self.get_logger().info("land")

    def callback_response(self, future):
        try:
            response = future.result()
            self.get_logger().info(f"Response received: {response}")
        except Exception as e:
            self.get_logger().error(f"Service call failed: {e}")


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