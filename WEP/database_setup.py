import sqlite3
<<<<<<< HEAD
from datetime import datetime, timedelta
=======
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
<<<<<<< HEAD
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            credit REAL DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
=======
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL UNIQUE,
            credit INTEGER DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818
        )
    ''')

    # إنشاء جدول الخدمات إذا لم يكن موجودًا
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

<<<<<<< HEAD
    # إنشاء جدول النشاطات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            type TEXT CHECK(type IN ('success', 'warning', 'danger', 'info')) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # إنشاء جدول المعاملات المالية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('credit', 'debit')) NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # تحديث جدول التوكنات مع الأعمدة الجديدة
    # أولاً، نحفظ البيانات القديمة
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tokens'")
    if cursor.fetchone() is not None:
        cursor.execute("ALTER TABLE tokens RENAME TO tokens_old")
        
        # نقل البيانات القديمة إلى الجدول الجديد
        cursor.execute('''
            CREATE TABLE tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                token_type TEXT DEFAULT 'access',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expiry_time TIMESTAMP NOT NULL,
                last_used_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                device_info TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                CHECK (token_type IN ('access', 'refresh', 'reset_password'))
            )
        ''')
        
        # نقل البيانات القديمة
        cursor.execute('''
            INSERT INTO tokens (user_id, token, created_at)
            SELECT user_id, token, created_at FROM tokens_old
        ''')
        
        # تحديث expiry_time للتوكنات القديمة
        cursor.execute('''
            UPDATE tokens 
            SET expiry_time = datetime(created_at, '+1 day'),
                token_type = 'access',
                is_active = 1
            WHERE expiry_time IS NULL
        ''')
        
        # حذف الجدول القديم
        cursor.execute("DROP TABLE tokens_old")
    else:
        # إنشاء جدول التوكنات الجديد إذا لم يكن موجوداً
        cursor.execute('''
            CREATE TABLE tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                token_type TEXT DEFAULT 'access',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expiry_time TIMESTAMP NOT NULL,
                last_used_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                device_info TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                CHECK (token_type IN ('access', 'refresh', 'reset_password'))
            )
        ''')

    # إضافة فهرس للبحث السريع
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tokens_user 
        ON tokens(user_id, is_active)
    ''')

=======
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818
    conn.commit()
    conn.close()

if __name__ == '__main__':
<<<<<<< HEAD
    init_db()  # تهيئة قاعدة البيانات عند تشغيل البرنامج
=======
    init_db()
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818
