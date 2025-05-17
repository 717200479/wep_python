import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# إضافة العمود is_admin إذا لم يكن موجودًا
try:
    cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;')
except sqlite3.OperationalError:
    print("Column 'is_admin' already exists.")

# تعيين بعض المستخدمين كمديرين (على سبيل المثال، المستخدم الأول)
cursor.execute('UPDATE users SET is_admin = 1 WHERE id = 1;')

# تأكيد التغييرات
conn.commit()
conn.close()