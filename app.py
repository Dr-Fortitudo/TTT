from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask App
app = Flask(__name__)

# Load Firebase Credentials
cred = credentials.Certificate("timetable-b3371-firebase-adminsdk-fbsvc-d13120ed4b.json") 
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route("/")
def home():
    return jsonify({"message": "Flask API is running!"})

if __name__ == "__main__":
    app.run(debug=True)
