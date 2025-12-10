from datetime import datetime, timezone
import mongomock
import sensor_simulator.writer as writer


def test_write_readings_inserts_and_returns_count():
    client = mongomock.MongoClient()
    db = client["smart_apartment"]

    readings = [
        {
            "timestamp": datetime.now(timezone.utc),
            "apartment_id": "A-101",
            "room": "room-1",
            "sensor_type": "temperature",
            "value": 22.5,
            "unit": "C",
        },
        {
            "timestamp": datetime.now(timezone.utc),
            "apartment_id": "A-101",
            "room": "room-1",
            "sensor_type": "noise",
            "value": 40.0,
            "unit": "dB",
        },
    ]

    inserted = writer.write_readings(db, readings)
    assert inserted == 2
    assert db.sensor_readings.count_documents({}) == 2


def test_write_readings_empty_returns_zero():
    client = mongomock.MongoClient()
    db = client["smart_apartment"]

    inserted = writer.write_readings(db, [])
    assert inserted == 0
    assert db.sensor_readings.count_documents({}) == 0


def test_ensure_indexes_uses_schema_fields():
    client = mongomock.MongoClient()
    db = client["smart_apartment"]

    writer.ensure_indexes(db)

    info = db.sensor_readings.index_information()

    wanted = [("apartment_id", 1), ("room", 1), ("sensor_type", 1), ("timestamp", -1)]

    assert any(idx.get("key") == wanted for idx in info.values()), (
        f"Expected compound index {wanted}, but got: {info}"
    )


def test_get_db_uses_mongoclient(monkeypatch):
    mock_client = mongomock.MongoClient()

    def fake_mongo_client(uri, serverSelectionTimeoutMS=None):
        assert uri == "mongodb://example"
        assert serverSelectionTimeoutMS == 5000
        return mock_client

    monkeypatch.setattr(writer, "MongoClient", fake_mongo_client)

    db = writer.get_db("mongodb://example", "smart_apartment")
    assert db.name == "smart_apartment"