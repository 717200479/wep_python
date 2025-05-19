import pytest
from flask import session
from model import User
from controller import LoginController

class TestAuthentication:
    def test_user_authentication(self, test_database):
        """اختبار المصادقة"""
        user = User()
        # اختبار تسجيل دخول صحيح
        result = user.authenticate('test_user', 'test_password')
        assert result is not None
        assert result['username'] == 'test_user'

        # اختبار تسجيل دخول خاطئ
        result = user.authenticate('wrong_user', 'wrong_password')
        assert result is None

    def test_user_registration(self, test_database):
        """اختبار تسجيل مستخدم جديد"""
        user = User()
        # اختبار إنشاء مستخدم جديد
        result = user.create_user('new_user', 'new_password')
        assert result is True

    def test_login_controller(self, client):
        """اختبار متحكم تسجيل الدخول"""
        # اختبار عرض صفحة تسجيل الدخول
        response = client.get('/login')
        assert response.status_code == 200
        
        # اختبار تسجيل دخول صحيح
        response = client.post('/login', data={
            'username': 'test_user',
            'password': 'test_password'
        })
        assert response.status_code == 302  # توجيه إلى لوحة التحكم
        assert 'user_id' in session
        
        # اختبار تسجيل دخول خاطئ
        response = client.post('/login', data={
            'username': 'wrong_user',
            'password': 'wrong_password'
        })
        assert response.status_code == 200
        assert 'error' in response.data.decode()

    def test_register_user(self, client):
        """اختبار تسجيل مستخدم جديد"""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'Test123!',
            'email': 'new@test.com',
            'phone': '1234567890',
            'smartphone_services': 'yes'
        })
        assert response.status_code == 302  # توجيه بعد التسجيل الناجح 