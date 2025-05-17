from flask import render_template
from flask_login import login_required, current_user
from datetime import datetime
import sqlite3

@app.route('/my-account')
@login_required
def my_account():
    # جلب التوكنات النشطة للمستخدم الحالي
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT device_info, created_at, last_used_at, expiry_time 
        FROM tokens 
        WHERE user_id = ? AND is_active = 1 
        ORDER BY created_at DESC
    ''', (current_user.id,))
    
    tokens_data = cursor.fetchall()
    conn.close()
    
    # تحويل البيانات إلى كائنات لسهولة استخدامها في القالب
    active_tokens = []
    for token in tokens_data:
        active_tokens.append({
            'device_info': token[0],
            'created_at': datetime.strptime(token[1], '%Y-%m-%d %H:%M:%S'),
            'last_used_at': datetime.strptime(token[2], '%Y-%m-%d %H:%M:%S') if token[2] else None,
            'expiry_time': datetime.strptime(token[3], '%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('my_account.html', user=current_user, active_tokens=active_tokens) 