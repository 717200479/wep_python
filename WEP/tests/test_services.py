import pytest
from datetime import datetime, timedelta

class TestServices:
    def test_service_management(self, test_database):
        """اختبار إدارة الخدمات"""
        conn = test_database
        cursor = conn.cursor()
        
        # إضافة خدمة جديدة
        service_data = {
            'brand': 'TestBrand',
            'name': 'Test Service',
            'description': 'Test Description',
            'price': 99.99,
            'requirements': 'Test Requirements'
        }
        
        add_service(cursor, service_data)
        conn.commit()
        
        # التحقق من إضافة الخدمة
        cursor.execute('SELECT * FROM services WHERE brand = ? AND name = ?', 
                      ('TestBrand', 'Test Service'))
        service = cursor.fetchone()
        
        assert service is not None
        assert service[1] == 'TestBrand'
        assert service[2] == 'Test Service'
        assert float(service[4]) == 99.99
        
        # اختبار تحديث الخدمة
        update_service(cursor, service[0], {
            'price': 149.99,
            'description': 'Updated Description'
        })
        conn.commit()
        
        cursor.execute('SELECT price, description FROM services WHERE id = ?', (service[0],))
        updated_service = cursor.fetchone()
        assert float(updated_service[0]) == 149.99
        assert updated_service[1] == 'Updated Description'

    def test_imei_request(self, test_database):
        """اختبار طلبات IMEI"""
        conn = test_database
        cursor = conn.cursor()
        
        # إنشاء مستخدم للاختبار
        cursor.execute('''
            INSERT INTO users (username, password, email)
            VALUES (?, ?, ?)
        ''', ('imeiuser', 'hashedpass', 'imei@test.com'))
        user_id = cursor.lastrowid
        conn.commit()
        
        # إنشاء طلب IMEI
        request_data = {
            'user_id': user_id,
            'device': 'Test Phone',
            'imei': '123456789012345',
            'service': 'Unlock Service'
        }
        
        create_imei_request(cursor, request_data)
        conn.commit()
        
        # التحقق من إنشاء الطلب
        cursor.execute('SELECT * FROM imei_requests WHERE user_id = ?', (user_id,))
        request = cursor.fetchone()
        
        assert request is not None
        assert request[1] == user_id
        assert request[2] == 'Test Phone'
        assert request[3] == '123456789012345'
        assert request[4] == 'Unlock Service'
        assert request[5] == 'pending'

    def test_credit_operations(self, test_database):
        """اختبار عمليات الرصيد"""
        conn = test_database
        cursor = conn.cursor()
        
        # إنشاء مستخدم للاختبار
        cursor.execute('''
            INSERT INTO users (username, password, email, credit)
            VALUES (?, ?, ?, ?)
        ''', ('credituser', 'hashedpass', 'credit@test.com', 100.0))
        user_id = cursor.lastrowid
        conn.commit()
        
        # اختبار إضافة رصيد
        add_credit_to_user(user_id, 50.0)
        cursor.execute('SELECT credit FROM users WHERE id = ?', (user_id,))
        credit = cursor.fetchone()[0]
        assert credit == 150.0
        
        # اختبار خصم رصيد
        deduct_credit_from_user(user_id, 30.0)
        cursor.execute('SELECT credit FROM users WHERE id = ?', (user_id,))
        credit = cursor.fetchone()[0]
        assert credit == 120.0
        
        # اختبار خصم رصيد أكبر من المتوفر
        with pytest.raises(Exception):
            deduct_credit_from_user(user_id, 200.0) 