import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, convert_objectid_to_str, allowed_file
from bson import ObjectId

def create_mock_cursor(data=None):
    if data is None:
        data = []
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.limit.return_value = data
    mock_cursor.__iter__ = lambda self: iter(data)
    return mock_cursor

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
    
    def test_convert_objectid_to_str_regular_string(self):
        result = convert_objectid_to_str("not_an_objectid")
        self.assertEqual(result, "not_an_objectid")
    
    def test_allowed_file_valid(self):
        self.assertTrue(allowed_file("test.jpg"))
        self.assertTrue(allowed_file("test.png"))
        self.assertTrue(allowed_file("test.gif"))
        self.assertTrue(allowed_file("test.JPG"))
        self.assertTrue(allowed_file("test.PNG"))
    
    def test_allowed_file_invalid(self):
        self.assertFalse(allowed_file("test.txt"))
        self.assertFalse(allowed_file("test.pdf"))
        self.assertFalse(allowed_file("test"))
        self.assertFalse(allowed_file(""))
    
    def test_index_redirects_when_not_logged_in(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
    
    def test_login_page_loads(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_signup_page_loads(self):
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_login_post_success(self, mock_db):
        mock_user = {
            "_id": ObjectId(),
            "username": "testuser",
            "password": "$2b$12$test_hash",
            "role": "resident",
            "apartment_number": "A-101"
        }
        mock_db.users.find_one.return_value = mock_user
        
        with patch('app.check_password_hash', return_value=True):
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'password123'
            }, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_login_post_invalid_credentials(self, mock_db):
        mock_db.users.find_one.return_value = None
        
        response = self.client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrong'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid', response.data)
    
    @patch('app.db')
    def test_signup_post_success(self, mock_db):
        mock_db.users.find_one.return_value = None
        mock_db.users.insert_one.return_value = MagicMock()
        
        with patch('app.generate_password_hash', return_value='hashed_password'):
            response = self.client.post('/signup', data={
                'first_name': 'John',
                'last_name': 'Doe',
                'username': 'newuser',
                'password': 'password123',
                'apartment_number': 'A-102',
                'role': 'resident'
            }, follow_redirects=False)
            self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_signup_post_existing_user(self, mock_db):
        mock_db.users.find_one.return_value = {"username": "existing"}
        
        response = self.client.post('/signup', data={
            'username': 'existing',
            'password': 'password123',
            'apartment_number': 'A-101'
        })
        self.assertEqual(response.status_code, 200)
    
    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
        
        response = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    def test_packages_requires_login(self):
        response = self.client.get('/packages', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    def test_community_requires_login(self):
        response = self.client.get('/community', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    def test_admin_dashboard_requires_admin(self):
        response = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_admin_overview_api_requires_auth(self, mock_db):
        response = self.client.get('/api/admin/overview')
        self.assertEqual(response.status_code, 401)
    
    @patch('app.db')
    def test_admin_alerts_api_requires_auth(self, mock_db):
        response = self.client.get('/api/admin/alerts')
        self.assertEqual(response.status_code, 401)
    
    @patch('app.db')
    def test_admin_rooms_api_requires_auth(self, mock_db):
        response = self.client.get('/api/admin/rooms')
        self.assertEqual(response.status_code, 401)
    
    @patch('app.db')
    def test_api_latest_sensor_readings(self, mock_db):
        mock_reading = {
            "_id": ObjectId(),
            "apartment_id": "A-101",
            "sensor_type": "temperature",
            "value": 22.5,
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_db.sensor_readings.find_one.return_value = mock_reading
        
        response = self.client.get('/api/sensor_readings/latest?apartment_id=A-101&sensor_type=temperature')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_api_latest_sensor_readings_no_db(self, mock_db):
        with patch('app.db', None):
            response = self.client.get('/api/sensor_readings/latest?apartment_id=A-101')
            self.assertEqual(response.status_code, 500)
    
    def test_signup_apartment_number_formatting(self):
        with patch('app.db') as mock_db:
            mock_db.users.find_one.return_value = None
            mock_db.users.insert_one.return_value = MagicMock()
            
            with patch('app.generate_password_hash', return_value='hashed'):
                response = self.client.post('/signup', data={
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'username': 'user1',
                    'password': 'pass123',
                    'apartment_number': '102',
                    'role': 'resident'
                }, follow_redirects=False)
                self.assertEqual(response.status_code, 302)
                call_args = mock_db.users.insert_one.call_args[0][0]
                self.assertEqual(call_args['apartment_number'], 'A-102')
    
    @patch('app.db')
    def test_dashboard_with_session(self, mock_db):
        mock_db.users.find_one.return_value = {
            "first_name": "Test",
            "apartment_number": "A-101"
        }
        mock_db.alerts.find.return_value = []
        mock_db.sensor_readings.find.return_value = create_mock_cursor([])
        mock_db.maintenance_requests.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
            sess['apartment_number'] = 'A-101'
        
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_packages_with_session(self, mock_db):
        mock_db.packages.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/packages')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_community_with_session(self, mock_db):
        mock_db.community_posts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/community')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_create_post_get(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/community/create')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_maintenance_get(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/maintenance/new')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_packages_get(self, mock_db):
        mock_db.packages.find.return_value = []
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/packages')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_maintenance_get(self, mock_db):
        mock_db.maintenance_requests.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/maintenance')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_overview_with_auth(self, mock_db):
        mock_db.alerts.find.return_value = create_mock_cursor([])
        mock_db.maintenance_requests.find.return_value = create_mock_cursor([])
        mock_db.packages.find.return_value = []
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/overview')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_overview_no_db(self, mock_db):
        with patch('app.db', None):
            with self.client.session_transaction() as sess:
                sess['username'] = 'admin'
                sess['role'] = 'admin'
            
            response = self.client.get('/api/admin/overview')
            self.assertEqual(response.status_code, 500)
    
    @patch('app.db')
    def test_admin_alerts_with_auth(self, mock_db):
        mock_db.alerts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/alerts')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_update_alert_status_patch(self, mock_db):
        alert_id = str(ObjectId())
        mock_db.alerts.update_one.return_value = MagicMock(matched_count=1)
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(
            f'/api/admin/alerts/{alert_id}',
            json={'status': 'resolved'}
        )
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_update_alert_status_invalid(self, mock_db):
        alert_id = str(ObjectId())
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(
            f'/api/admin/alerts/{alert_id}',
            json={'status': 'invalid_status'}
        )
        self.assertEqual(response.status_code, 400)
    
    @patch('app.db')
    def test_admin_rooms_with_auth(self, mock_db):
        mock_db.rooms.find.return_value = []
        mock_db.sensor_readings.aggregate.return_value = []
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/rooms')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_room_history_with_auth(self, mock_db):
        mock_db.sensor_readings.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/rooms/A-101_room-1/history')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_index_with_admin_session(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_index_with_resident_session(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'resident'
            sess['role'] = 'resident'
        
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    def test_convert_objectid_to_str_with_none(self):
        result = convert_objectid_to_str(None)
        self.assertIsNone(result)
    
    def test_convert_objectid_to_str_with_number(self):
        result = convert_objectid_to_str(123)
        self.assertEqual(result, 123)
    
    @patch('app.db')
    def test_create_post_post_success(self, mock_db):
        mock_db.community_posts.insert_one.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
            sess['apartment_number'] = 'A-101'
        
        response = self.client.post('/community/create', data={
            'title': 'Test Post',
            'category': 'Food',
            'description': 'Test description'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_create_post_missing_fields(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.post('/community/create', data={
            'title': '',
            'category': 'Food',
            'description': 'Test'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'required', response.data)
    
    @patch('app.db')
    def test_maintenance_post_success(self, mock_db):
        mock_db.users.find_one.return_value = None
        mock_db.maintenance_requests.insert_one.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
            sess['apartment_number'] = 'A-101'
            sess['first_name'] = 'Test'
            sess['last_name'] = 'User'
        
        response = self.client.post('/maintenance/new', data={
            'category': 'Plumbing',
            'description': 'Leaky faucet',
            'urgency': 'medium'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_maintenance_post_missing_fields(self, mock_db):
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.post('/maintenance/new', data={
            'issue_type': '',
            'description': 'Test'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_post_detail_with_session(self, mock_db):
        post_id = str(ObjectId())
        mock_db.community_posts.find_one.return_value = {
            "_id": ObjectId(post_id),
            "title": "Test Post",
            "description": "Test",
            "author": "testuser",
            "created_at": datetime.now()
        }
        mock_db.comments.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get(f'/community/post/{post_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_add_comment_post(self, mock_db):
        post_id = str(ObjectId())
        mock_db.community_posts.find_one.return_value = {"_id": ObjectId(post_id)}
        mock_db.comments.insert_one.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.post(f'/community/post/{post_id}/comment', data={
            'comment': 'Test comment'
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_delete_post_success(self, mock_db):
        post_id = str(ObjectId())
        mock_db.community_posts.find_one.return_value = {
            "_id": ObjectId(post_id),
            "author": "testuser"
        }
        mock_db.community_posts.delete_one.return_value = MagicMock()
        mock_db.comments.delete_many.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.post(f'/community/post/{post_id}/delete', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
    
    @patch('app.db')
    def test_admin_packages_post(self, mock_db):
        mock_user = {
            "_id": ObjectId(),
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "apartment_number": "A-101"
        }
        mock_db.users.find_one.return_value = mock_user
        mock_db.packages.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.post('/api/admin/packages', json={
            'resident_id': 'johndoe',
            'carrier': 'UPS',
            'location': 'Lobby'
        })
        self.assertEqual(response.status_code, 201)
    
    @patch('app.db')
    def test_update_package_status_patch(self, mock_db):
        package_id = str(ObjectId())
        mock_db.packages.update_one.return_value = MagicMock(matched_count=1)
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(f'/api/admin/packages/{package_id}', json={
            'status': 'picked_up'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_update_package_status_delete(self, mock_db):
        package_id = str(ObjectId())
        mock_db.packages.delete_one.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.delete(f'/api/admin/packages/{package_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_update_maintenance_status_patch(self, mock_db):
        request_id = str(ObjectId())
        mock_db.maintenance_requests.update_one.return_value = MagicMock(matched_count=1)
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(f'/api/admin/maintenance/{request_id}', json={
            'status': 'resolved'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_community_posts_get(self, mock_db):
        mock_db.community_posts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/community/posts')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_community_post_patch(self, mock_db):
        post_id = str(ObjectId())
        mock_db.community_posts.update_one.return_value = MagicMock(matched_count=1)
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(f'/api/admin/community/posts/{post_id}', json={
            'status': 'closed'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_community_post_delete(self, mock_db):
        post_id = str(ObjectId())
        mock_db.community_posts.find_one.return_value = {"_id": ObjectId(post_id)}
        mock_db.community_posts.delete_one.return_value = MagicMock()
        mock_db.comments.delete_many.return_value = MagicMock()
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.delete(f'/api/admin/community/posts/{post_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_api_latest_sensor_readings_with_params(self, mock_db):
        mock_reading = {
            "_id": ObjectId(),
            "apartment_id": "A-101",
            "sensor_type": "temperature",
            "value": 22.5,
            "timestamp": datetime.now()
        }
        mock_db.sensor_readings.find_one.return_value = mock_reading
        
        response = self.client.get('/api/sensor_readings/latest?apartment_id=A-101&sensor_type=temperature')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_rooms_with_data(self, mock_db):
        mock_db.rooms.find.return_value = [{
            "_id": ObjectId(),
            "apartment_id": "A-101",
            "room_name": "room-1"
        }]
        mock_db.sensor_readings.find_one.return_value = None
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/rooms')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_rooms_no_rooms_with_sensor_readings(self, mock_db):
        mock_db.rooms.find.return_value = []
        mock_db.sensor_readings.count_documents.return_value = 10
        mock_db.sensor_readings.aggregate.return_value = [{
            "_id": {"apartment_id": "A-101", "room": "room-1"}
        }]
        mock_db.sensor_readings.find_one.return_value = None
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/rooms')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_login_post_wrong_password(self, mock_db):
        mock_user = {
            "_id": ObjectId(),
            "username": "testuser",
            "password": "$2b$12$test_hash",
            "role": "resident",
            "apartment_number": "A-101"
        }
        mock_db.users.find_one.return_value = mock_user
        
        with patch('app.check_password_hash', return_value=False):
            response = self.client.post('/login', data={
                'username': 'testuser',
                'password': 'wrongpassword'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Invalid', response.data)
    
    @patch('app.db')
    def test_signup_validation_errors(self, mock_db):
        mock_db.users.find_one.return_value = None
        
        response = self.client.post('/signup', data={
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'ab',
            'password': '123',
            'apartment_number': 'A-102',
            'role': 'resident'
        })
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_alerts_with_severity_filter(self, mock_db):
        mock_db.alerts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/alerts?severity=high')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_admin_alerts_with_status_filter(self, mock_db):
        mock_db.alerts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.get('/api/admin/alerts?status=new')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_community_with_category_filter(self, mock_db):
        mock_db.community_posts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/community?category=food')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_community_with_search(self, mock_db):
        mock_db.community_posts.find.return_value = create_mock_cursor([])
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'testuser'
            sess['role'] = 'resident'
        
        response = self.client.get('/community?search=test')
        self.assertEqual(response.status_code, 200)
    
    @patch('app.db')
    def test_update_alert_status_not_found(self, mock_db):
        alert_id = str(ObjectId())
        mock_db.alerts.update_one.return_value = MagicMock(matched_count=0)
        
        with self.client.session_transaction() as sess:
            sess['username'] = 'admin'
            sess['role'] = 'admin'
        
        response = self.client.patch(f'/api/admin/alerts/{alert_id}', json={
            'status': 'resolved'
        })
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
