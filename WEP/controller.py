<<<<<<< HEAD
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
from api import init_api
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # المفتاح السري لـ JWT

# تهيئة Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# تهيئة API
init_api(app)

logger = logging.getLogger(__name__)

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

@app.context_processor
def inject_notifications():
    """إضافة الإشعارات لجميع القوالب"""
    if current_user.is_authenticated:
        unread_count = get_unread_notifications_count(current_user.id)
        return {'notifications_count': unread_count}
    return {'notifications_count': 0}

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
            phone = request.form['phone']
            
            logger.debug(f"Registration attempt - Username: {username}, Phone: {phone}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            # التحقق من وجود المستخدم
            if get_user_by_username(username):
                logger.warning(f"Registration failed - Username already exists: {username}")
                flash('اسم المستخدم موجود بالفعل', 'error')
                return render_template('register.html')
            
            if get_user_by_phone(phone):
                logger.warning(f"Registration failed - Phone already exists: {phone}")
                flash('رقم الهاتف مسجل بالفعل', 'error')
                return render_template('register.html')
            
            # إنشاء المستخدم
            try:
                create_user(username, password, phone)
                logger.info(f"New user registered: {username}")
                logger.debug(f"User registration details - Username: {username}, Phone: {phone}")
                flash('تم إنشاء الحساب بنجاح!', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                logger.error(f"Error creating user: {str(e)}")
                logger.debug(f"User creation error details: {e.__class__.__name__}: {str(e)}")
                flash('حدث خطأ أثناء إنشاء الحساب', 'error')
                return render_template('register.html')
                
        return render_template('register.html')
    except Exception as e:
        logger.error(f"Error in register route: {str(e)}")
        logger.debug(f"Register route error details: {e.__class__.__name__}: {str(e)}")
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
            
            logger.debug(f"Login attempt - Username: {username}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            
            user_data = get_user_by_username(username)
            if not user_data:
                logger.warning(f"Login failed - User not found: {username}")
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
                return render_template('login.html')
            
            if verify_password(password, user_data[2]):
                user = User(user_data)
                login_user(user)
                
                logger.debug(f"User authenticated successfully: {username}")
                logger.debug(f"User session data: {dict(session)}")
                
                # إضافة إشعار ترحيب
                add_notification(
                    user_id=user.id,
                    title="مرحباً بعودتك!",
                    message=f"تم تسجيل دخولك بنجاح، {user.username}",
                    type="success"
                )
                
                # إنشاء توكن جديد
                token = str(uuid.uuid4())
                created_at = datetime.now()
                expiry_time = created_at + timedelta(days=1)
                
                # جمع معلومات الجهاز
                user_agent = request.headers.get('User-Agent', 'غير معروف')
                device_info = f"المتصفح: {user_agent}"
                
                logger.debug(f"Generated new token for user {username}: {token}")
                logger.debug(f"Device info: {device_info}")
                
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
                    
                    logger.debug(f"Token saved successfully for user {username}")
                    
                    # تخزين معلومات التوكن في الجلسة
                    session['token'] = token
                    session['expiration'] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    logger.info(f"تم تسجيل دخول المستخدم بنجاح: {username}")
                    flash('تم تسجيل الدخول بنجاح!', 'success')
                    return redirect(url_for('home'))
                except Exception as e:
                    logger.error(f"خطأ في حفظ التوكن: {str(e)}")
                    logger.debug(f"Token save error details: {e.__class__.__name__}: {str(e)}")
                    flash('حدث خطأ أثناء تسجيل الدخول', 'error')
                    return render_template('login.html')
            else:
                logger.warning(f"Login failed - Invalid password for user: {username}")
                flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        return render_template('login.html')
    except Exception as e:
        logger.error(f"خطأ في عملية تسجيل الدخول: {str(e)}")
        logger.debug(f"Login error details: {e.__class__.__name__}: {str(e)}")
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
        
        # إضافة إشعار للمستخدم عن زيادة الرصيد
        add_notification(
            user_id=user_data[0],
            title="تم زيادة الرصيد",
            message=f"تم إضافة {credit_to_add}$ إلى رصيدك",
            type="success"
        )
        
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
def add_specialized_service():
    try:
        category = request.form.get('serviceType')
        name = request.form.get('name')
        
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
        
        # إضافة إشعار للمشرفين
        admin_users = get_all_users()
        for user in admin_users:
            if user[5]:  # is_admin
                add_notification(
                    user_id=user[0],
                    title="تم إضافة خدمة جديدة",
                    message=f"تم إضافة خدمة جديدة: {name}",
                    type="info"
                )
        
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
        
        if not re.match(r'^\d{15}$', imei):
            return jsonify({
                'success': False,
                'error': 'رقم IMEI غير صالح'
            })
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO imei_requests (user_id, service_id, device, imei, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', datetime('now'))
        ''', (current_user.id, service_id, device, imei))
        
        # إضافة إشعار للمستخدم
        add_notification(
            user_id=current_user.id,
            title="تم استلام طلب IMEI",
            message=f"تم استلام طلبك للجهاز {device} برقم IMEI: {imei}",
            type="success"
        )
        
        # إضافة إشعار للمشرفين
        admin_users = get_all_users()
        for user in admin_users:
            if user[5]:  # is_admin
                add_notification(
                    user_id=user[0],
                    title="طلب IMEI جديد",
                    message=f"طلب جديد من {current_user.username} للجهاز {device}",
                    type="info"
                )
        
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

@app.route('/statistics')
@login_required
@admin_required
def statistics():
    """عرض صفحة الإحصائيات"""
    return render_template('statistics.html')

@app.route('/api/statistics/users')
@login_required
@admin_required
def get_user_statistics():
    """جلب إحصائيات المستخدمين"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # إحصائيات المستخدمين الجدد حسب التاريخ
    cursor.execute('''
        SELECT date(created_at) as reg_date, COUNT(*) as count 
        FROM users 
        GROUP BY date(created_at) 
        ORDER BY reg_date 
        LIMIT 30
    ''')
    user_stats = cursor.fetchall()
    
    # إجمالي عدد المستخدمين
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # عدد المستخدمين النشطين (لديهم توكن نشط)
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) 
        FROM tokens 
        WHERE is_active = 1 AND expiry_time > datetime('now')
    ''')
    active_users = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'user_growth': {
            'labels': [date for date, _ in user_stats],
            'data': [count for _, count in user_stats]
        },
        'total_users': total_users,
        'active_users': active_users
    })

@app.route('/api/statistics/services')
@login_required
@admin_required
def get_service_statistics():
    """جلب إحصائيات الخدمات"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # الخدمات الأكثر طلباً
        cursor.execute('''
            SELECT s.name, COUNT(ir.id) as count 
            FROM specialized_services s
            LEFT JOIN imei_requests ir ON ir.service_id = s.id
            WHERE s.is_active = 1
            GROUP BY s.name 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        service_stats = cursor.fetchall()
        
        # إحصائيات حسب حالة الطلب
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM imei_requests 
            GROUP BY status
        ''')
        status_stats = cursor.fetchall()

        # إجمالي عدد الطلبات
        cursor.execute('SELECT COUNT(*) FROM imei_requests')
        total_requests = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'popular_services': {
                'labels': [service[0] for service in service_stats] if service_stats else [],
                'data': [service[1] for service in service_stats] if service_stats else []
            },
            'request_status': {
                'labels': [status[0] for status in status_stats] if status_stats else [],
                'data': [status[1] for status in status_stats] if status_stats else []
            },
            'total_requests': total_requests
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics/revenue')
@login_required
@admin_required
def get_revenue_statistics():
    """جلب إحصائيات الإيرادات"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # الإيرادات اليومية
        cursor.execute('''
            SELECT date(created_at) as tx_date, 
                   SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END) as daily_revenue 
            FROM transactions 
            GROUP BY date(created_at) 
            ORDER BY tx_date 
            LIMIT 30
        ''')
        revenue_stats = cursor.fetchall()
        
        # إجمالي الإيرادات
        cursor.execute('''
            SELECT SUM(CASE WHEN type = 'credit' THEN amount ELSE -amount END) 
            FROM transactions
        ''')
        total_revenue = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'daily_revenue': {
                'labels': [date for date, _ in revenue_stats] if revenue_stats else [],
                'data': [float(amount) for _, amount in revenue_stats] if revenue_stats else []
            },
            'total_revenue': float(total_revenue)
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/notifications')
@login_required
def notifications():
    """صفحة الإشعارات"""
    user_notifications = get_user_notifications(current_user.id)
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    """تحديث حالة الإشعار إلى مقروء"""
    mark_notification_as_read(notification_id)
    return jsonify({'success': True})

@app.route('/notifications/get_unread')
@login_required
def get_unread_count():
    """جلب عدد الإشعارات غير المقروءة"""
    count = get_unread_notifications_count(current_user.id)
    return jsonify({'count': count})

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """عرض لوحة تحكم المشرف"""
    return render_template('admin/dashboard.html')

@app.route('/api/admin/stats')
@login_required
@admin_required
def get_admin_stats():
    """جلب إحصائيات لوحة التحكم"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # إحصائيات المستخدمين النشطين
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) 
            FROM tokens 
            WHERE is_active = 1 AND expiry_time > datetime('now')
        ''')
        active_users = cursor.fetchone()[0]

        # الإيرادات اليومية
        cursor.execute('''
            SELECT SUM(amount) 
            FROM transactions 
            WHERE date(created_at) = date('now')
        ''')
        daily_revenue = cursor.fetchone()[0] or 0

        # الطلبات المعلقة
        cursor.execute('SELECT COUNT(*) FROM imei_requests WHERE status = "pending"')
        pending_requests = cursor.fetchone()[0]

        # الخدمات النشطة
        cursor.execute('SELECT COUNT(*) FROM specialized_services WHERE is_active = 1')
        active_services = cursor.fetchone()[0]

        # بيانات المستخدمين للرسم البياني
        cursor.execute('''
            SELECT date(created_at) as reg_date, COUNT(*) as count 
            FROM users 
            GROUP BY date(created_at) 
            ORDER BY reg_date DESC 
            LIMIT 30
        ''')
        users_data = cursor.fetchall()

        # بيانات الإيرادات للرسم البياني
        cursor.execute('''
            SELECT date(created_at) as tx_date, SUM(amount) as daily_amount 
            FROM transactions 
            GROUP BY date(created_at) 
            ORDER BY tx_date DESC 
            LIMIT 30
        ''')
        revenue_data = cursor.fetchall()

        # بيانات الخدمات للرسم البياني
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM specialized_services 
            GROUP BY category
        ''')
        services_data = cursor.fetchall()

        return jsonify({
            'activeUsers': active_users,
            'dailyRevenue': daily_revenue,
            'pendingRequests': pending_requests,
            'activeServices': active_services,
            'users': {
                'labels': [row[0] for row in users_data],
                'data': [row[1] for row in users_data]
            },
            'revenue': {
                'labels': [row[0] for row in revenue_data],
                'data': [row[1] for row in revenue_data]
            },
            'services': {
                'labels': [row[0] for row in services_data],
                'data': [row[1] for row in services_data]
            }
        })
    finally:
        conn.close()

@app.route('/api/admin/activity')
@login_required
@admin_required
def get_admin_activity():
    """جلب سجل النشاطات الأخيرة"""
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    try:
        # جلب آخر النشاطات من جدول النشاطات
        cursor.execute('''
            SELECT title, description, type, created_at 
            FROM activities 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        activities = cursor.fetchall()
        
        return jsonify([{
            'title': activity[0],
            'description': activity[1],
            'type': activity[2],
            'time': activity[3]
        } for activity in activities])
    finally:
        conn.close()

@app.route('/api/admin/system-status')
@login_required
@admin_required
def get_system_status():
    """جلب حالة النظام"""
    import psutil
    
    return jsonify({
        'server': 'نشط',
        'database': 'متصل',
        'memory': round(psutil.virtual_memory().percent),
        'cpu': round(psutil.cpu_percent())
    })

@app.route('/api/admin/users', methods=['POST'])
@login_required
@admin_required
def add_user():
    """إضافة مستخدم جديد"""
    data = request.get_json()
    
    if not all(key in data for key in ['username', 'email', 'password']):
        return jsonify({'error': 'البيانات غير مكتملة'}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # التحقق من عدم وجود المستخدم
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?',
                      (data['username'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'اسم المستخدم أو البريد الإلكتروني مستخدم بالفعل'}), 400
        
        # إضافة المستخدم
        cursor.execute('''
            INSERT INTO users (username, email, password, is_admin, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (
            data['username'],
            data['email'],
            hash_password(data['password']),
            bool(data.get('isAdmin', False))
        ))
        
        # تسجيل النشاط
        user_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO activities (title, description, type, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (
            'إضافة مستخدم جديد',
            f'تم إضافة المستخدم {data["username"]}',
            'success'
        ))
        
        conn.commit()
        return jsonify({'success': True}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/services', methods=['POST'])
@login_required
@admin_required
def admin_add_service():
    """إضافة خدمة جديدة"""
    data = request.get_json()
    
    if not all(key in data for key in ['name', 'category', 'price', 'description']):
        return jsonify({'error': 'البيانات غير مكتملة'}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # إضافة الخدمة
        cursor.execute('''
            INSERT INTO specialized_services (name, category, price, description, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, datetime('now'))
        ''', (
            data['name'],
            data['category'],
            float(data['price']),
            data['description']
        ))
        
        # تسجيل النشاط
        service_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO activities (title, description, type, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (
            'إضافة خدمة جديدة',
            f'تم إضافة خدمة {data["name"]}',
            'success'
        ))
        
        conn.commit()
        return jsonify({'success': True}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
=======
import re
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from model import *

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/tools_boxes', methods=['GET'])
def tools_boxes():
    logger.info("Accessed Tools & Boxes page.")
    return render_template('tools_boxes.html')

@app.route('/imei_services', methods=['GET', 'POST'])
def imei_services():
    if request.method == 'POST':
        device = request.form['device']
        imei = request.form['imei']
        # Process the service request here
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

@app.route('/user_details', methods=['GET'])
def user_details():
    if 'user_id' not in session:
        flash('يجب تسجيل الدخول لعرض التفاصيل.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    if user:
        logger.info(f"Fetched user details for user ID {user_id}")
        return render_template('user_details.html', user=user)
    else:
        flash('لم يتم العثور على المستخدم.', 'danger')
        return redirect(url_for('home'))

import re

@app.route('/register', methods=['GET', 'POST'])
def register():
    logger.info("Accessed registration page.")
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        smartphone_services = request.form.get('smartphone_services', 'no')  # قيمة افتراضية
        
        # تحقق من صحة المدخلات
        if not username or not password or not email or not phone:
            flash('جميع الحقول مطلوبة!', 'danger')
            return render_template('register.html')

        # استخدام REGEX للتحقق من كلمة المرور
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[\W_]).{8,}$', password):
            flash('خطأ: يجب أن تتكون كلمة المرور من 8 أحرف على الأقل، وتحتوي على أحرف وأرقام ورموز خاصة.', 'danger')
            return render_template('register.html')

        password_hashed = hash_password(password)
        
        try:
            add_user(username, password_hashed, email, phone, smartphone_services == 'yes')
            flash('تم التسجيل بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
            logger.info(f"User registered: {username}")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('اسم المستخدم أو البريد الإلكتروني موجود بالفعل!', 'danger')
            logger.warning(f"Registration failed for {username}: User already exists.")
        except Exception as e:
            flash('حدث خطأ أثناء التسجيل، يرجى المحاولة لاحقًا.', 'danger')
            logger.error(f"Registration error for {username}: {str(e)}")

    return render_template('register.html')

@app.route('/users', methods=['GET'])
def list_users():
    users = get_all_users()
    return jsonify(users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Accessed login page.")
    
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        user = get_user_by_username(username)
        
        if user and user[2] == password:
            session['user_id'] = user[0]
            session['is_admin'] = user[6]
            flash('Logged in successfully!', 'success')
            logger.info(f"User logged in: {username}")
            return redirect(url_for('balance'))
        else:
            flash('Invalid username or password!', 'danger')
            logger.warning(f"Login failed for {username}: Invalid credentials.")
    
    return render_template('login.html')

@app.route('/increase_credit', methods=['POST'])
def increase_credit():
    logger.info("Accessed credit increase page.")
    
    username = request.form['username']
    password = request.form['password']
    credit_to_add = request.form['credit']

    user = get_user_by_username(username)
    if user and user[2] == hash_password(password):
        update_user_credit(user[0], credit_to_add)
        flash('تم زيادة الرصيد بنجاح!', 'success')
        logger.info(f"Credit increased for user: {username}")
    else:
        flash('اسم المستخدم أو كلمة المرور غير صحيحة!', 'danger')
        logger.warning(f"Credit increase failed for {username}: Invalid credentials.")

    return redirect(url_for('manage_services'))

@app.route('/admin/services', methods=['GET', 'POST'])
def manage_services():
    if request.method == 'POST':
        if 'add' in request.form:
            brand = request.form['brand']
            name = request.form['name']
            price = request.form['price']
            description = request.form['description']
            requirements = request.form['requirements']
            add_service(brand, name, price, description, requirements)
            flash('تم إضافة الخدمة بنجاح!', 'success')
            logger.info(f"Service added: {name}")

        elif 'delete' in request.form:
            service_id = request.form['service_id']
            delete_service(service_id)
            flash('تم حذف الخدمة بنجاح!', 'success')
            logger.info(f"Service deleted: {service_id}")

        elif 'edit' in request.form:
            service_id = request.form['service_id']
            brand = request.form['brand']
            name = request.form['name']
            price = request.form['price']
            description = request.form['description']
            requirements = request.form['requirements']
            update_service(service_id, brand, name, price, description, requirements)
            flash('تم تعديل الخدمة بنجاح!', 'success')
            logger.info(f"Service updated: {service_id}")

    users = get_all_users()
    services = get_all_services()
    
    return render_template('manage_services.html', services=services, users=users)

@app.route('/balance', methods=['GET'])
def balance():
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user:
            return render_template('index.html', balance=user[3])
    return redirect(url_for('login'))

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    logger.info("User logged out.")
    return redirect(url_for('home'))

if __name__ == '__main__':
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818
    app.run(debug=True)