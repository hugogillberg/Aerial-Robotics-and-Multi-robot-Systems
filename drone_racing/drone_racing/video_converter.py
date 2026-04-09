import rclpy 
from rclpy.node import Node 
from sensor_msgs.msg import Image 
import cv_bridge 
import cv2 
import numpy as np
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import os

class ImageToVideoConverter(Node): 
    
    def __init__(self): 
        custom_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE
        )
        
        super().__init__('video_converter')
        self.get_logger().info("Starting video converter node")
        self.bridge = cv_bridge.CvBridge()
        self.frame = 0
        self.subscription = self.create_subscription( 
            Image, '/image_raw', 
            self.image_callback, custom_qos ) 
        self.video_writer = None
        


    def image_callback(self, msg):
        self.get_logger().info("Processing video")
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            if cv_image is None:
                return

            if self.video_writer is None:
                self.init_video_writer(cv_image)
            
            self.video_writer.write(cv_image)
            self.get_logger().info("Frame written to video")

            # Images
            if self.frame %10 == 0:
                image_filename = f"recording/frame_{self.frame}.png"
                print(self.frame)
                cv2.imwrite(image_filename, cv_image)
            self.frame += 1
        
        except Exception as e:
            self.get_logger().error('Error processing image: %s' % str(e))


    def init_video_writer(self, image):
        try:
            folder = 'recording'
            if not os.path.exists(folder):
                os.makedirs(folder)

            # Video
            height, width, _ = image.shape
            video_filename = 'recording/output_video.mp4'
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 30  # Frames per second

            self.video_writer = cv2.VideoWriter(
                video_filename, 
                fourcc, 
                fps, 
                (width, height))
            
        except Exception as e:
            self.get_logger().error('Error initializing video writer: %s' % str(e))


    def destroy_node(self):
        if self.video_writer is not None:
            print("Shutting down video converter")
            self.video_writer.release()
        super().destroy_node()
    
    

def main(args=None): 
    rclpy.init(args=args) 
    node = ImageToVideoConverter() 
    
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