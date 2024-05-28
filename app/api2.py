from flask import Flask, jsonify, render_template
from flask_cors import CORS
import rospy
from std_msgs.msg import Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import threading
import io
import base64
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)
bridge = CvBridge()

current_image = None
current_ids = []

def image_callback(msg):
    global current_image
    current_image = bridge.imgmsg_to_cv2(msg, "bgr8")

def id_callback(msg):
    global current_ids
    current_ids.append(msg.data)

@app.route('/api/image')
def get_image():
    if current_image is not None:
        _, buffer = cv2.imencode('.jpg', current_image)
        img_str = base64.b64encode(buffer).decode('utf-8')
        return jsonify({"image": img_str})
    else:
        return jsonify({"image": ""})

@app.route('/api/ids')
def get_ids():
    return jsonify({"ids": current_ids})

@app.route('/')
def index():
    # Render the HTML file
    return render_template('app2.html')

def ros_listener():
    rospy.init_node('web_listener', anonymous=True)
    rospy.Subscriber('/aruco_detected_image', Image, image_callback)
    rospy.Subscriber('/aruco_marker_id', Int32, id_callback)
    rospy.spin()

if __name__ == '__main__':
    threading.Thread(target=ros_listener).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
