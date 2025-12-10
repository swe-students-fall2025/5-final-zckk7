import os
import time
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "smart_apartment_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
print("Connected to MongoDB.")


def check_rules(reading):
    sensor_type = reading.get("sensor_type")
    value = reading.get("value")
    room = reading.get("room")
    if sensor_type == "smoke" and (value == 1 or value is True):
        return {
            "type": "Fire Safety",
            "severity": "high",
            "message": f"CRITICAL: Smoke detected in {room}!",
        }
    if sensor_type == "temperature" and isinstance(value, (int, float)) and value > 35:
        return {
            "type": "High Temp",
            "severity": "high",
            "message": f"Dangerous heat ({value}°C) in {room}. Potential fire risk.",
        }
    if sensor_type == "temperature" and isinstance(value, (int, float)) and value < 10:
        return {
            "type": "Low Temp",
            "severity": "medium",
            "message": f"Low temperature ({value}°C) in {room}. Check heating.",
        }
    if sensor_type == "humidity" and isinstance(value, (int, float)) and value > 70:
        return {
            "type": "Humidity",
            "severity": "low",
            "message": f"High humidity ({value}%) in {room}. Mold risk.",
        }

    return None


def run_engine():
    print("Alert Engine running...")
    initial_delay = True
    while True:
        try:
            if initial_delay:
                print("Waiting 30 seconds before first check to avoid startup burst...")
                time.sleep(30)
                initial_delay = False
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=20)
            recent_readings = list(
                db.sensor_readings.find({"timestamp": {"$gte": cutoff_time}})
            )
            
            for reading in recent_readings:
                alert_data = check_rules(reading)
                if alert_data:
                    existing_alert = db.alerts.find_one(
                        {
                            "reading_id": reading.get("_id"),
                            "type": alert_data["type"],
                        }
                    )
                    
                    if not existing_alert:
                        new_alert = {
                            "timestamp": datetime.now(timezone.utc),
                            "apartment_id": reading.get("apartment_id"),
                            "room": reading.get("room"),
                            "reading_id": reading.get("_id"),
                            "type": alert_data["type"],
                            "severity": alert_data["severity"],
                            "message": alert_data["message"],
                            "status": "new",
                        }
                        db.alerts.insert_one(new_alert)
                        print(f"Alert created: {alert_data['message']}")
            time.sleep(12)
        except Exception as e:
            print(f"Error in engine loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)


if __name__ == "__main__":
    run_engine()
