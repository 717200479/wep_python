from flask import Blueprint
from flask_restx import Api, Resource, fields, Namespace
from flask_login import current_user, login_required
from functools import wraps
from model import *

# إنشاء Blueprint للـ API
api_bp = Blueprint('api', __name__)
api = Api(api_bp,
    title='WEP API',
    version='1.0',
    description='توثيق API الخاص بنظام WEP',
    doc='/docs',
    default='WEP',
    default_label='الواجهات البرمجية الأساسية'
)

# التحقق من صلاحيات المشرف
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            api.abort(403, "غير مصرح لك بهذه العملية")
        return f(*args, **kwargs)
    return decorated_function

# تعريف Namespaces
auth_ns = Namespace('auth', description='عمليات المصادقة')
services_ns = Namespace('services', description='إدارة الخدمات')
users_ns = Namespace('users', description='إدارة المستخدمين')
notifications_ns = Namespace('notifications', description='إدارة الإشعارات')
imei_ns = Namespace('imei', description='خدمات IMEI')

# إضافة Namespaces للـ API
api.add_namespace(auth_ns)
api.add_namespace(services_ns)
api.add_namespace(users_ns)
api.add_namespace(notifications_ns)
api.add_namespace(imei_ns)

# نماذج البيانات
user_model = api.model('User', {
    'id': fields.Integer(readonly=True, description='معرف المستخدم'),
    'username': fields.String(required=True, description='اسم المستخدم'),
    'email': fields.String(required=True, description='البريد الإلكتروني'),
    'phone': fields.String(required=True, description='رقم الهاتف'),
    'credit': fields.Float(description='الرصيد'),
    'is_admin': fields.Boolean(description='صلاحيات المشرف')
})

service_model = api.model('Service', {
    'id': fields.Integer(readonly=True, description='معرف الخدمة'),
    'category': fields.String(required=True, description='فئة الخدمة'),
    'name': fields.String(required=True, description='اسم الخدمة'),
    'price': fields.Float(required=True, description='السعر'),
    'description': fields.String(required=True, description='وصف الخدمة'),
    'requirements': fields.String(description='المتطلبات')
})

notification_model = api.model('Notification', {
    'id': fields.Integer(readonly=True, description='معرف الإشعار'),
    'title': fields.String(required=True, description='عنوان الإشعار'),
    'message': fields.String(required=True, description='نص الإشعار'),
    'type': fields.String(description='نوع الإشعار'),
    'is_read': fields.Boolean(description='حالة القراءة'),
    'created_at': fields.DateTime(description='تاريخ الإنشاء')
})

imei_request_model = api.model('IMEIRequest', {
    'service_id': fields.Integer(required=True, description='معرف الخدمة'),
    'device': fields.String(required=True, description='نوع الجهاز'),
    'imei': fields.String(required=True, description='رقم IMEI')
})

# واجهات المصادقة
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc('تسجيل الدخول')
    @auth_ns.expect(api.model('LoginCredentials', {
        'username': fields.String(required=True, description='اسم المستخدم'),
        'password': fields.String(required=True, description='كلمة المرور')
    }))
    def post(self):
        """تسجيل الدخول للمستخدم"""
        pass

# واجهات الخدمات
@services_ns.route('/')
class ServiceList(Resource):
    @services_ns.doc('قائمة الخدمات')
    @services_ns.marshal_list_with(service_model)
    def get(self):
        """جلب قائمة الخدمات المتاحة"""
        return get_specialized_services()
    
    @services_ns.doc('إضافة خدمة')
    @services_ns.expect(service_model)
    @services_ns.marshal_with(service_model)
    @admin_required
    def post(self):
        """إضافة خدمة جديدة (للمشرفين فقط)"""
        pass

# واجهات المستخدمين
@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc('قائمة المستخدمين')
    @users_ns.marshal_list_with(user_model)
    @admin_required
    def get(self):
        """جلب قائمة المستخدمين (للمشرفين فقط)"""
        return get_all_users()

# واجهات الإشعارات
@notifications_ns.route('/')
class NotificationList(Resource):
    @notifications_ns.doc('إشعارات المستخدم')
    @notifications_ns.marshal_list_with(notification_model)
    @login_required
    def get(self):
        """جلب إشعارات المستخدم الحالي"""
        return get_user_notifications(current_user.id)

@notifications_ns.route('/<int:id>/read')
class NotificationRead(Resource):
    @notifications_ns.doc('تحديث حالة الإشعار')
    @login_required
    def put(self, id):
        """تحديث حالة الإشعار إلى مقروء"""
        mark_notification_as_read(id)
        return {'message': 'تم تحديث حالة الإشعار'}

# واجهات IMEI
@imei_ns.route('/request')
class IMEIRequest(Resource):
    @imei_ns.doc('تقديم طلب IMEI')
    @imei_ns.expect(imei_request_model)
    @login_required
    def post(self):
        """تقديم طلب خدمة IMEI جديد"""
        pass

# تسجيل Blueprint في التطبيق
def init_api(app):
    app.register_blueprint(api_bp, url_prefix='/api/v1') 