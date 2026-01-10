import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import String
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError

import cv2
import numpy as np
import subprocess
import shlex
    
class CsiCameraPublisher(Node):
    def __init__(self):
        super().__init__('csi_cam_publsiher')
        qos_profile = QoSProfile(depth=10)
        self.csi_cam_publisher = self.create_publisher(Image, '/csi_camera/image_raw', qos_profile)
        self.csi_cam_compressed_publisher = self.create_publisher(CompressedImage, '/csi_camera/compressed', qos_profile)
        self.cmd = 'rpicam-vid --inline --nopreview -t 0 --codec mjpeg --width 640 --height 480 --framerate 30 -o - --camera 1'
        self.process = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.bridge = CvBridge()
        self.buffer = b""
        self.publish_compressed_img()
        
    def publish_compressed_img(self):
        while True:
            self.buffer += self.process.stdout.read(4096)
            a = self.buffer.find(b'\xff\xd8')
            b = self.buffer.find(b'\xff\xd9')

            if a != -1 and b != -1:
                jpg = self.buffer[a:b+2]
                self.buffer = self.buffer[b+2:]

                bgr_frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                if bgr_frame is not None:
                    cv2.imshow('Camera Stream', bgr_frame)
                    self.csi_cam_publisher.publish(self.bridge.cv2_to_imgmsg(bgr_frame, encoding='bgr8'))
                    self.csi_cam_compressed_publisher.publish(self.bridge.cv2_to_compressed_imgmsg(bgr_frame))

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        process.terminate()
                        cv2.destroyAllWindows()
                        self.destroy_node()
                        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    node = CsiCameraPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT)')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

