import pytest
import sys
import os
import tempfile
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller import app
from model import init_db

@pytest.fixture
def app_context():
    """إعداد سياق التطبيق للاختبارات"""
    with app.app_context() as context:
        yield context

@pytest.fixture
def test_client():
    """إنشاء عميل اختبار للتطبيق"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_database():
    """إنشاء قاعدة بيانات مؤقتة للاختبارات"""
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path
    
    # إنشاء قاعدة البيانات وجداولها
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # إنشاء جداول الاختبار
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            credit REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT NOT NULL,
            device_info TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expiry_time TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            requirements TEXT,
            is_active INTEGER DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS imei_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            device TEXT NOT NULL,
            imei TEXT NOT NULL,
            service TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # تنظيف بعد الانتهاء
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def auth_client(test_client, test_database):
    """إنشاء عميل مصادق عليه للاختبارات"""
    # إنشاء مستخدم اختبار
    conn = sqlite3.connect(test_database)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password, email, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('testuser', 'hashedpass', 'test@example.com', 0))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    with test_client.session_transaction() as session:
        session['user_id'] = user_id
        session['is_authenticated'] = True
    
    return test_client

@pytest.fixture
def admin_client(test_client, test_database):
    """إنشاء عميل مشرف للاختبارات"""
    # إنشاء مستخدم مشرف
    conn = sqlite3.connect(test_database)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password, email, is_admin)
        VALUES (?, ?, ?, ?)
    ''', ('adminuser', 'hashedpass', 'admin@test.com', 1))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    with test_client.session_transaction() as session:
        session['user_id'] = user_id
        session['is_authenticated'] = True
        session['is_admin'] = True
    
    return test_client 