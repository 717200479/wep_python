import unittest
import sqlite3
from datetime import datetime, timedelta

class TestUserOperations(unittest.TestCase):
    def setUp(self):
        """تهيئة قاعدة البيانات للاختبار"""
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                email TEXT,
                credit REAL DEFAULT 0.0
            )
        ''')
        self.conn.commit()

    def tearDown(self):
        """تنظيف بعد كل اختبار"""
        self.conn.close()

    def test_user_creation(self):
        """اختبار إنشاء مستخدم جديد"""
        self.cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', ('testuser', 'password123', 'test@example.com'))
        self.conn.commit()

        self.cursor.execute('SELECT * FROM users WHERE username = ?', ('testuser',))
        user = self.cursor.fetchone()
        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'testuser')
        self.assertEqual(user[2], 'password123')
        self.assertEqual(user[3], 'test@example.com')

    def test_credit_operations(self):
        """اختبار عمليات الرصيد"""
        # إنشاء مستخدم
        self.cursor.execute('''
            INSERT INTO users (username, password, email, credit)
            VALUES (?, ?, ?, ?)
        ''', ('credituser', 'pass123', 'credit@example.com', 100.0))
        self.conn.commit()

        # اختبار إضافة رصيد
        self.cursor.execute('UPDATE users SET credit = credit + ? WHERE username = ?', 
                          (50.0, 'credituser'))
        self.conn.commit()

        self.cursor.execute('SELECT credit FROM users WHERE username = ?', ('credituser',))
        credit = self.cursor.fetchone()[0]
        self.assertEqual(credit, 150.0)

        # اختبار خصم رصيد
        self.cursor.execute('UPDATE users SET credit = credit - ? WHERE username = ?', 
                          (30.0, 'credituser'))
        self.conn.commit()

        self.cursor.execute('SELECT credit FROM users WHERE username = ?', ('credituser',))
        credit = self.cursor.fetchone()[0]
        self.assertEqual(credit, 120.0)

class TestTokenOperations(unittest.TestCase):
    def setUp(self):
        """تهيئة قاعدة البيانات للاختبار"""
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE tokens (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                token TEXT,
                device_info TEXT,
                expiry_time DATETIME,
                is_active INTEGER DEFAULT 1
            )
        ''')
        self.conn.commit()

    def tearDown(self):
        """تنظيف بعد كل اختبار"""
        self.conn.close()

    def test_token_creation(self):
        """اختبار إنشاء توكن"""
        expiry_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO tokens (user_id, token, device_info, expiry_time)
            VALUES (?, ?, ?, ?)
        ''', (1, 'test_token', 'Test Device', expiry_time))
        self.conn.commit()

        self.cursor.execute('SELECT * FROM tokens WHERE token = ?', ('test_token',))
        token = self.cursor.fetchone()
        self.assertIsNotNone(token)
        self.assertEqual(token[1], 1)
        self.assertEqual(token[2], 'test_token')
        self.assertEqual(token[3], 'Test Device')
        self.assertEqual(token[5], 1)  # is_active

if __name__ == '__main__':
    unittest.main() 