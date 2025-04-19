import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import user_service as service
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

user_bp = Blueprint('user', __name__)


def get_user_id():
    # 예시: JWT 토큰에서 사용자 ID 추출
    token = request.cookies.get('jwt')
    if token:
        try:
            payload = decode_token(token)  # 직접 구현한 함수
            return payload.get('user_id')
        except:
            return get_remote_address()
    return get_remote_address()

# 커스텀 키 함수 사용
limiter = Limiter(
    key_func=get_user_id,
    default_limits=["100 per minute"]
)

# === JWT 관련 ===
@user_bp.context_processor
def inject_current_user():
    token = request.cookies.get('jwt')
    user = None
    if token:
        payload = decode_token(token)
        if payload:
            user = service.get_user(payload['user_id'])
    return {'current_user': user}

def generate_token(user_id):
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1)  # 토큰 유효기간 1시간
    }
    token = jwt.encode(payload, current_app.config['CLIENT_JWT_SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['CLIENT_JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# --- JWT 인증 데코레이터 ---
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = None
        # 우선 Authorization 헤더에서 확인
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        # 없으면 쿠키에서 확인
        elif request.cookies.get('jwt'):
            token = request.cookies.get('jwt')
        if not token:
            flash("로그인이 필요합니다.")
            return redirect(url_for('user.login'))
        payload = decode_token(token)
        if not payload:
            flash("유효하지 않은 토큰입니다. 다시 로그인 해주세요.")
            return redirect(url_for('user.login'))
        user = service.get_user(payload['user_id'])
        if user and user.status == '휴먼':
            flash("해당 계정은 휴먼 상태이므로 이 기능을 사용할 수 없습니다. 관리자에게 문의하세요.")
            return redirect(url_for('user.login'))
        # 인증된 사용자 정보를 request 객체에 저장 (추후 사용)
        request.user = user
        return func(*args, **kwargs)
    return wrapper

# === 기본 라우트 ===
@user_bp.route('/')
def index():
    token = request.cookies.get('jwt')
    if token and decode_token(token):
        return redirect(url_for('user.dashboard'))
    return render_template('index.html')

# === 로그인 관련 ===
@user_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_id, error = service.register_user(username, password)
        if error:
            flash(error)
            return redirect(url_for('user.register'))
        flash("회원가입이 완료되었습니다. 로그인 해주세요.")
        return redirect(url_for('user.login'))
    return render_template('register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        # (원하는 경우 WTForms 등을 사용해 입력 검증 수행)
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        # bcrypt 및 계정 잠금 로직이 포함된 로그인 서비스 호출
        user, error = service.login_user(username, password)
        if error:
            flash(error)
            return redirect(url_for('user.login'))
        
        token = generate_token(user.id)
        response = redirect(url_for('user.dashboard'))
        
        # HTTPS 환경 또는 production 환경에서 Secure 플래그 적용
        secure_flag = request.is_secure or current_app.config.get('ENV') == 'production'
        response.set_cookie('jwt', token, httponly=True, secure=secure_flag)
        
        flash("로그인 성공!")
        return response
    return render_template('login.html')


@user_bp.after_request
def check_cookie_flags(response):
    if current_app.config.get('ENV') != 'production':
        return response
    
    set_cookie_header = response.headers.get('Set-Cookie')
    if set_cookie_header and 'jwt=' in set_cookie_header:
        if 'HttpOnly' not in set_cookie_header:
            current_app.logger.warning("JWT cookie is missing HttpOnly flag!")
        if request.is_secure and 'Secure' not in set_cookie_header:
            current_app.logger.warning("JWT cookie is missing Secure flag in HTTPS environment!")
    return response

@user_bp.route('/logout')
def logout():
    response = redirect(url_for('user.index'))
    response.delete_cookie('jwt')
    flash("로그아웃되었습니다.")
    return response

# === 대시보드 관련 ===
@user_bp.route('/dashboard')
@login_required
def dashboard():
    user = request.user
    products = service.list_products()
    global_chats = service.get_global_chats()
    return render_template('dashboard.html', user=user, products=products, global_chats=global_chats, service=service)

# === 프로필 관련 ===
@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        service.update_bio(request.user.id, bio)
        flash("프로필이 업데이트되었습니다.")
        return redirect(url_for('user.profile'))
    user = request.user
    return render_template('profile.html', user=user)

@user_bp.route('/profile/password', methods=['GET', 'POST'])
@login_required
def update_password_route():
    if request.method == 'POST':
        new_password = request.form['new_password']
        user_id, error = service.update_password(request.user.id, new_password)
        if error:
            flash(error)
            return redirect(url_for('user.update_password_route'))
        flash("비밀번호가 업데이트되었습니다.")
        return redirect(url_for('user.profile'))
    return render_template('update_password.html')

# === 상품 관련 ===
@user_bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        service.add_product(title, description, price, request.user.id)
        flash("상품이 등록되었습니다.")
        return redirect(url_for('user.dashboard'))
    return render_template('new_product.html')

@user_bp.route('/product/<product_id>')
@login_required
def view_product(product_id):
    product = service.get_product(product_id)
    if not product:
        flash("상품을 찾을 수 없습니다.")
        return redirect(url_for('user.dashboard'))
    seller = service.get_user(product.seller_id)
    return render_template('view_product.html', product=product, seller=seller)

@user_bp.route('/product/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        product, error = service.update_product_by_user(request.user.id, product_id, title, description, price)
        if error:
            flash(error)
            return redirect(url_for('user.dashboard'))
        flash("상품이 수정되었습니다.")
        return redirect(url_for('user.view_product', product_id=product_id))
    # GET 요청 시 상품 존재 여부만 확인 (추가 검증은 서비스 함수에서 수행했으므로)
    product = service.get_product(product_id)
    if not product:
        flash("상품을 찾을 수 없습니다.")
        return redirect(url_for('user.dashboard'))
    return render_template('edit_product.html', product=product)

@user_bp.route('/product/delete/<product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product_id, error = service.delete_product_by_user(request.user.id, product_id)
    if error:
        flash(error)
        return redirect(url_for('user.dashboard'))
    flash("상품이 삭제되었습니다.")
    return redirect(url_for('user.dashboard'))

@user_bp.route('/product/search', methods=['GET'])
@login_required
def search_products_route():
    query = request.args.get('q', '')
    products = []
    if query:
        products = service.search_products(query)
    return render_template('product_search_results.html', products=products, query=query)

# === 신고 관련 ===
@user_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        target_id = request.form['target_id']
        reason = request.form['reason']
        report_id, error = service.file_report(request.user.id, target_id, reason)
        if error:
            flash(error)
        else:
            flash("신고가 접수되었습니다.")
        return redirect(url_for('user.dashboard'))
    return render_template('report.html')

# === 사용자 관련 ===
@user_bp.route('/users')
@login_required
def users():
    all_users = service.get_user_list()
    all_users = [user for user in all_users if user.status != '휴먼']
    return render_template('users.html', users=all_users)

@user_bp.route('/user/<user_id>')
@login_required
def user_detail(user_id):
    target_user = service.get_user(user_id)
    if not target_user or target_user.status == '휴먼':
        flash("사용자를 찾을 수 없습니다.")
        return redirect(url_for('user.users'))
    private_chats = service.get_private_chats(request.user.id, user_id)
    return render_template('user_detail.html', user=target_user, private_chats=private_chats, service=service)

# === 채팅 관련 ===
@user_bp.route('/chat/<recipient_id>')
@login_required
def chat(recipient_id):
    recipient = service.get_user(recipient_id)
    if not recipient:
        flash("대화 상대를 찾을 수 없습니다.")
        return redirect(url_for('user.dashboard'))
    return render_template('chat.html', recipient=recipient)

# === 송금 관련 ===
@user_bp.route('/wallet')
@login_required
def wallet():
    user = request.user
    transactions = service.get_wallet_transactions(request.user.id)
    return render_template('wallet.html', user=user, transactions=transactions, service=service)

@user_bp.route('/user/<user_id>/transfer', methods=['GET', 'POST'])
@login_required
def transfer_funds_route(user_id):
    recipient = service.get_user(user_id)
    if not recipient:
        flash("대상 사용자를 찾을 수 없습니다.")
        return redirect(url_for('user.users'))
    if request.method == 'POST':
        amount = request.form.get('amount')
        success, message = service.transfer_funds(request.user.id, user_id, amount)
        flash(message)
        return redirect(url_for('user.user_detail', user_id=user_id))
    return render_template('transfer_funds.html', recipient=recipient)

