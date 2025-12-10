import random
import time
from datetime import datetime, timezone
from typing import Dict, List

SENSORS = ("temperature", "smoke", "noise", "motion")

def _gen_value(sensor: str, rng: random.Random) -> Dict:
    if sensor == "temperature":
        v = rng.normalvariate(22.5, 2.5)
        return {"value": round(v, 2), "unit": "C"}
    if sensor == "smoke":
        abnormal = 1 if rng.random() < 0.001 else 0
        return {"value": abnormal, "unit": "bool"}
    if sensor == "noise":
        v = max(0.0, rng.normalvariate(40.0, 10.0))
        return {"value": round(v, 1), "unit": "dB"}
    if sensor == "motion":
        return {"value": 1 if rng.random() < 0.15 else 0, "unit": "bool"}
    raise ValueError(f"unknown sensor: {sensor}")

def generate_batch(apartments: int, rooms_per_apartment: int, seed: int) -> List[Dict]:
    rng = random.Random(seed)
    base_time = datetime.now(timezone.utc)

    batch: List[Dict] = []
    for a in range(1, apartments + 1):
        apt_id = f"A-{100 + a}"
        for r in range(1, rooms_per_apartment + 1):
            room = f"room-{r}"
            now = datetime.now(timezone.utc)
            for sensor in SENSORS:
                payload = _gen_value(sensor, rng)
                doc = {
                    "timestamp": now,
                    "apartment_id": apt_id,
                    "room": room,
                    "sensor_type": sensor,
                    "value": payload["value"],
                    "unit": payload["unit"],
                }
                batch.append(doc)
    return batch