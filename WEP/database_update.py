import sqlite3
from datetime import datetime

def update_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # إضافة عمود created_at إلى جدول users
        cursor.execute('''
            SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='created_at'
        ''')
        if cursor.fetchone()[0] == 0:
            # إضافة العمود بدون قيمة افتراضية
            cursor.execute('ALTER TABLE users ADD COLUMN created_at TIMESTAMP')
            # تحديث القيم الموجودة
            cursor.execute('UPDATE users SET created_at = ?', (current_time,))

        # إنشاء جدول transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # تحديث القيم الفارغة في جدول transactions
        cursor.execute('UPDATE transactions SET created_at = ? WHERE created_at IS NULL', (current_time,))

        # التحقق من وجود جدول imei_requests
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='imei_requests'")
        if cursor.fetchone() is not None:
            # إضافة عمود created_at إلى جدول imei_requests
            cursor.execute('''
                SELECT COUNT(*) FROM pragma_table_info('imei_requests') WHERE name='created_at'
            ''')
            if cursor.fetchone()[0] == 0:
                cursor.execute('ALTER TABLE imei_requests ADD COLUMN created_at TIMESTAMP')
                cursor.execute('UPDATE imei_requests SET created_at = ?', (current_time,))

        conn.commit()
        print("تم تحديث قاعدة البيانات بنجاح!")

    except Exception as e:
        print(f"حدث خطأ أثناء تحديث قاعدة البيانات: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_database() 