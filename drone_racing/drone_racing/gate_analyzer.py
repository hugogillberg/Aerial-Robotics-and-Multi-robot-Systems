import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from yolo_msgs.msg import DetectionArray
from yolo_msgs.msg import Detection
from yolo_msgs.msg import BoundingBox2D
from drone_racing_msgs.msg import GateTarget
import time

class GateAnalyzer(Node):

    def __init__(self):

        #Initialize ros class thingy
        super().__init__('gate_analyzer')

        #cmd_vel publisher
        self.gate_publisher = self.create_publisher(GateTarget, "target", 1)
        #TelloAction response subscriber
        self.response_subscriber = self.create_subscription(DetectionArray, "yolo/detections", self.detection_callback, 1)
    

    def detection_callback(self, msg: DetectionArray):
        detections: list[Detection] = msg.detections
        
        gates: list[GateTarget] = []
        for item in detections:
            bounding_box: BoundingBox2D = item.bbox
            class_name: str = item.class_name
            size: int = bounding_box.size.x
            position_x: int = bounding_box.center.position.x
            position_y: int = bounding_box.center.position.y

            gate_target = GateTarget()
            gate_target.class_name = class_name
            gate_target.size = size
            gate_target.x = position_x
            gate_target.y = position_y

            gates.append(gate_target)
        
        #Check biggest size
        biggest: int = 0
        biggest_gate = GateTarget()
        for gate_target in gates:
            if gate_target.size > biggest:
                biggest = gate_target.size
                biggest_gate = gate_target
        
        self.gate_publisher.publish(biggest_gate)


def main(args=None):
    rclpy.init(args=args)

    gate_analyzer = GateAnalyzer()

    rclpy.spin(gate_analyzer)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    gate_analyzer.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()