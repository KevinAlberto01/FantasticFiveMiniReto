#author: AECL

import signal
import threading
from concurrent import futures
import cv2
import base64
import numpy as np

import rospy
from std_msgs.msg import Float64MultiArray, Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import grpc
import sys
sys.path.insert(1, './protos')
import rpc_demo_pb2
import rpc_demo_pb2_grpc

class RPCDemoImpl(rpc_demo_pb2_grpc.RPCDemoServicer):
    def __init__(self):
        self.data = [0,0,0]
        self.img_compressed = None
        self.br = CvBridge()
        rospy.Subscriber('/object_position', Float64MultiArray, self.UpdateData)
        rospy.Subscriber('/detected_image', Image, self.UpdateImage)
        rospy.Subscriber('/aruco_marker_id', Int32, self.IdDetector)
        rospy.Subscriber('/aruco_detected_image', Image, self.ImageUpdated)
        print("Initialized gRPC Server")

    def UpdateData(self, data):
        self.data[0] = data.data[0]
        self.data[1] = data.data[1]
        self.data[2] = data.data[2]
        #print(rospy.get_caller_id() + " / Got data: " + str(self.data))

    def UpdateImage(self, data):
        img_original = self.br.imgmsg_to_cv2(data)
        self.shape = img_original.shape

        self.img_compressed = np.array(cv2.imencode('.jpg', img_original)[1]).tobytes()
        img_base64 = base64.b64encode(self.img_compressed)
    
    def ImageUpdated(self, data):
        img_original1 = self.br.imgmsg_to_cv2(data)
        self.shape1 = img_original1.shape

        self.img_compressed1 = np.array(cv2.imencode('.jpg', img_original1)[1]).tobytes()
        img_base64 = base64.b64encode(self.img_compressed1)

    def IdDetector(self, data):
        result1 = data.data
        rospy.loginfo(f"Received marker ID: {result1}")


    def GetMultCoords(self, request, context):
        print("Got call: " + context.peer())
        results = rpc_demo_pb2.MultCoords()
        results.values.append(self.data[0])
        results.values.append(self.data[1])
        results.values.append(self.data[2])
        #print("hola")
        print(results)
        return results

    def GetImageResult(self, request, context):
        print("GetImage Got call: " + context.peer())
        # img_original = cv2.imread('../isorepublic-red-green-apples-1.jpg')
        # self.img_compressed = np.array(cv2.imencode('.jpg', img_original)[1]).tobytes()
        # self.shape = img_original.shape
        results = rpc_demo_pb2.ImageResult()
        #print(results)
        results.b64img = self.img_compressed
        results.width = self.shape[1]
        results.height = self.shape[0]
        print(results)
        return results

terminate = threading.Event()
def terminate_server(signum, frame):
    print("Got signal {}, {}".format(signum, frame))
    rospy.signal_shutdown('Ending ROS node')
    terminate.set()

if __name__ == '__main__':
    print("-------ROS to gRPC Wrapper--------")
    signal.signal(signal.SIGINT, terminate_server)

    print("Starting ROS node")
    rospy.init_node('object_position_wrapper', anonymous=True)

    print("Starting gRPC Server")
    server_addr = "[::]:7042"
    service = RPCDemoImpl()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc_demo_pb2_grpc.add_RPCDemoServicer_to_server(service, server)
    server.add_insecure_port(server_addr)
    server.start()
    print("gRPC Server listening on " + server_addr)

    print("Running ROS node")
    rospy.spin()

    terminate.wait()
    print("Stopping gRPC Server")
    server.stop(1).wait()
    print("Exited")

