# model.py
import sqlite3
import hashlib
import logging
from functools import wraps
import bcrypt

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection decorator
def db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        db_path = kwargs.pop('db_path', 'users.db')
        conn = sqlite3.connect(db_path)
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()
    return wrapper

@db_connection
def init_db(conn, db_path='users.db'):
    """
    Initialize database tables and add test data
    
    >>> init_db(db_path=':memory:')
    """
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL UNIQUE,
            credit REAL DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
    # Create tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            expiry_time DATETIME NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            device_info TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create specialized services table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS specialized_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (category IN ('remote', 'imei', 'tools'))
        )
    ''')
    
    # Create services table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT NOT NULL,
            requirements TEXT
        )
    ''')
    
    # Create imei requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imei_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            device TEXT NOT NULL,
            imei TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at DATETIME NOT NULL,
            updated_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (service_id) REFERENCES specialized_services (id)
        )
    ''')
    
    # Insert test data
    test_data = [
        ('testuser', bcrypt.hashpw('testpass'.encode('utf-8'), bcrypt.gensalt()), 'test@example.com', '1234567890', 100.0, 0),
        ('adminuser', bcrypt.hashpw('adminpass'.encode('utf-8'), bcrypt.gensalt()), 'admin@example.com', '0987654321', 500.0, 1)
    ]
    
    for user in test_data:
        try:
            cursor.execute('''
                INSERT INTO users 
                (username, password, email, phone, credit, is_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', user)
        except sqlite3.IntegrityError:
            pass
    

    
   
    


def hash_password(password):
    """
    Hash password using bcrypt
    
    >>> hash_password('test')
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """
    التحقق من كلمة المرور باستخدام bcrypt
    
    >>> verify_password('test', hashed_password)
    """
    try:
        # تحويل كلمة المرور المدخلة إلى bytes
        password_bytes = password.encode('utf-8')
        # التحقق من كلمة المرور
        return bcrypt.checkpw(password_bytes, hashed)
    except Exception as e:
        logger.error(f"خطأ في التحقق من كلمة المرور: {str(e)}")
        return False

@db_connection
def get_user_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

@db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()

@db_connection
def get_all_users(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, phone, credit, is_admin FROM users')
    return cursor.fetchall()

@db_connection
def add_user(conn, username, password, email, phone, is_admin=False):
    """
    Add new user to database
    
    >>> add_user('newuser', 'Password123!', 'new@example.com', '1122334455', db_path=':memory:')
    """
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users 
            (username, password, email, phone, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password, email, phone, is_admin))
    except sqlite3.IntegrityError as e:
        logger.error(f"User registration failed: {str(e)}")
        raise

@db_connection
def update_user_credit(conn, user_id, credit):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET credit = credit + ? 
        WHERE id = ?
    ''', (credit, user_id))

@db_connection
def get_services_by_brand(conn, brand):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, description, price, requirements 
        FROM services 
        WHERE brand = ?
    ''', (brand,))
    return cursor.fetchall()

@db_connection
def add_service(conn, brand, name, price, description, requirements=None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO services 
        (brand, name, price, description, requirements)
        VALUES (?, ?, ?, ?, ?)
    ''', (brand, name, price, description, requirements))

@db_connection
def delete_service(conn, service_id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM services WHERE id = ?', (service_id,))

@db_connection
def update_service(conn, service_id, brand, name, price, description, requirements):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE services 
        SET brand = ?, name = ?, price = ?, description = ?, requirements = ?
        WHERE id = ?
    ''', (brand, name, price, description, requirements, service_id))

@db_connection
def get_all_services(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM services')
    return cursor.fetchall()

@db_connection
def get_specialized_services(conn, category=None):
    """
    جلب الخدمات المخصصة حسب الفئة
    """
    cursor = conn.cursor()
    if category:
        cursor.execute('''
            SELECT * FROM specialized_services 
            WHERE category = ? AND is_active = 1
            ORDER BY created_at DESC
        ''', (category,))
    else:
        cursor.execute('''
            SELECT * FROM specialized_services 
            WHERE is_active = 1
            ORDER BY category, created_at DESC
        ''')
    return cursor.fetchall()

@db_connection
def add_specialized_service(conn, category, name, price, description, requirements):
    """
    إضافة خدمة مخصصة جديدة
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO specialized_services 
        (category, name, price, description, requirements)
        VALUES (?, ?, ?, ?, ?)
    ''', (category, name, price, description, requirements))

@db_connection
def update_specialized_service(conn, service_id, category, name, price, description, requirements):
    """
    تحديث خدمة مخصصة
    """
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE specialized_services 
        SET category = ?, name = ?, price = ?, description = ?, requirements = ?
        WHERE id = ?
    ''', (category, name, price, description, requirements, service_id))

@db_connection
def delete_specialized_service(conn, service_id):
    """
    حذف خدمة مخصصة (تعطيلها)
    """
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE specialized_services 
        SET is_active = 0
        WHERE id = ?
    ''', (service_id,))

# Test data helpers
@db_connection
def add_test_user(conn):
    """Add test user for unit testing"""
    try:
        add_user(
            username='testuser',
            password=hash_password('testpass'),
            email='test@example.com',
            phone='1234567890',
            db_path=':memory:'
        )
    except sqlite3.IntegrityError:
        pass

@db_connection
def add_test_service(conn):
    """Add test service for unit testing"""
    try:
        add_service(
            brand='Samsung',
            name='Test Service',
            price=9.99,
            description='Test description',
            requirements='None',
            db_path=':memory:'
        )
    except sqlite3.IntegrityError:
        pass

if __name__ == '__main__':
    # Initialize database when running directly
    init_db()
    print("Database initialized successfully!")