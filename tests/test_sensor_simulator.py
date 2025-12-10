import importlib

def test_sensor_simulator_module_imports():
    module = importlib.import_module("sensor_simulator.main")
    assert module is not None

def test_sensor_reading_structure():
    sim = importlib.import_module("sensor_simulator.main")
    reading = sim.build_fake_reading()
    assert isinstance(reading, dict)
    required_keys = {
        "sensor_type",
        "apartment_id",
        "room_id",
        "value",
        "created_at",
    }
    assert required_keys.issubset(reading.keys())
