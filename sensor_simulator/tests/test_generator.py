from datetime import datetime as real_datetime, timezone

import sensor_simulator.generator as gen


def test_generate_batch_count_and_fields(monkeypatch):
    fixed_now = real_datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(gen, "datetime", FakeDatetime)

    apartments = 2
    rooms_per_apartment = 3
    seed = 42

    batch = gen.generate_batch(apartments=apartments, rooms_per_apartment=rooms_per_apartment, seed=seed)

    assert len(batch) == apartments * rooms_per_apartment * len(gen.SENSORS)

    for doc in batch:
        for k in ["timestamp", "apartment_id", "room", "sensor_type", "value", "unit"]:
            assert k in doc

        assert doc["timestamp"] == fixed_now
        assert doc["timestamp"].tzinfo == timezone.utc

        assert doc["apartment_id"].startswith("A-")
        assert doc["room"].startswith("room-")

        assert doc["sensor_type"] in gen.SENSORS

        if doc["sensor_type"] == "temperature":
            assert doc["unit"] == "C"
            assert isinstance(doc["value"], (int, float))

        elif doc["sensor_type"] == "noise":
            assert doc["unit"] == "dB"
            assert isinstance(doc["value"], (int, float))
            assert doc["value"] >= 0.0

        elif doc["sensor_type"] in ("smoke", "motion"):
            assert doc["unit"] == "bool"
            assert doc["value"] in (0, 1)


def test_generate_batch_deterministic_with_fixed_time(monkeypatch):
    fixed_now = real_datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(gen, "datetime", FakeDatetime)

    b1 = gen.generate_batch(apartments=2, rooms_per_apartment=2, seed=123)
    b2 = gen.generate_batch(apartments=2, rooms_per_apartment=2, seed=123)

    assert b1 == b2
