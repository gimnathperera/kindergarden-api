from tensorflow import keras
from flask import Flask, request, jsonify
import os
from flask_cors import CORS

from keras.models import load_model 
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg16 import preprocess_input


# Disable scientific notation for clarity
np.set_printoptions(suppress=True)

# Load the models
letter_model = load_model("sinhala_letter_model.h5", compile=False)

# Load the labels
letter_class_names = open("labels.txt", "r").readlines()

APP_ROOT = os.path.abspath(os.path.dirname(__file__))


def detect_image(file_path):
    img = image.load_img(file_path, target_size=(224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)  # Preprocess the image to match VGG16's requirements
    prediction = letter_model.predict(img)

    index = np.argmax(prediction)
    class_name = letter_class_names[index].strip()
    confidence_score = prediction[0][index]


    return class_name, confidence_score



# Init app
app = Flask(__name__)
CORS(app)



# Image prediction endpoint
@app.route('/api/predict', methods=['POST'])
def get_disease_prediction():
    target = os.path.join(APP_ROOT, 'images/')

    if not os.path.isdir(target):
        os.mkdir(target)

    file = request.files.get('file')
    filename = file.filename
    destination = '/'.join([target, filename])

    file.save(destination)
    class_name, confidence_score = detect_image(f"./images/{filename}")

    data = {'className':class_name, 
    'confidenceScore':str(confidence_score)
    }

    return jsonify(data)


# Run Server
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=False)