import os
import sys
import unittest
from flask import url_for
from flask_login import current_user

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import app
from model import init_db, User

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test"""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()
        init_db()  # Initialize test database

    def tearDown(self):
        """Clean up after each test"""
        self.app_context.pop()

    def test_home_page(self):
        """Test the home page route"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)

    def test_user_registration(self):
        """Test user registration functionality"""
        test_user = {
            'username': 'testuser',
            'password': 'Test123!',
            'email': 'test@example.com',
            'phone': '1234567890',
            'smartphone_services': 'yes'
        }
        
        # Test registration
        response = self.app.post('/register', data=test_user, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify user was created in database
        user = User.query.filter_by(username=test_user['username']).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, test_user['email'])

    def test_login_logout(self):
        """Test login and logout functionality"""
        # First register a user
        self.app.post('/register', data={
            'username': 'logintest',
            'password': 'Test123!',
            'email': 'login@test.com',
            'phone': '1234567890',
            'smartphone_services': 'yes'
        })

        # Test login
        login_response = self.app.post('/login', data={
            'username': 'logintest',
            'password': 'Test123!'
        }, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)

        # Test logout
        logout_response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(logout_response.status_code, 200)

    def test_protected_route(self):
        """Test access to protected routes"""
        # Try accessing protected route without login
        response = self.app.get('/imei_services', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())

    def test_admin_required(self):
        """Test admin-only routes"""
        # Try accessing admin route without admin privileges
        response = self.app.get('/admin', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'access denied', response.data.lower())

if __name__ == '__main__':
    unittest.main() 