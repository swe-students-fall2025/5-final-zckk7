from typing import Dict, List
from pymongo import MongoClient

def get_db(mongodb_uri: str, db_name: str):
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    return client[db_name]


def ensure_indexes(db):
    db.sensor_readings.create_index(
        [("apartment_id", 1), ("room", 1), ("sensor_type", 1), ("timestamp", -1)]
    )
    db.sensor_readings.create_index([("timestamp", -1)])


def write_readings(db, readings: List[Dict]) -> int:
    if not readings:
        return 0
    res = db.sensor_readings.insert_many(readings, ordered=False)
    return len(res.inserted_ids)