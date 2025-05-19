

def add_credit_to_user(user_id, amount):
    """
    إضافة رصيد للمستخدم
    
    >>> add_credit_to_user(1, 50.0)
    True
    >>> add_credit_to_user(1, -10.0)
    False
    """
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET credit = credit + ? WHERE id = ?', (amount, user_id))
        conn.commit()
        return True
    except:
        return False
    finally:
        if conn:
            conn.close()

def validate_imei(imei):
    """
    التحقق من صحة رقم IMEI
    
    >>> validate_imei('123456789012345')
    True
    >>> validate_imei('12345')
    False
    >>> validate_imei('abcdefghijklmno')
    False
    """
    if not imei.isdigit() or len(imei) != 15:
        return False
    return True

if __name__ == '__main__':
    import doctest
    doctest.testmod() 