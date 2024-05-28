#!/usr/bin/env python3
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from std_msgs.msg import Int32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import rospy
import requests
import json
import schedule
import time
import threading
import io
import base64
import cv2
import numpy as np

app = Flask(__name__)
result = None
result_img = None

def call_api():
    global result
    url = 'http://127.0.0.1:8042/restgatewaydemo/getmultcoords'
    data = {}
    headers = {'Content-type': 'application/json'}
    #print(data)
    response = requests.post(url, data=json.dumps(data), headers=headers)
    result = response.json()
    #print(result)
    result["values"].pop()
    with open('result.json', 'w') as f:
        json.dump(result, f)

def call_api_image():
    global result_img
    url = 'http://127.0.0.1:8042/restgatewaydemo/getimageresult'
    data = {}
    headers = {'Content-type': 'application/json'}

    response = requests.post(url, data=json.dumps(data), headers=headers)
    result_img = response.json()
    with open('result_img.json', 'w') as f:
        json.dump(result_img["b64img"], f)

def schedule_api_call():
    while True:
        schedule.run_pending()
        time.sleep(1)

        # schedule.cancel_job(call_api)

if __name__ == '__main__':
    call_api() # initial call
    schedule.every(0.1).seconds.do(call_api) # Schedule call every half second
    schedule.every(0.1).seconds.do(call_api_image)

    t = threading.Thread(target=schedule_api_call)
    t.start()
    
    @app.route('/api/result')
    def get_result():
        return str(result['values'][0]) + "," + str(result["values"][1])

    @app.route('/api/image')
    def get_image():
        if result_img is not None:
            return "data:image/jpg;base64, " + result_img["b64img"].replace('"','')
        else:
            return "Not found"

    @app.route('/')
    def show_result():
        return render_template('imagen.html')

    app.run(debug=True, port=8002)