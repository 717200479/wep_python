import sqlite3

def make_admin(username):
    """
    جعل مستخدم مديراً عن طريق تحديث قاعدة البيانات
    """
    try:
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # التحقق من وجود المستخدم
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            # تحديث المستخدم ليكون مديراً
            cursor.execute('UPDATE users SET is_admin = 1 WHERE username = ?', (username,))
            conn.commit()
            print(f"تم جعل المستخدم {username} مديراً بنجاح!")
        else:
            print(f"المستخدم {username} غير موجود!")
        
        conn.close()
    except Exception as e:
        print(f"حدث خطأ: {str(e)}")

if __name__ == '__main__':
    # يمكنك تغيير اسم المستخدم هنا
    username = input("أدخل اسم المستخدم الذي تريد جعله مديراً: ")
    make_admin(username) 