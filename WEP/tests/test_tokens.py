import pytest
from datetime import datetime, timedelta

class TestTokens:
    def test_token_management(self, test_database):
        """اختبار إدارة التوكنات"""
        conn = test_database
        cursor = conn.cursor()
        
        # إنشاء مستخدم للاختبار
        cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', ('tokenuser', 'hashedpass', 'token@test.com'))
        user_id = cursor.lastrowid
        conn.commit()
        
        # إنشاء توكن جديد
        token_data = {
            'user_id': user_id,
            'token': 'test_token',
            'device_info': 'Test Device',
            'expiry_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        create_token(cursor, token_data)
        conn.commit()
        
        # التحقق من إنشاء التوكن
        cursor.execute('SELECT * FROM tokens WHERE user_id = ?', (user_id,))
        token = cursor.fetchone()
        
        assert token is not None
        assert token[1] == user_id
        assert token[2] == 'test_token'
        assert token[3] == 'Test Device'
        
        # اختبار تعطيل التوكن
        deactivate_token(cursor, token[0])
        conn.commit()
        
        cursor.execute('SELECT is_active FROM tokens WHERE id = ?', (token[0],))
        is_active = cursor.fetchone()[0]
        assert is_active == 0

    def test_token_expiry(self, test_database):
        """اختبار انتهاء صلاحية التوكن"""
        conn = test_database
        cursor = conn.cursor()
        
        # إنشاء مستخدم للاختبار
        cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', ('expiryuser', 'hashedpass', 'expiry@test.com'))
        user_id = cursor.lastrowid
        conn.commit()
        
        # إنشاء توكن منتهي الصلاحية
        expired_time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        token_data = {
            'user_id': user_id,
            'token': 'expired_token',
            'device_info': 'Test Device',
            'expiry_time': expired_time
        }
        
        create_token(cursor, token_data)
        conn.commit()
        
        # التحقق من حالة التوكن
        cursor.execute('SELECT is_active FROM tokens WHERE token = ?', ('expired_token',))
        is_active = cursor.fetchone()[0]
        assert is_active == 0  # يجب أن يكون معطلاً 