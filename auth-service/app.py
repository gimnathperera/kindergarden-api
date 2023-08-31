import hashlib
import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId 

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'UGUsVuDMPEzDLIQv'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

client = MongoClient("mongodb+srv://root:UGUsVuDMPEzDLIQv@cluster0.gvvm6fh.mongodb.net/") # your connection string
db = client["kindergarden"]
users_collection = db["users"]
letter_collection = db["letters"]
audio_collection = db["audio"]
emotion_collection = db["emotion"]
game_collection = db["game"]


@app.route("/api/v1/users", methods=["POST"])
def register():
    new_user = request.get_json()  # Store the JSON body request
    new_user["type"] = new_user["type"]
    new_user["email"] = new_user["email"].lower()
    new_user["level"] = 0

    if "parentEmail" in new_user:
        new_user["parentEmail"] = new_user["parentEmail"]

    if "dob" in new_user:
        new_user["dob"] = new_user["dob"]

    new_user["password"] = hashlib.sha256(new_user["password"].encode("utf-8")).hexdigest()  # Encrypt password
    doc = users_collection.find_one({"username": new_user["username"]})  # Check if user exists
    
    if not doc:
        users_collection.insert_one(new_user)
        return jsonify({'msg': 'User created successfully'}), 201
    else:
        return jsonify({'msg': 'Username already exists'}), 409


@app.route("/api/v1/login", methods=["POST"])
def login():
	login_details = request.get_json() # store the json body request
	user_from_db = users_collection.find_one({'username': login_details['username']})  # search for user in database

	if user_from_db:
		encrpted_password = hashlib.sha256(login_details['password'].encode("utf-8")).hexdigest()
		if encrpted_password == user_from_db['password']:
			user_data = {
                'username': user_from_db['username'],
                'type': user_from_db['type'],
                'level': user_from_db['level'],
            }
			access_token = create_access_token(identity=user_data) # create jwt token
			return jsonify(access_token=access_token,), 200

	return jsonify({'msg': 'The username or password is incorrect'}), 401


@app.route("/api/v1/user", methods=["GET"])
@jwt_required
def profile():
	current_user = get_jwt_identity() # Get the identity of the current user
	user_from_db = users_collection.find_one({'username' : current_user})
	if user_from_db:
		del user_from_db['_id'], user_from_db['password'] # delete data we don't want to return
		return jsonify({'profile' : user_from_db }), 200
	else:
		return jsonify({'msg': 'Profile not found'}), 404
	

@app.route("/api/v1/letter-records", methods=["POST"])
def add_letter_record():
    letter_record = request.get_json()  
    letter_record["username"] = letter_record["username"]
    letter_record["marks"] = letter_record["marks"]
    letter_record["created_at"] = datetime.datetime.now()

    
    letter_collection.insert_one(letter_record)
    return jsonify({'msg': 'Record added successfully'}), 201


@app.route("/api/v1/audio-records", methods=["POST"])
def add_audio_record():
    audio_record = request.get_json()  
    audio_record["username"] = audio_record["username"]
    audio_record["marks"] = audio_record["marks"]
    audio_record["created_at"] = datetime.datetime.now()

    
    audio_collection.insert_one(audio_record)
    return jsonify({'msg': 'Record added successfully'}), 201    


@app.route("/api/v1/emotion-records", methods=["POST"])
def add_emotion_record():
    emotion_record = request.get_json()  
    emotion_record["username"] = emotion_record["username"]
    emotion_record["emotion"] = emotion_record["emotion"]
    emotion_record["created_at"] = datetime.datetime.now()

    
    emotion_collection.insert_one(emotion_record)
    return jsonify({'msg': 'Record added successfully'}), 201 


@app.route("/api/v1/game-records", methods=["POST"])
def add_game_record():
    game_record = request.get_json()  
    game_record["username"] = game_record["username"]
    game_record["level"] = game_record["level"]
    game_record["duration"] = game_record["duration"]
    game_record["stepCount"] = game_record["stepCount"]
    game_record["created_at"] = datetime.datetime.now()

    
    game_collection.insert_one(game_record)
    return jsonify({'msg': 'Record added successfully'}), 201    


@app.route("/api/v1/get-records", methods=["POST"])
def get_all_records():
    username = request.json.get("username")

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    records = {
        "letters": [],
        "audio": [],
        "emotion": [],
        "game": [],
    }

    # Fetch records from each collection based on the username
    letter_records = letter_collection.find({"username": username})
    for record in letter_records:
        # Convert ObjectId to string for serialization
        record['_id'] = str(record['_id'])
        records["letters"].append(record)

    audio_records = audio_collection.find({"username": username})
    for record in audio_records:
        record['_id'] = str(record['_id'])
        records["audio"].append(record)

    emotion_records = emotion_collection.find({"username": username})
    for record in emotion_records:
        record['_id'] = str(record['_id'])
        records["emotion"].append(record)

    game_records = game_collection.find({"username": username})
    for record in game_records:
        record['_id'] = str(record['_id'])
        records["game"].append(record)

    return jsonify(records), 200


@app.route("/api/v1/children/<parent_username>", methods=["GET"])
def get_children(parent_username):
    # Query the users collection to find all CHILD type users for the given parent username
    children = users_collection.find({"parentEmail": parent_username, "type": "CHILD"})

    # Create a list to store the child users
    child_users = []

    # Iterate through the query result and append child users to the list
    for child in children:
        # Remove sensitive information like '_id' and 'password' if necessary
        if '_id' in child:
            del child['_id']
        if 'password' in child:
            del child['password']
        child_users.append(child)

    # Return the list of child users as a JSON response
    return jsonify(child_users), 200





if __name__ == '__main__':
	app.run(debug=True)
