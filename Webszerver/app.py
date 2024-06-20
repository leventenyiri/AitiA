from flask import Flask, jsonify
import base64
import datetime

app = Flask(__name__)

def get_base64_image():
    raw_image = emulated_camera()
    # Encode the image data to base64
    encoded_image = base64.b64encode(raw_image).decode('utf-8')
    return encoded_image

def emulated_camera():
    # Open the JPG image
    with open('raspberry-pi-1.jpg', 'rb') as image_file:
        # Read the image file
        image_data = image_file.read()
    return image_data

def emulated_rtc():
    return datetime.datetime.now()

@app.route("/image")
def send_image():
    response = {
        "image_data": get_base64_image(),
        "encoding": "base64",
        "time": emulated_rtc().strftime("%m/%d/%Y, %H:%M:%S")
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(ssl_context='adhoc')
