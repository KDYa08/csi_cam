import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from std_msgs.msg import String
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge, CvBridgeError
from ament_index_python.packages import get_package_share_directory

import cv2
import numpy as np
import subprocess
import shlex
import pickle
import os

class CsiCameraPublisher(Node):
    def __init__(self):
        super().__init__('csi_cam_publsiher')
        qos_profile = QoSProfile(depth=10)
        self.csi_cam_publisher = self.create_publisher(Image, '/csi_camera_1/image_raw', qos_profile)
        self.csi_cam_compressed_publisher = self.create_publisher(CompressedImage, '/csi_camera_1/compressed', qos_profile)
        self.cmd = 'rpicam-vid --inline --nopreview -t 0 --codec mjpeg --width 640 --height 480 --framerate 30 -o - --camera 0'
        self.process = subprocess.Popen(shlex.split(self.cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.bridge = CvBridge()
        self.buffer = b""
        print(os.getcwd())
        with open('../calibration/camera_calibration.pkl', 'rb') as f:
            calibration_data = pickle.load(f)
        
        self.mtx = calibration_data['camera_matrix']
        self.dist = calibration_data['dist_coeffs']        
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
                    #cv2.imshow('Camera Stream', bgr_frame)

                    h, w = bgr_frame.shape[:2]
                    
                    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(self.mtx, self.dist, (w,h), 1, (w,h))
                    dst = cv2.undistort(bgr_frame, self.mtx, self.dist, None, newcameramtx)
                    x, y, w, h = roi
                    if all(v > 0 for v in [x, y, w, h]):
                        dst = dst[y:y+h, x:x+w]

                    dst = cv2.flip(bgr_frame, -1)
                    self.csi_cam_publisher.publish(self.bridge.cv2_to_imgmsg(dst, encoding='bgr8'))
                    self.csi_cam_compressed_publisher.publish(self.bridge.cv2_to_compressed_imgmsg(dst))
                    #self.get_logger().info('success')
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        process.terminate()
                        cv2.destroyAllWindows()
                        self.destroy_node()
                        rclpy.shutdown()
                else:
                    self.get_logger().warn("Camera Not Detect!")

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

