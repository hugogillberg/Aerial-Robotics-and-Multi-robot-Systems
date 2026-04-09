import rclpy 
from rclpy.node import Node 
from sensor_msgs.msg import Image 
import cv_bridge 
import cv2 
import numpy as np
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

class ImageStream(Node): 
    
    def __init__(self): 
        custom_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )
        
        super().__init__('image_stream')
        self.bridge = cv_bridge.CvBridge() 
        self.subscription = self.create_subscription( 
            Image, '/image_raw', 
            self.image_callback, custom_qos ) 
        self.video_publisher = self.create_publisher(Image, 'video_frame', 10)
        


    def image_callback(self, msg):
        self.get_logger().info("Processing video")
        try:
            cv_image : Image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            if cv_image is None:
                return

            self.video_publisher.publish(cv_image)
            self.get_logger().info("Frame written to video")
        
        except Exception as e:
            self.get_logger().error('Error processing image: %s' % str(e))


    def destroy_node(self):
        super().destroy_node()
    
    

def main(args=None): 
    rclpy.init(args=args) 
    node = ImageStream() 
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Keyboard Interupt")
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()