# service.py
import repository
from utils import sanitize_input, safe_int

# === 사용자 관련 서비스 ===

def get_user(user_id):
    user_id = sanitize_input(user_id)
    
    return repository.get_user_by_id(user_id)

def get_user_list():
    return repository.get_all_users()

def suspend_user(user_id):
    user_id = sanitize_input(user_id)
    
    repository.update_user_status(user_id, '휴먼')

def restore_user(user_id):
    user_id = sanitize_input(user_id)
    
    repository.update_user_status(user_id, 'active')

# === 상품 관련 서비스 ===

def list_products():
    return repository.get_all_products()

def get_product(product_id):
    product_id = sanitize_input(product_id)
    
    return repository.get_product_by_id(product_id)

def remove_product(product_id):
    product_id = sanitize_input(product_id)
    
    repository.delete_product(product_id)

# === 신고 관련 서비스 ===

def list_reports():
    return repository.get_all_reports()

# === 채팅 관련 서비스 ===

def get_global_chats(limit=50):
    limit = safe_int(limit, use_abort=True)
    
    return repository.get_global_chat_history(limit)

def remove_chat_message(chat_id):
    chat_id = f'{chat_id}' # chat_id를 문자열로 변환
    
    repository.delete_chat_message(chat_id)

# === 지갑 관련 서비스 ===