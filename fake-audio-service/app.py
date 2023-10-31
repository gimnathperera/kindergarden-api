import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import numpy as np
from tensorflow import keras
import librosa
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
MODEL_FILE = "audio_model.h5"
LABELS = ['Amma', 'Pusa', 'Aliya', 'Wathura', 'Mala']

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

loaded_model = keras.models.load_model(MODEL_FILE, compile=False)

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_mp3_to_wav(mp3_path, wav_path):
    # Load the MP3 audio using pydub
    audio = AudioSegment.from_mp3(mp3_path)

    # Export the audio as WAV
    audio.export(wav_path, format="wav")



def process_audio(wav_path):
    # Load the audio file using librosa
    audio, sr = librosa.load(wav_path, sr=None)

    # Calculate the spectrogram
    spectrogram = librosa.feature.melspectrogram(y=audio, sr=sr)

    # Resize the spectrogram to a fixed size (e.g., 128x128)
    resized_spectrogram = np.zeros((128, 128))
    if spectrogram.shape[1] < 128:
        resized_spectrogram[:, :spectrogram.shape[1]] = spectrogram
    else:
        resized_spectrogram = spectrogram[:, :128]

    # Normalize the spectrogram
    normalized_spectrogram = (resized_spectrogram - np.min(resized_spectrogram)) / (np.max(resized_spectrogram) - np.min(resized_spectrogram))

 
    audio_data = normalized_spectrogram.reshape(1, 128, 128, 1)

    return audio_data

def get_audio_prediction(mp3_file_path):
    wav_audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.wav')
    convert_mp3_to_wav(mp3_file_path, wav_audio_path)

    audio_data = process_audio(wav_audio_path)
    prediction_result = loaded_model.predict(np.array(audio_data))

    predicted_class = LABELS[np.argmax(prediction_result)]
    predicted_probability = float(np.max(prediction_result))

    return predicted_class, predicted_probability

@app.route("/api/v1/audio", methods=["POST"])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file and allowed_file(file.filename):
        category = request.form.get('category')
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        prediction = get_audio_prediction(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if category in LABELS:
            if prediction[0] == category:
                return jsonify({'msg': 'correct', 'marks': 1, 'recognized_class': prediction[0], 'probability': prediction[1]}), 200
            return jsonify({'msg': 'incorrect', 'marks': 0, 'recognized_class': prediction[0], 'probability': prediction[1]}), 200
        else:
            return jsonify({'msg': 'wrong', 'marks': 0, 'recognized_class': prediction[0], 'probability': prediction[1]}), 200

    return jsonify({'error': 'Invalid file type (allowed: .mp3)'}), 400

if __name__ == '__main__':
    app.run(debug=True)
