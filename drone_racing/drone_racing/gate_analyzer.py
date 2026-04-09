import rclpy
from rclpy.node import Node
from rclpy.timer import Timer
from yolo_msgs.msg import DetectionArray
from yolo_msgs.msg import Detection
from yolo_msgs.msg import BoundingBox2D
from drone_racing_msgs.msg import GateTarget
import time
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, QoSPresetProfiles

class GateAnalyzer(Node):

    def __init__(self):

        #Initialize ros class thingy
        super().__init__('gate_analyzer')
        print("Starting Gate analyzer")
        
        custom_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE
        )

        #cmd_vel publisher
        self.gate_publisher = self.create_publisher(GateTarget, "target", 1)
        #TelloAction response subscriber - use absolute topic path
        self.response_subscriber = self.create_subscription(DetectionArray, "yolo/tracking", self.detection_callback, custom_qos)
        print(f"Init done - Subscribed to topic: {self.response_subscriber.topic_name}")
        print(f"Node name: {self.get_name()}")
    

    def detection_callback(self, msg):
        print("Detection Callback")
        detections: list[Detection] = msg.detections
        if detections == False:
            return

        gates: list[GateTarget] = []
        for item in detections:
            bounding_box: BoundingBox2D = item.bbox
            class_name: str = item.class_name
            size: int = int(bounding_box.size.x)
            position_x: int = int(bounding_box.center.position.x)
            position_y: int = int(bounding_box.center.position.y)

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
        
        self.get_logger().info(f"Biggest Gate {biggest_gate}")
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