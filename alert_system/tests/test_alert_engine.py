import unittest
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from alert_engine import check_rules

class TestAlertEngine(unittest.TestCase):
    
    def setUp(self):
        self.base_reading = {
            "apartment_id": "A-101",
            "room": "room-1",
            "sensor_type": "temperature",
            "value": 25.0,
            "timestamp": datetime.now(timezone.utc)
        }
    
    def test_smoke_detection(self):
        reading = {**self.base_reading, "sensor_type": "smoke", "value": 1}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Fire Safety")
        self.assertEqual(result["severity"], "high")
    
    def test_no_smoke(self):
        reading = {**self.base_reading, "sensor_type": "smoke", "value": 0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_high_temperature(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 40.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "High Temp")
        self.assertEqual(result["severity"], "high")
    
    def test_normal_temperature(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 22.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_low_temperature(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 5.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Low Temp")
        self.assertEqual(result["severity"], "medium")
    
    def test_high_noise(self):
        reading = {**self.base_reading, "sensor_type": "noise", "value": 80.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_normal_noise(self):
        reading = {**self.base_reading, "sensor_type": "noise", "value": 30.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_motion_detection(self):
        reading = {**self.base_reading, "sensor_type": "motion", "value": 1}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_unknown_sensor_type(self):
        reading = {**self.base_reading, "sensor_type": "unknown"}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_smoke_detection_bool_true(self):
        reading = {**self.base_reading, "sensor_type": "smoke", "value": True}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Fire Safety")
        self.assertEqual(result["severity"], "high")
    
    def test_high_humidity(self):
        reading = {**self.base_reading, "sensor_type": "humidity", "value": 80.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Humidity")
        self.assertEqual(result["severity"], "low")
    
    def test_normal_humidity(self):
        reading = {**self.base_reading, "sensor_type": "humidity", "value": 50.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_temperature_boundary_high(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 36.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "High Temp")
    
    def test_temperature_boundary_low(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 9.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Low Temp")
    
    def test_temperature_exact_threshold_high(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 35.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_temperature_exact_threshold_low(self):
        reading = {**self.base_reading, "sensor_type": "temperature", "value": 10.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_humidity_boundary(self):
        reading = {**self.base_reading, "sensor_type": "humidity", "value": 71.0}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Humidity")
    
    def test_humidity_exact_threshold(self):
        reading = {**self.base_reading, "sensor_type": "humidity", "value": 70.0}
        result = check_rules(reading)
        self.assertIsNone(result)
    
    def test_missing_room_field(self):
        reading = {"apartment_id": "A-101", "sensor_type": "smoke", "value": 1}
        result = check_rules(reading)
        self.assertIsNotNone(result)
        self.assertEqual(result["type"], "Fire Safety")

if __name__ == '__main__':
    unittest.main()
