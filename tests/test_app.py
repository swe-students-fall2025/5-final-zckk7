import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, convert_objectid_to_str, allowed_file
from bson import ObjectId

class TestApp(unittest.TestCase):
    
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
    
    def test_convert_objectid_to_str_with_objectid(self):
        obj_id = ObjectId()
        result = convert_objectid_to_str(obj_id)
        self.assertEqual(result, str(obj_id))
    
    def test_convert_objectid_to_str_with_dict(self):
        obj_id = ObjectId()
        data = {"_id": obj_id, "name": "test"}
        result = convert_objectid_to_str(data)
        self.assertEqual(result["_id"], str(obj_id))
        self.assertEqual(result["name"], "test")
    
    def test_convert_objectid_to_str_with_list(self):
        obj_id = ObjectId()
        data = [{"_id": obj_id}, {"name": "test"}]
        result = convert_objectid_to_str(data)
        self.assertEqual(result[0]["_id"], str(obj_id))
        self.assertEqual(result[1]["name"], "test")
    
    def test_convert_objectid_to_str_nested(self):
        obj_id = ObjectId()
        data = {"items": [{"_id": obj_id}]}
        result = convert_objectid_to_str(data)
        self.assertEqual(result["items"][0]["_id"], str(obj_id))
    
    def test_allowed_file_valid(self):
        self.assertTrue(allowed_file("test.jpg"))
        self.assertTrue(allowed_file("test.png"))
        self.assertTrue(allowed_file("test.gif"))
    
    def test_allowed_file_invalid(self):
        self.assertFalse(allowed_file("test.txt"))
        self.assertFalse(allowed_file("test.pdf"))
    
    def test_index_redirects_when_not_logged_in(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
    
    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_signup_page_loads(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
