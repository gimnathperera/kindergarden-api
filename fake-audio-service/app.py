import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import AudioFileClip
import speech_recognition as sr
from tensorflow import keras
from keras.models import load_model 

app = Flask(__name__)

# Define the directory where uploaded files will be saved
UPLOAD_FOLDER = 'uploads'
CONFIG_FOLDER = 'config'
ALLOWED_EXTENSIONS = {'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONFIG_FOLDER'] = CONFIG_FOLDER
labels = ['Amma', 'Pusa', 'Aliya', 'Wathura', 'Mala']
loaded_model = load_model("audio_model.h5", compile=False)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_prediction(mp3_file_path):
    # Load the MP3 audio file using moviepy
    audio = AudioFileClip(mp3_file_path)

    # Convert the audio to WAV format (required by SpeechRecognition)
    wav_audio_path = "temp.wav"
    fromatted_audio = audio.write_audiofile(wav_audio_path, codec="pcm_s16le")
    prediction_result = load_model.predict(fromatted_audio)

    predicted_class = prediction_result.argmax()
    predicted_probability = prediction_result.max()
    
    return predicted_class, predicted_probability



@app.route("/api/v1/audio", methods=["POST"])
def upload_audio():
    # Check if a file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Check if the file has a valid extension
    if file and allowed_file(file.filename):
        # Get the 'category' attribute from the request
        category = request.form.get('category')

        # Generate a secure filename and save the file to the UPLOAD_FOLDER
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


        

        # Get text from the audio file
        prediction = get_audio_prediction(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if any(label in prediction for label in labels):

            if prediction == category:
                return jsonify({'msg': 'correct', 'marks': 1}), 200
            return jsonify({'msg': 'incorrect', 'marks': 0}), 200
        else:
            return jsonify({'msg': 'wrong', 'marks': 0}), 200

    return jsonify({'error': 'Invalid file type (allowed: .mp3)'}), 400

if __name__ == '__main__':
    app.run(debug=True)
