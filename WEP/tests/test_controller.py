import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controller import app
from database_setup import init_db  # استيراد دالة init_db

# إعداد قاعدة البيانات قبل كل اختبار
@pytest.fixture(scope='module', autouse=True)
def setup_database():
    init_db()  # تهيئة قاعدة البيانات
    yield
    # يمكن إضافة كود لتنظيف قاعدة البيانات إذا لزم الأمر

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_imei_services(client):
    response = client.get('/imei_services')
    assert response.status_code == 200

def test_register_user(client):
    response = client.post('/register', data={
        'username': 'tykgl',
        'password': 'cghvjord123!',
        'email': 'jhk.j@example.com',
        'phone': '123456789',
        'smartphone_services': 'yes'
    })
    assert response.status_code == 302  # Redirect بعد التسجيل الناجح