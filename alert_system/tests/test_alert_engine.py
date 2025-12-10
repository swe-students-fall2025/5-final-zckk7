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

if __name__ == '__main__':
    unittest.main()
