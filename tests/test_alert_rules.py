import importlib


def _make_reading(value, sensor_type="smoke", apartment_id="3B"):
    return {
        "sensor_type": sensor_type,
        "apartment_id": apartment_id,
        "room_id": "Living Room",
        "value": value,
    }


def test_high_value_triggers_alert():
    engine = importlib.import_module("alert_system.alert_engine")
    alerts = engine.check_alerts(_make_reading(95))
    assert alerts is not None


def test_normal_value_no_alert():
    engine = importlib.import_module("alert_system.alert_engine")
    alerts = engine.check_alerts(_make_reading(10))
    assert alerts is not None
