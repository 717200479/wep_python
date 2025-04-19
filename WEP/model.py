# model.py
import sqlite3
import hashlib
import logging
from functools import wraps

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
    
    # Insert test data
    test_data = [
        ('testuser', hash_password('testpass'), 'test@example.com', '1234567890', 100.0, 0),
        ('adminuser', hash_password('adminpass'), 'admin@example.com', '0987654321', 500.0, 1)
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
    
    # Insert test services
    test_services = [
        ('Samsung', 'Unlock', 29.99, 'Device unlocking service', 'IMEI required'),
        ('Apple', 'iCloud Removal', 49.99, 'iCloud activation lock removal', 'Proof of ownership required')
    ]
    
    for service in test_services:
        try:
            cursor.execute('''
                INSERT INTO services 
                (brand, name, price, description, requirements)
                VALUES (?, ?, ?, ?, ?)
            ''', service)
        except sqlite3.IntegrityError:
            pass

def hash_password(password):
    """
    Hash password using SHA-256
    
    >>> hash_password('test')
    '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
    """
    return hashlib.sha256(password.encode()).hexdigest()

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