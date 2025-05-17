import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import app
from model import init_db  # استيراد دالة init_db

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        init_db()  # تهيئة قاعدة البيانات قبل كل اختبار

    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_imei_services_get(self):
        response = self.app.get('/imei_services')
        self.assertEqual(response.status_code, 200)

    def test_register_user(self):
        response = self.app.post('/register', data={
            'username': 'tuser',
            'password': 'word176823!',
            'email': 'fgjhk@example.com',
            'phone': '5678956789',
        })
        
        print(response.data)  # طباعة بيانات الاستجابة لفهم الخطأ
        print(response.status_code)  # طباعة رمز الحالة للاستجابة

        # تأكد من أن النموذج يعيد 400 فقط إذا كان هناك خطأ
        self.assertEqual(response.status_code, 302)  # Redirect بعد التسجيل الناجح

if __name__ == '__main__':
    unittest.main()