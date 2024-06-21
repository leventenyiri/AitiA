from flask import Flask, jsonify
import base64
import datetime
import random

app = Flask(__name__)

def get_base64_image():
    raw_image = emulated_camera()
    # Encode the image data to base64
    return base64.b64encode(raw_image).decode('utf-8')

def emulated_camera():
    # Selects the random image
    num = random.randint(1,3)
    images = {
        1:'raspberry-pi-1.jpg',
        2: 'raspberry-pi-2.jpg',
        3: 'raspberry-pi-1.jpg'
    }
    # Open the JPG image
    with open(images[num], 'rb') as image_file:
        return image_file.read()

def emulated_rtc():
    return datetime.datetime.now()

@app.route("/image")
def send_image():
    response = {
        "image_data": get_base64_image(),
        "encoding": "base64",
        "time": emulated_rtc().strftime("%Y.%m.%d., %H:%M:%S")
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port= 5000, ssl_context='adhoc', debug = True)
