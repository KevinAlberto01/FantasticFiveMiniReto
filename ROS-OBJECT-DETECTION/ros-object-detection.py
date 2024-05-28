#author: AECL
#Image from: https://isorepublic.com/photo/red-green-apples-2/

import numpy as np
import cv2
from time import time
import ctypes

import rospy
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

so_file = "../lib/src/cpp_lib_demo.so"

if __name__ == '__main__':
    mylib = ctypes.CDLL(so_file)
    val_in = np.array([0.0, 0.0])
    val_out = np.array([0.0, 0.0])

    rospy.init_node('object_detection', anonymous = True)

    pub_position = rospy.Publisher('/object_position', Float64MultiArray, queue_size = 10)
    pub_image = rospy.Publisher('/detected_image', Image, queue_size=10)

    rate = rospy.Rate(100)

    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])

    bridge = CvBridge()

    while not rospy.is_shutdown():
        
        img = cv2.imread("../isorepublic-red-green-apples-1.jpg", cv2.IMREAD_COLOR)
        img = cv2.resize(img, [640, 480])

        noise = np.zeros([480, 640, 3], dtype = np.uint8)
        cv2.randn(noise, 0, 60)
        img = cv2.add(img, noise)

        hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_image = cv2.inRange(hsv_image, lower_green, upper_green)

        kernel = np.ones([5, 5], np.uint8)
        mask_image = cv2.morphologyEx(mask_image, cv2.MORPH_OPEN, kernel) #erosion and dilation
        mask_image = cv2.morphologyEx(mask_image, cv2.MORPH_CLOSE, kernel) #close holes

        contours, hierachy = cv2.findContours(mask_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        max_area = 0
        max_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                max_contour = contour
        
        if max_contour is not None:
            x,y,w,h = cv2.boundingRect(max_contour)
            center_x = x + w/2
            center_y = y + h/2
            print("Center point: ({}, {})".format(center_x, center_y))
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            val_in = np.array([center_x, center_y])

        cv2.imshow('img', img)

        cv2.waitKey(1)

        res = mylib.Mult100(val_in.ctypes, val_in.shape[0], val_out.ctypes, val_out.shape[0])
        print("Multiplied Center point: " + str(val_out))

        msg = Float64MultiArray()
        msg.data = [val_out[0], val_out[1], time()]
        pub_position.publish(msg)

        # Convertir la imagen a mensaje de ROS
        img_msg = bridge.cv2_to_imgmsg(img, encoding="bgr8")
        pub_image.publish(img_msg)

        rate.sleep()

    cv2.destroyAllWindows()