from flask import Flask, jsonify, url_for
from PIL import Image
import os
import base64


app = Flask(__name__)

# Create a directory for static images if it doesn't exist
os.makedirs('static/images', exist_ok=True)

# Convert the JPEG image to BMP and save it in the static directory
jpeg_image = Image.open('raspberry-pi-1.jpg')
bmp_image_path = os.path.join('static', 'images', 'output_image.bmp')
jpeg_image.save(bmp_image_path)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/image")
def get_image():
    # Open the BMP image
    with open(bmp_image_path, 'rb') as image_file:
        # Read the image file
        image_data = image_file.read()
        # Encode the image data to base64
        encoded_image = base64.b64encode(image_data).decode('utf-8')

    ############################TEST####################################
    decoded_image_data = base64.b64decode(encoded_image)
    
    # Write the decoded image data to a new file to see if the JSON conversion succeeded
    decoded_image_path = os.path.join('static', 'images', 'decoded_image.bmp')
    with open(decoded_image_path, 'wb') as decoded_image_file:
        decoded_image_file.write(decoded_image_data)
    #############################END_TEST###############################

    # Create a JSON response with the base64 image
    response = {
        "image_data": encoded_image,
        "mimetype": "image/bmp"
    }
    return jsonify(response)

#
@app.route("/image_link")
def get_image_link():
    return jsonify({"decoded_image_path": url_for('static', filename='images/decoded_image.bmp', _external=True)})


if __name__ == "__main__":
    app.run(ssl_context='adhoc')
