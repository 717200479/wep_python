import re
import sqlite3
import uuid
import jwt
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime, timedelta
from model import *
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # المفتاح السري لـ JWT

# تهيئة Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# إضافة متغير now لجميع القوالب
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# تعريف نموذج المستخدم
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data[0]
        self.username = user_data[1]
        self.email = user_data[3]
        self.phone = user_data[4]
        self.credit = user_data[5]
        self.is_admin = user_data[6]

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(user_data)
    return None

def generate_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)  # توكن صالح لمدة يوم
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

@app.route('/')
def home():
    expiration_time = None
    time_remaining_percentage = 0
    time_remaining_seconds = 0
    time_remaining_hours = 0
    session_max_seconds = 24 * 60 * 60  # 24 hours in seconds

    if current_user.is_authenticated:
        # التحقق من وجود توكن نشط للمستخدم الحالي
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT expiry_time 
            FROM tokens 
            WHERE user_id = ? AND is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (current_user.id,))
        
        token_data = cursor.fetchone()
        conn.close()
        
        if token_data:
            expiration_time = datetime.strptime(token_data[0], '%Y-%m-%d %H:%M:%S')
            # حساب الوقت المتبقي
            time_remaining = expiration_time - datetime.now()
            time_remaining_seconds = int(time_remaining.total_seconds())
            time_remaining_hours = round(time_remaining_seconds / 3600, 1)
            time_remaining_percentage = (time_remaining_seconds / session_max_seconds) * 100
            
            # تحديث وقت انتهاء الصلاحية في الجلسة
            session['expiration'] = expiration_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return render_template('home.html', 
                         expiration_time=expiration_time.strftime('%Y-%m-%d %H:%M:%S') if expiration_time else None,
                         time_remaining_percentage=time_remaining_percentage,
                         time_remaining_seconds=time_remaining_seconds,
                         time_remaining_hours=time_remaining_hours,
                         session_max_seconds=session_max_seconds)

@app.route('/tools_boxes', methods=['GET'])
def tools_boxes():
    logger.info("Accessed Tools & Boxes page.")
    return render_template('tools_boxes.html')

@app.route('/imei_services', methods=['GET', 'POST'])
def imei_services():
    if request.method == 'POST':
        device = request.form['device']
        imei = request.form['imei']
        flash('تم تقديم طلب الخدمة بنجاح!', 'success')
        logger.info(f"IMEI service requested for device: {device}, IMEI: {imei}")
        return redirect(url_for('imei_services'))
    
    logger.info("Accessed IMEI services page.")
    return render_template('imei_services.html')

@app.route('/remote', methods=['GET'])
def remote():
    logger.info("Accessed remote services page.")
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT brand FROM services')
    brands = cursor.fetchall()
    conn.close()
    
    return render_template('remote.html', brands=brands)

@app.route('/services/<brand>', methods=['GET'])
def get_services(brand):
    services = get_services_by_brand(brand)
    services_list = [{'name': service[0], 'description': service[1], 'price': service[2], 'requirements': service[3]} for service in services]
    return jsonify(services_list)

@app.route('/user_details')
@login_required
def user_details():
    # جلب التوكنات النشطة للمستخدم
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT device_info, created_at, expiry_time, is_active 
        FROM tokens 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (current_user.id,))
    
    tokens_data = cursor.fetchall()
    active_tokens = []
    expiration_time = None
    time_remaining_percentage = 0
    time_remaining_seconds = 0
    time_remaining_hours = 0
    session_max_seconds = 24 * 60 * 60  # 24 hours in seconds
    
    for token in tokens_data:
        token_expiry = datetime.strptime(token[2], '%Y-%m-%d %H:%M:%S')
        is_active = token[3]
        
        active_tokens.append({
            'device_info': token[0],
            'created_at': datetime.strptime(token[1], '%Y-%m-%d %H:%M:%S'),
            'expiry_time': token_expiry,
            'is_active': is_active
        })
        
        # حساب معلومات الجلسة للتوكن النشط الأحدث
        if is_active and (expiration_time is None or token_expiry > expiration_time):
            expiration_time = token_expiry
            time_remaining = expiration_time - datetime.now()
            time_remaining_seconds = int(time_remaining.total_seconds())
            time_remaining_hours = round(time_remaining_seconds / 3600, 1)
            time_remaining_percentage = (time_remaining_seconds / session_max_seconds) * 100

    # إنشاء سجل نشاطات وهمي (يمكن تعديله لاحقاً لجلب النشاطات الفعلية)
    activities = [
        {
            'timestamp': datetime.now() - timedelta(minutes=30),
            'description': 'تسجيل دخول جديد',
            'status': 'ناجح',
            'status_class': 'success'
        },
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'description': 'تحديث معلومات الحساب',
            'status': 'مكتمل',
            'status_class': 'info'
        },
        {
            'timestamp': datetime.now() - timedelta(days=1),
            'description': 'شحن رصيد',
            'status': 'مكتمل',
            'status_class': 'success'
        }
    ]

    conn.close()
    return render_template('user_details.html', 
                         active_tokens=active_tokens,
                         activities=activities,
                         expiration_time=expiration_time.strftime('%Y-%m-%d %H:%M:%S') if expiration_time else None,
                         time_remaining_percentage=time_remaining_percentage,
                         time_remaining_seconds=time_remaining_seconds,
                         time_remaining_hours=time_remaining_hours,
                         session_max_seconds=session_max_seconds)

import re

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            phone = request.form['phone']

            # تحقق من صحة المدخلات باستخدام Regex
            if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
                flash('اسم المستخدم يجب أن يتكون من 3 إلى 20 حرفًا أو رقمًا.', 'error')
                return render_template('register.html')

            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                flash('البريد الإلكتروني غير صالح.', 'error')
                return render_template('register.html')

            if not re.match(r'^\+?[0-9]{10,15}$', phone):
                flash('رقم الهاتف يجب أن يتكون من 10 إلى 15 رقمًا.', 'error')
                return render_template('register.html')

            try:
                hashed_password = hash_password(password)
                add_user(username, hashed_password, email, phone)
                logger.info(f"New user registered: {username}")
                flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                logger.warning(f"Registration failed - duplicate username/email/phone: {username}")
                flash('اسم المستخدم أو البريد الإلكتروني أو رقم الهاتف مستخدم بالفعل', 'error')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                flash('حدث خطأ أثناء التسجيل', 'error')
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error in register route: {str(e)}")
        flash('حدث خطأ غير متوقع', 'error')
        return render_template('register.html')

@app.route('/users', methods=['GET'])
def list_users():
    users = get_all_users()
    return jsonify(users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            logger.info(f"محاولة تسجيل دخول للمستخدم: {username}")
            
            user_data = get_user_by_username(username)
            if not user_data:
                logger.warning(f"فشل تسجيل الدخول: المستخدم غير موجود - {username}")
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
                return render_template('login.html')
            
            if verify_password(password, user_data[2]):  # user_data[2] هو كلمة المرور المشفرة
                user = User(user_data)
                login_user(user)
                
                # إنشاء توكن جديد
                token = str(uuid.uuid4())
                created_at = datetime.now()
                expiry_time = created_at + timedelta(days=1)
                
                # جمع معلومات الجهاز
                user_agent = request.headers.get('User-Agent', 'غير معروف')
                device_info = f"المتصفح: {user_agent}"
                
                try:
                    # حفظ التوكن في قاعدة البيانات
                    conn = sqlite3.connect('users.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO tokens (user_id, token, created_at, expiry_time, is_active, device_info)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user.id, token, created_at.strftime('%Y-%m-%d %H:%M:%S'),
                          expiry_time.strftime('%Y-%m-%d %H:%M:%S'), 1, device_info))
                    conn.commit()
                    conn.close()
                    
                    # تخزين معلومات التوكن في الجلسة
                    session['token'] = token
                    session['expiration'] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    logger.info(f"تم تسجيل دخول المستخدم بنجاح: {username}")
                    flash('تم تسجيل الدخول بنجاح!', 'success')
                    return redirect(url_for('home'))
                except Exception as e:
                    logger.error(f"خطأ في حفظ التوكن: {str(e)}")
                    flash('حدث خطأ أثناء تسجيل الدخول', 'error')
                    return render_template('login.html')
            else:
                logger.warning(f"فشل تسجيل الدخول: كلمة مرور غير صحيحة - {username}")
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        return render_template('login.html')
    except Exception as e:
        logger.error(f"خطأ في عملية تسجيل الدخول: {str(e)}")
        flash('حدث خطأ أثناء تسجيل الدخول', 'error')
        return render_template('login.html')

@app.route('/increase_credit', methods=['POST'])
@login_required
def increase_credit():
    logger.info("Accessed credit increase page.")
    
    if not current_user.is_admin:
        flash('غير مصرح لك بهذه العملية!', 'danger')
        return redirect(url_for('home'))
    
    username = request.form['username']
    password = request.form['password']
    credit_to_add = request.form['credit']

    user_data = get_user_by_username(username)
    if user_data and user_data[2] == hash_password(password):
        update_user_credit(user_data[0], credit_to_add)
        flash('تم زيادة الرصيد بنجاح!', 'success')
        logger.info(f"Credit increased for user: {username}")
    else:
        flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
        logger.warning(f"Credit increase failed for {username}: Invalid credentials.")

    return redirect(url_for('manage_services'))

@app.route('/admin/services')
@login_required
@admin_required
def manage_services():
    if not current_user.is_admin:
        flash('غير مصرح لك بهذه العملية!', 'danger')
        return redirect(url_for('home'))

    # جلب التوكنات النشطة للمستخدم
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT device_info, created_at, expiry_time, is_active 
        FROM tokens 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (current_user.id,))
    
    tokens_data = cursor.fetchall()
    active_tokens = []
    expiration_time = None
    time_remaining_percentage = 0
    time_remaining_seconds = 0
    time_remaining_hours = 0
    session_max_seconds = 24 * 60 * 60  # 24 hours in seconds
    
    for token in tokens_data:
        token_expiry = datetime.strptime(token[2], '%Y-%m-%d %H:%M:%S')
        is_active = token[3]
        
        active_tokens.append({
            'device_info': token[0],
            'created_at': datetime.strptime(token[1], '%Y-%m-%d %H:%M:%S'),
            'expiry_time': token_expiry,
            'is_active': is_active
        })
        
        # حساب معلومات الجلسة للتوكن النشط الأحدث
        if is_active and (expiration_time is None or token_expiry > expiration_time):
            expiration_time = token_expiry
            time_remaining = expiration_time - datetime.now()
            time_remaining_seconds = int(time_remaining.total_seconds())
            time_remaining_hours = round(time_remaining_seconds / 3600, 1)
            time_remaining_percentage = (time_remaining_seconds / session_max_seconds) * 100

    # إنشاء سجل نشاطات وهمي (يمكن تعديله لاحقاً لجلب النشاطات الفعلية)
    activities = [
        {
            'timestamp': datetime.now() - timedelta(minutes=30),
            'description': 'تم إضافة خدمة جديدة: فك قفل الشاشة لهواتف سامسونج',
            'status': 'تم بنجاح',
            'status_class': 'success'
        },
        {
            'timestamp': datetime.now() - timedelta(hours=2),
            'description': 'تم تحديث سعر خدمة فك شفرة آيفون',
            'status': 'مكتمل',
            'status_class': 'info'
        },
        {
            'timestamp': datetime.now() - timedelta(days=1),
            'description': 'تم حذف خدمة قديمة',
            'status': 'تم التنفيذ',
            'status_class': 'warning'
        }
    ]

    # جلب الخدمات المخصصة
    services = get_specialized_services()
    
    conn.close()
    return render_template('admin/manage_services.html', 
                         services=services,
                         users=get_all_users(),
                         active_tokens=active_tokens,
                         activities=activities,
                         expiration_time=expiration_time.strftime('%Y-%m-%d %H:%M:%S') if expiration_time else None,
                         time_remaining_percentage=time_remaining_percentage,
                         time_remaining_seconds=time_remaining_seconds,
                         time_remaining_hours=time_remaining_hours,
                         session_max_seconds=session_max_seconds)

@app.route('/api/services', methods=['POST'])
@admin_required
def add_service():
    try:
        # التحقق من وجود الخدمة مسبقاً
        category = request.form.get('serviceType')
        name = request.form.get('name')
        
        # البحث عن الخدمة في قاعدة البيانات
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM specialized_services 
            WHERE category = ? AND name = ? AND is_active = 1
        ''', (category, name))
        existing_service = cursor.fetchone()
        
        if existing_service:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'هذه الخدمة موجودة مسبقاً'
            })
        
        # إضافة الخدمة الجديدة
        cursor.execute('''
            INSERT INTO specialized_services (category, name, price, description, requirements, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (
            category,
            name,
            request.form.get('price'),
            request.form.get('description'),
            request.form.get('requirements')
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'تم إضافة الخدمة بنجاح'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/services/<int:service_id>', methods=['GET'])
@login_required
@admin_required
def get_service(service_id):
    services = get_specialized_services()
    service = next((s for s in services if s[0] == service_id), None)
    if service:
        return jsonify({
            'id': service[0],
            'category': service[1],
            'name': service[2],
            'price': service[3],
            'description': service[4],
            'requirements': service[5]
        })
    return jsonify({'success': False, 'error': 'Service not found'})

@app.route('/api/services/<int:service_id>', methods=['PUT'])
@login_required
@admin_required
def update_service(service_id):
    try:
        data = request.json
        update_specialized_service(
            service_id=service_id,
            category=data['category'],
            name=data['name'],
            price=float(data['price']),
            description=data['description'],
            requirements=data['requirements']
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/services/<int:service_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_service_status(service_id):
    try:
        delete_specialized_service(service_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/balance')
@login_required
def balance():
    return render_template('index.html', balance=current_user.credit)

@app.route('/logout')
@login_required
def logout():
    # تعطيل التوكن الحالي
    if current_user.is_authenticated:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tokens 
            SET is_active = 0 
            WHERE user_id = ? AND is_active = 1
        ''', (current_user.id,))
        conn.commit()
        conn.close()
    
    logout_user()
    session.clear()
    flash('تم تسجيل الخروج بنجاح!', 'success')
    return redirect(url_for('home'))

def save_token(user_id, token, timestamp):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tokens (user_id, token, created_at) VALUES (?, ?, ?)', (user_id, token, timestamp))
    conn.commit()
    conn.close()

@app.route('/api/imei-requests', methods=['POST'])
@login_required
def submit_imei_request():
    try:
        data = request.json
        service_id = data.get('service_id')
        device = data.get('device')
        imei = data.get('imei')
        
        if not all([service_id, device, imei]):
            return jsonify({
                'success': False,
                'error': 'جميع الحقول مطلوبة'
            })
        
        # التحقق من صحة رقم IMEI
        if not re.match(r'^\d{15}$', imei):
            return jsonify({
                'success': False,
                'error': 'رقم IMEI غير صالح'
            })
        
        # حفظ الطلب في قاعدة البيانات
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO imei_requests (user_id, service_id, device, imei, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', datetime('now'))
        ''', (current_user.id, service_id, device, imei))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'تم تقديم طلب الخدمة بنجاح'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)