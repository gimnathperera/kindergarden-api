import datetime
from tensorflow import keras
from flask import Flask, request, jsonify
from flask_cors import CORS
from keras.models import load_model 
import numpy as np
from pymongo import MongoClient
from sklearn.preprocessing import StandardScaler
import pandas as pd

# Init app
app = Flask(__name__)
CORS(app)

# Load the models
loaded_model = load_model("model.h5", compile=False)
client = MongoClient("mongodb+srv://root:UGUsVuDMPEzDLIQv@cluster0.gvvm6fh.mongodb.net/") # your connection string

db = client["kindergarden"]
game_collection = db["game"]
users_collection = db["users"]
data = pd.read_csv('game_dataset.csv')

# get next level
def getNextLevelPrediction(age, duration, stepCount):
    scaler = StandardScaler()
    # Input sample data for prediction
    sample_data = np.array([[age, stepCount, duration]]) 

    X = data[['age', 'stepCount', 'duration']]
    X_scaled = scaler.fit_transform(X)
    
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
    


def determine_next_level(age, step_count, duration):
    if age < 3:
        if step_count > 25 and duration >= 35:
            return 1
        elif step_count == 24 and 29 < duration < 35:
            return 2
        elif 20 <= step_count <= 22 and 23 <= duration <= 27:
            return 4
        elif step_count <= 18 and duration <= 23:
            return 5
        elif 22 <= step_count <= 25 and 26 <= duration:
            return 3
    elif 3 <= age < 5:
        if step_count <= 16 and duration <= 18:
            return 5
        elif step_count == 18 and 18 < duration < 21:
            return 4
        elif 20 <= step_count <= 22 and 20 < duration < 23:
            return 3
        elif step_count == 22 and 22 < duration < 25:
            return 2
        elif step_count > 25 and duration >= 25:
            return 1
    elif 5 <= age < 7:
        if step_count <= 14 and duration <= 15:
            return 5
        elif step_count == 16 and 15 < duration < 18:
            return 4
        elif step_count == 18 and 17 < duration < 20:
            return 3
        elif 20 <= step_count <= 22 and 19 < duration < 22:
            return 2
        elif step_count > 21 and duration >= 22:
            return 1
    else:
        if step_count <= 12 and duration <= 12:
            return 5
        elif step_count == 14 and 12 < duration < 15:
            return 4
        elif 16 <= step_count <= 18 and 14 < duration < 17:
            return 3
        elif step_count == 18 and 16 < duration < 19:
            return 2
        elif step_count > 19 and duration >= 19:
            return 1

    return 2  



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
    next_level= determine_next_level(age, game_record["duration"], game_record["stepCount"])

    return jsonify({'msg': 'Record added successfully','nextLevel': next_level}), 200   

     

# Run Server
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=False)