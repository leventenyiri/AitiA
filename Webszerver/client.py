import requests
from PIL import Image
import io
import base64

# URL of the Flask server endpoint
url = "https://localhost:5000/image"

# Make a request to the Flask server
response = requests.get(url, verify=False)  # verify=False to ignore SSL certificate warnings

if response.status_code == 200:
    # Parse the JSON response
    json_response = response.json()
    
    # Extract the base64 image data
    base64_image = json_response["image_data"]
    
    # Decode the base64 image data
    image_data = base64.b64decode(base64_image)
    
    # Convert the image data to an Image object
    image = Image.open(io.BytesIO(image_data))
    
    # Save the image as a BMP file
    image.save("output_image.bmp", format="BMP")
    print("Image saved as output_image.bmp")
else:
    print("Failed to retrieve the image. Status code:", response.status_code)
