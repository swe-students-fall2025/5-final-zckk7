"""Mock Sensor Data Sender."""

from datetime import datetime, timezone

from sensor_simulator.config import load_config
from sensor_simulator.writer import get_db, write_readings


def trigger_fire():
    cfg = load_config()
    db = get_db(cfg.mongodb_uri, cfg.mongodb_db)

    reading = {
        "timestamp": datetime.now(timezone.utc),
        "apartment_id": "A-101",
        "room": "Kitchen",
        "sensor_type": "temperature",
        "value": 90.0,
        "unit": "C",
        "source": "manual_fire_test",
    }

    write_readings(db, [reading])
    print("Fire test reading inserted into sensor_readings")


if __name__ == "__main__":
    trigger_fire()