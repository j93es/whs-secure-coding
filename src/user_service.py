# service.py
import re
import bcrypt
import repository
from datetime import datetime, timedelta
from utils import sanitize_input, safe_int


# === 사용자 관련 서비스 ===

def check_password(password):
    password = sanitize_input(password)
    
    # 비밀번호 검증: 6~128자, 최소 하나의 영문자와 하나의 숫자 포함
    if len(password) < 6 or len(password) > 16:
        return "비밀번호는 6자 이상 16자 이하이어야 합니다."
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return "비밀번호는 최소한 하나의 영문자와 하나의 숫자를 포함해야 합니다."
    return None
    
def register_user(username, password):
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    # 사용자명 검증: 3~25자, 영문, 숫자, 밑줄(_)만 허용
    if not re.fullmatch(r'[A-Za-z0-9_]{5,10}', username):
        return None, "사용자명은 5자 이상 10자 이하의 영문, 숫자 및 밑줄(_)만 사용할 수 있습니다."
    
    # 이미 존재하는 사용자명인지 확인
    if repository.get_user_by_username(username):
        return None, "이미 존재하는 사용자명입니다."
    
    # 비밀번호 검증
    error_message = check_password(password)
    if error_message:
        return None, error_message
    
    # bcrypt를 사용하여 고유 salt와 함께 비밀번호 해시 생성
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # 해시값은 바이트 문자열이므로, 저장하기 위해 디코딩합니다.
    hashed_password = hashed_password.decode('utf-8')
    
    # 모든 검증 통과 시 사용자 생성
    user_id = repository.create_user(username, hashed_password)
    return user_id, None

# 로그인 실패 횟수 제한 및 잠금 시간(초)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 예: 5분 (300초)

def login_user(username, password):
    username = sanitize_input(username)
    password = sanitize_input(password)
    
    user = repository.get_user_by_username(username)
    if not user:
        # 사용자 존재하지 않으면 바로 오류 반환 (실패 횟수 업데이트 불가)
        return None, "아이디 또는 비밀번호가 올바르지 않습니다."

    now = datetime.utcnow()
    if user.lockout_until:
        # 문자열을 datetime 객체로 변환합니다.
        lockout_until = datetime.strptime(user.lockout_until, '%Y-%m-%d %H:%M:%S.%f')
        if lockout_until > now:
            remaining = safe_int((lockout_until - now).total_seconds())
            return None, f"계정이 잠겨있습니다. {remaining}초 후에 다시 시도해 주세요."

    # 비밀번호 확인
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        # 로그인 실패: 실패 횟수를 증가시킴
        failed_attempts = user.failed_attempts + 1
        repository.update_failed_attempts(user.id, failed_attempts)

        if failed_attempts >= MAX_FAILED_ATTEMPTS:
            # 실패 횟수가 허용치를 초과하면 계정 잠금 설정
            lockout_until = now + timedelta(seconds=LOCKOUT_DURATION)
            repository.set_lockout(user.id, lockout_until)
            return None, "로그인 실패 횟수가 너무 많아 계정이 잠겼습니다. 잠시 후에 다시 시도해 주세요."
        else:
            remaining = MAX_FAILED_ATTEMPTS - failed_attempts
            return None, f"아이디 또는 비밀번호가 올바르지 않습니다. 남은 시도 횟수: {remaining}"
    else:
        # 비밀번호 일치 시, 실패 횟수 및 잠금 정보 초기화
        repository.reset_failed_attempts(user.id)
        if user.status == '휴먼':
            return None, "해당 계정은 휴먼 상태이므로 로그인할 수 없습니다. 관리자에게 문의하세요."
        return user, None


def get_user(user_id):
    user_id = sanitize_input(user_id)
    
    return repository.get_user_by_id(user_id)

def get_user_list():
    return repository.get_all_users()

def update_bio(user_id, bio):
    user_id = sanitize_input(user_id)
    bio = sanitize_input(bio)
    
    if len(bio) > 500:
        return None, "자기 소개는 500자 이내로 작성해 주세요."
    repository.update_user_bio(user_id, bio)
    return user_id, None

def update_password(user_id, new_password):
    user_id = sanitize_input(user_id)
    new_password = sanitize_input(new_password)
    
    error_message = check_password(new_password)
    if error_message:
        return None, error_message
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    repository.update_user_password(user_id, hashed_password)
    return user_id, None

# === 상품 관련 서비스 ===
PRODUCT_TITLE_MAX_LENGTH = 100
PRODUCT_DESCRIPTION_MAX_LENGTH = 500
PRODUCT_PRICE_MIN = 0

def add_product(title, description, price, seller_id):
    title = sanitize_input(title)
    description = sanitize_input(description)
    seller_id = sanitize_input(seller_id)
    price = safe_int(price, use_abort=True)   # 가격을 정수로 변환
    
    if len(title) > PRODUCT_TITLE_MAX_LENGTH:
        return None, f'상품명은 {PRODUCT_TITLE_MAX_LENGTH}자 이내로 작성해 주세요.'
    if len(description) > PRODUCT_DESCRIPTION_MAX_LENGTH:
        return None, f'상품 설명은 {PRODUCT_DESCRIPTION_MAX_LENGTH}자 이내로 작성해 주세요.'
    if price < 0:
        return None, f'가격은 {PRODUCT_PRICE_MIN} 이상이어야 합니다.'
    return repository.create_product(title, description, price, seller_id)

def list_products():
    return repository.get_all_products()

def get_product(product_id):
    product_id = sanitize_input(product_id)
    
    return repository.get_product_by_id(product_id)


def update_product_by_user(user_id, product_id, title, description, price):
    user_id = sanitize_input(user_id)
    product_id = sanitize_input(product_id)
    title = sanitize_input(title)
    description = sanitize_input(description)
    price = safe_int(price, use_abort=True)   # 가격을 정수로 변환
    
    if len(title) > PRODUCT_TITLE_MAX_LENGTH:
        return None, f'상품명은 {PRODUCT_TITLE_MAX_LENGTH}자 이내로 작성해 주세요.'
    if len(description) > PRODUCT_DESCRIPTION_MAX_LENGTH:
        return None, f'상품 설명은 {PRODUCT_DESCRIPTION_MAX_LENGTH}자 이내로 작성해 주세요.'
    if price < 0:
        return None, f'가격은 {PRODUCT_PRICE_MIN} 이상이어야 합니다.'
    
    product = get_product(product_id)
    if not product:
        return None, "상품을 찾을 수 없습니다."
    if product.seller_id != user_id:
        return None, "수정 권한이 없습니다."
    repository.edit_product(product_id, title, description, price)
    return product, None

def delete_product_by_user(user_id, product_id):
    user_id = sanitize_input(user_id)
    product_id = sanitize_input(product_id)
    
    product = get_product(product_id)
    if not product:
        return None, "상품을 찾을 수 없습니다."
    if product.seller_id != user_id:
        return None, "삭제 권한이 없습니다."
    repository.delete_product(product_id)
    return product_id, None
    
def search_products(query):
    query = sanitize_input(query)
    
    return repository.search_products(query)  # 주의: repository.search_products()를 호출해야 함

# === 신고 관련 ===
# 신고 제한 상수들
MAX_TARGET_ID_LENGTH = 36         # 예: UUID 형식이면 36자
MAX_REASON_LENGTH = 500           # 신고 사유 최대 길이
DAILY_REPORT_LIMIT = 5            # 하루 최대 신고 건수
SAME_TARGET_INTERVAL = timedelta(hours=24)  # 동일 대상 신고 제한 기간 (24시간)
TARGET_REPORT_THRESHOLD = 10      # 동일 대상이 24시간 내에 신고된 건수 임계값

def file_report(reporter_id, target_id, reason):
    reporter_id = sanitize_input(reporter_id)
    target_id = sanitize_input(target_id)
    reason = sanitize_input(reason)
    
    # 입력값의 앞뒤 공백 제거
    if isinstance(target_id, str):
        target_id = target_id.strip()
    if isinstance(reason, str):
        reason = reason.strip()

    # 1. 신고 대상(target_id) 검증: 비어있거나 길이가 너무 긴 경우 차단
    if not target_id:
        return None, "신고 대상이 비어있습니다."
    if len(target_id) > MAX_TARGET_ID_LENGTH:
        return None, f"신고 대상의 길이는 최대 {MAX_TARGET_ID_LENGTH}자까지 허용됩니다."

    # 2. 신고 사유(reason) 검증: 비어있거나 길이가 너무 긴 경우 차단
    if not reason:
        return None, "신고 사유를 입력해 주세요."
    if len(reason) > MAX_REASON_LENGTH:
        return None, f"신고 사유의 길이는 최대 {MAX_REASON_LENGTH}자까지 허용됩니다."

    now = datetime.utcnow()
    since_time = (now - SAME_TARGET_INTERVAL).strftime('%Y-%m-%d %H:%M:%S')

    # 3. 동일 대상 신고 제한: 지난 24시간 동안 동일 대상을 신고한 적이 있는지 확인
    existing_reports = repository.get_reports_by_reporter_target(reporter_id, target_id, since_time)
    if existing_reports:
        return None, "이미 최근에 이 대상을 신고하셨습니다."

    # 4. 신고 건수 제한: 하루 동안 신고한 건수가 DAILY_REPORT_LIMIT 이상이면 차단
    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
    daily_count = repository.get_daily_report_count(reporter_id, start_of_day)
    if daily_count >= DAILY_REPORT_LIMIT:
        return None, "오늘 신고 가능한 횟수를 초과하였습니다. 내일 다시 시도해 주세요."

    # 5. 대상 신고 누적 제한: 동일 대상이 최근 24시간 내에 TARGET_REPORT_THRESHOLD 이상 신고되었다면 차단
    target_reports = repository.get_report_count_for_target(target_id, since_time)
    if target_reports >= TARGET_REPORT_THRESHOLD:
        return None, "해당 대상은 이미 다수 신고되어 관리자의 검토가 진행 중입니다."

    # 모든 검증 통과 시 신고 생성
    report_id = repository.create_report(reporter_id, target_id, reason)
    return report_id, None

# === 채팅 관련 서비스 ===
def save_chat_message(sender_id, recipient_id, message):
    sender_id = sanitize_input(sender_id)
    recipient_id = sanitize_input(recipient_id)
    message = sanitize_input(message)
    
    if not message:
        return None, "빈 메시지"
    if len(message) > 500:
        return None, "메시지는 500자 이내로 작성해 주세요."
    
    return repository.create_chat_message(sender_id, recipient_id, message), None

def save_global_chat_message(sender_id, message):
    sender_id = sanitize_input(sender_id)
    message = sanitize_input(message)
    
    if not message:
        return None, "빈 메시지"
    if len(message) > 500:
        return None, "메시지는 500자 이내로 작성해 주세요."
    
    """전역 채팅 메시지 저장 (recipient_id는 'global')"""
    return repository.create_global_chat_message(sender_id, message), None

def get_global_chats(limit=50):
    limit = safe_int(limit, use_abort=True)
    
    return repository.get_global_chat_history(limit)

def get_private_chats(user1, user2, limit=50):
    user1 = sanitize_input(user1)
    user2 = sanitize_input(user2)
    limit = safe_int(limit, use_abort=True)
    
    return repository.get_private_chat_history(user1, user2, limit)

# === 지갑 관련 서비스 ===
def record_wallet_transaction(sender_id, recipient_id, amount, transaction_type):
    sender_id = sanitize_input(sender_id)   # 보낸 사용자 ID를 문자열로 변환
    recipient_id = sanitize_input(recipient_id)   # 받는 사용
    amount = safe_int(amount, use_abort=True)   # 거래 금액을 정수로 변환
    transaction_type = sanitize_input(transaction_type)
    
    return repository.create_wallet_transaction(sender_id, recipient_id, amount, transaction_type)

def get_wallet_transactions(user_id, limit=50):
    user_id = f'{user_id}'   # 사용자 ID를 문자열로 변환
    limit = safe_int(limit, use_abort=True)
    
    return repository.get_wallet_transactions(user_id, limit)

def transfer_funds(sender_id, recipient_id, amount):
    sender_id = sanitize_input(sender_id)
    recipient_id = sanitize_input(recipient_id)
    amount = safe_int(amount, use_abort=True)
    
    sender = get_user(sender_id)
    if sender_id == recipient_id:
        return False, "자신에게 송금할 수 없습니다."
    if sender.wallet < amount:
        return False, "잔액이 부족합니다."
    if amount <= 0:
        return False, "송금 금액은 0보다 커야 합니다."
    
    # 잔액 업데이트
    repository.transfer_wallet(sender_id, recipient_id, amount)
    
    # 거래 내역 기록 (이체: sender와 recipient 모두 기록됨)
    record_wallet_transaction(sender_id, recipient_id, amount, "transfer")
    return True, "송금이 완료되었습니다."