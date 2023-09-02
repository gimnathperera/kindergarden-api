import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import AudioFileClip
import speech_recognition as sr

app = Flask(__name__)

# Define the directory where uploaded files will be saved
UPLOAD_FOLDER = 'uploads'
CONFIG_FOLDER = 'config'
ALLOWED_EXTENSIONS = {'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONFIG_FOLDER'] = CONFIG_FOLDER
labels = ['Amma', 'Pusa', 'Aliya', 'Wathura', 'Mala']

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def mp3_to_text(mp3_file_path):
    # Load the MP3 audio file using moviepy
    audio = AudioFileClip(mp3_file_path)

    # Convert the audio to WAV format (required by SpeechRecognition)
    wav_audio_path = "temp.wav"
    audio.write_audiofile(wav_audio_path, codec="pcm_s16le")

    # Initialize the SpeechRecognition recognizer
    recognizer = sr.Recognizer()

    # Perform speech recognition on the WAV audio
    with sr.AudioFile(wav_audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        # Use the Google Web Speech API to transcribe the audio to text
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand the audio."
    except sr.RequestError as e:
        return f"Could not request results from Google Web Speech API; {e}"
    finally:
        audio.close()
        os.remove(wav_audio_path)



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

        # Get text from config audio file
        configtext = mp3_to_text(os.path.join(app.config['CONFIG_FOLDER'], category + '.mp3'))

        

        # Get text from the audio file
        text = mp3_to_text(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Check if any label from the 'labels' array is present in the extracted text
        if any(label in text for label in labels):
            

            if text == configtext:
                return jsonify({'msg': 'correct', 'marks': 1}), 200
            return jsonify({'msg': 'incorrect', 'marks': 0}), 200
        else:
            return jsonify({'msg': 'wrong', 'marks': 0}), 200

    return jsonify({'error': 'Invalid file type (allowed: .mp3)'}), 400

if __name__ == '__main__':
    app.run(debug=True)
