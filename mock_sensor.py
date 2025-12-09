from datetime import datetime
from pymongo import MongoClient


MONGO_URI = "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.smart_apartment_db


def trigger_fire():
    print("Simulating fire...")
    reading = {
        "timestamp": datetime.utcnow(),
        "apartment_id": "A-101",
        "room": "Kitchen",
        "sensor_type": "temperature",
        "value": 90.0,
        "unit": "C",
    }
    db.sensor_readings.insert_one(reading)
    print("Data sent to cloud.")


if __name__ == "__main__":
    trigger_fire()
