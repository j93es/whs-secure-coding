import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import admin_service as service

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- JWT 관련 함수 (관리자 전용) ---
@admin_bp.context_processor
def inject_current_user():
    token = request.cookies.get('admin_jwt')
    admin = None
    if token:
        payload = decode_admin_token(token)
        if payload and payload.get("admin"):
            admin = {'is_admin': True}
    return {'current_admin': admin}

def generate_admin_token():
    payload = {
        'admin': True,
        'exp': datetime.utcnow() + timedelta(hours=1)  # 토큰 유효기간 1시간
    }
    token = jwt.encode(payload, current_app.config['ADMIN_JWT_SECRET_KEY'], algorithm='HS256')
    return token

def decode_admin_token(token):
    try:
        payload = jwt.decode(token, current_app.config['ADMIN_JWT_SECRET_KEY'], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# --- 관리자 인증 데코레이터 ---
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = None
        # Authorization 헤더에서 토큰 확인
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        # 없으면 쿠키에서 확인
        elif request.cookies.get('admin_jwt'):
            token = request.cookies.get('admin_jwt')
        if not token:
            flash("관리자 로그인이 필요합니다.")
            return redirect(url_for('admin.login'))
        payload = decode_admin_token(token)
        if not payload or not payload.get("admin"):
            flash("유효하지 않은 토큰입니다. 다시 로그인 해주세요.")
            return redirect(url_for('admin.login'))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/')
def index():
    token = request.cookies.get('admin_jwt')
    if token:
        payload = decode_admin_token(token)
        if payload and payload.get("admin"):
            return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == current_app.config['ADMIN_ID'] and password == current_app.config['ADMIN_PW']:
            token = generate_admin_token()
            response = redirect(url_for('admin.dashboard'))
            
            secure_flag = request.is_secure or current_app.config.get('ENV') == 'production'
            response.set_cookie('admin_jwt', token, httponly=True, secure=secure_flag)
            flash("관리자 로그인 성공!")
            return response
        else:
            flash("잘못된 관리자 계정 정보입니다.")
            return redirect(url_for('admin.login'))
    return render_template('admin_login.html')

@admin_bp.after_request
def check_cookie_flags(response):
    if current_app.config.get('ENV') != 'production':
        return response
    
    set_cookie_header = response.headers.get('Set-Cookie')
    if set_cookie_header and 'admin_jwt=' in set_cookie_header:
        if 'HttpOnly' not in set_cookie_header:
            current_app.logger.warning("JWT cookie is missing HttpOnly flag!")
        if request.is_secure and 'Secure' not in set_cookie_header:
            current_app.logger.warning("JWT cookie is missing Secure flag in HTTPS environment!")
    return response

@admin_bp.route('/logout')
def logout():
    response = redirect(url_for('admin.login'))
    response.delete_cookie('admin_jwt')
    flash("로그아웃 되었습니다.")
    return response

# === 대시보드 ===
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

# === 신고 관리 ===
@admin_bp.route('/report')
@admin_required
def report():
    reports = service.list_reports()
    enriched_reports = []
    for report in reports:
        target_id = report.target_id
        # 대상이 상품인지 확인 (service.get_product)
        product = service.get_product(target_id)
        if product:
            target_type = 'product'
            target_name = product.title
            target_status = None
        else:
            # 대상이 유저인 경우 (service.get_user)
            user = service.get_user(target_id)
            if user:
                target_type = 'user'
                target_name = user.username
                target_status = user.status
            else:
                target_type = 'unknown'
                target_name = '알 수 없음'
                target_status = None
        enriched_reports.append({
            'id': report.id,
            'reporter_id': report.reporter_id,
            'target_id': target_id,
            'target_type': target_type,
            'target_name': target_name,
            'target_status': target_status,
            'reason': report.reason
        })
    return render_template('admin_report.html', reports=enriched_reports)

@admin_bp.route('/report/product/delete/<product_id>', methods=['POST'])
@admin_required
def report_delete_product(product_id):
    service.remove_product(product_id)
    flash("상품이 삭제되었습니다.")
    return redirect(url_for('admin.report'))

@admin_bp.route('/report/user/suspend/<user_id>', methods=['POST'])
@admin_required
def report_suspend_user(user_id):
    service.suspend_user(user_id)
    flash("유저가 휴먼 상태로 전환되었습니다.")
    return redirect(url_for('admin.report'))

@admin_bp.route('/report/user/restore/<user_id>', methods=['POST'])
@admin_required
def report_restore_user(user_id):
    service.restore_user(user_id)
    flash("유저가 활성 상태로 복구되었습니다.")
    return redirect(url_for('admin.report'))

# === 상품 관리 ===
@admin_bp.route('/products')
@admin_required
def products():
    products = service.list_products()
    return render_template('admin_products.html', products=products)

@admin_bp.route('/product/delete/<product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    service.remove_product(product_id)
    flash("상품이 삭제되었습니다.")
    return redirect(url_for('admin.products'))

# === 유저 관리 ===
@admin_bp.route('/users')
@admin_required
def users():
    users = service.get_user_list()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/user/suspend/<user_id>', methods=['POST'])
@admin_required
def suspend_user(user_id):
    service.suspend_user(user_id)
    flash("유저가 휴먼 상태로 전환되었습니다.")
    return redirect(url_for('admin.users'))

@admin_bp.route('/user/restore/<user_id>', methods=['POST'])
@admin_required
def restore_user(user_id):
    service.restore_user(user_id)
    flash("유저가 활성 상태로 복구되었습니다.")
    return redirect(url_for('admin.users'))

# === 채팅 관리 ===
@admin_bp.route('/chats')
@admin_required
def chats():
    chats = service.get_global_chats()
    return render_template('admin_chats.html', chats=chats, service=service)

@admin_bp.route('/chat/delete/<chat_id>', methods=['POST'])
@admin_required
def delete_chat(chat_id):
    service.remove_chat_message(chat_id)
    flash("채팅 메시지가 삭제되었습니다.")
    return redirect(url_for('admin.chats'))
