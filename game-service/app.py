import datetime
from tensorflow import keras
from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model 
import numpy as np
from pymongo import MongoClient
from sklearn.preprocessing import StandardScaler

# Init app
app = Flask(__name__)
CORS(app)

# Load the models
loaded_model = load_model("model.h5", compile=False)
client = MongoClient("mongodb+srv://root:UGUsVuDMPEzDLIQv@cluster0.gvvm6fh.mongodb.net/") # your connection string

db = client["kindergarden"]
game_collection = db["game"]
users_collection = db["users"]


# get next level
def getNextLevelPrediction(age, duration, stepCount):
    scaler = StandardScaler()
    # Input sample data for prediction
    sample_data = np.array([[age, stepCount, duration]]) 

    # Standardize the sample data using the same scaler used for training
    sample_data_scaled = scaler.transform(sample_data)

    # Make predictions
    predicted_probabilities = loaded_model.predict(sample_data_scaled)
    predicted_class = np.argmax(predicted_probabilities, axis=1) + 1  # Adding 1 to match your original label encoding

    # Convert the predicted class to the corresponding level
    level_mapping = {1: 'Level 1', 2: 'Level 2', 3: 'Level 3', 4: 'Level 4', 5: 'Level 5'}
    predicted_level = level_mapping.get(predicted_class[0], 'Unknown')

    # Print the results
    print(f"Predicted Class: {predicted_class[0]}")
    print(f"Predicted Level: {predicted_level}")

    return predicted_level
    


# game level prediction
@app.route("/api/v1/game-records", methods=["POST"])
def add_game_record():
    game_record = request.get_json()  
    game_record["username"] = game_record["username"]
    game_record["level"] = game_record["level"]
    game_record["duration"] = game_record["duration"]
    game_record["stepCount"] = game_record["stepCount"]
    game_record["created_at"] = datetime.datetime.now()

    existing_child = users_collection.find_one({"username": game_record["username"]})

    # Extract the 'dob' value from the existing_child dictionary
    dob_str = existing_child.get("dob")

    if dob_str:
        # Calculate age from 'dob'
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d")
        today = datetime.datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        level = getNextLevelPrediction(age, game_record["duration"], game_record["stepCount"])
        game_record["level"] = level
    
    game_collection.insert_one(game_record)
    return jsonify({'msg': 'Record added successfully','nextLevel': level}), 200   

     

# Run Server
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=False)