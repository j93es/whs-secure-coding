# app.py
from dotenv import load_dotenv
load_dotenv()
import os
from flask import Flask
import time
from flask_socketio import join_room, emit, SocketIO
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
import repository as repository
import user_service as service
from admin_routes import admin_bp
from user_routes import user_bp, login_required, limiter, get_user_id
from error_handlers import register_error_handlers
from header_setter import register_headers


app = Flask(__name__)
app.config["ENV"] = os.environ.get('ENV')
app.config['ADMIN_JWT_SECRET_KEY'] = os.environ.get('ADMIN_JWT_SECRET_KEY')
app.config['CLIENT_JWT_SECRET_KEY'] = os.environ.get('CLIENT_JWT_SECRET_KEY')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['ADMIN_ID'] = os.environ.get('ADMIN_ID')
app.config['ADMIN_PW'] = os.environ.get('ADMIN_PW')
csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# Blueprints 등록
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@app.teardown_appcontext
def close_connection(exception):
    repository.close_db(exception)



# SocketIO 설정
socketio = SocketIO(app)

socketio_rate_limits = {}

def socketio_rate_limit(key_func, limit=20, window=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            key = key_func()
            now = time.time()
            log = socketio_rate_limits.get(key, [])
            log = [ts for ts in log if ts > now - window]  # 윈도우 내 요청만 유지
            if len(log) >= limit:
                emit("error", {"message": "Too many messages, please slow down."})
                return
            log.append(now)
            socketio_rate_limits[key] = log
            return f(*args, **kwargs)
        return wrapper
    return decorator

@socketio.on('join')
@login_required
@socketio_rate_limit(lambda: get_user_id(), limit=5, window=60)
def handle_join(data):
    user_id = data.get('user_id')
    if user_id:
        join_room(user_id)
        print(f"User {user_id} joined their personal room.")

@socketio.on('send_message')
@login_required
@socketio_rate_limit(lambda: get_user_id(), limit=20, window=60)
def handle_send_message(data):
    """
    전역 채팅 메시지 처리:
      - DB 저장 (recipient_id: 'global')
      - 모든 클라이언트에 broadcast (username 포함)
    """
    sender_id = data.get('sender_id')
    message = data.get('message')
    if sender_id and message:
        message, error = service.save_global_chat_message(sender_id, message)
        sender = service.get_user(sender_id)
        username = sender.username if sender else sender_id
        if error:
            emit('message', {'username': username, 'message': error}, broadcast=True)
            return
        emit('message', {'username': username, 'message': message}, broadcast=True)

@socketio.on('private_message')
@login_required
@socketio_rate_limit(lambda: get_user_id(), limit=20, window=60)
def handle_private_message(data):
    """
    1:1 채팅 메시지 처리:
      - DB 저장
      - 송신자와 수신자 room에 메시지 전송 (username 포함)
    """
    sender_id = data.get('sender_id')
    recipient_id = data.get('recipient_id')
    message = data.get('message')
    if recipient_id and message:
        message, error = service.save_chat_message(sender_id, recipient_id, message)
        sender = service.get_user(sender_id)
        username = sender.username if sender else sender_id
        if error:
            emit('private_message', {'username': username, 'message': error}, room=recipient_id)
            emit('private_message', {'username': username, 'message': error}, room=sender_id)
            return
        emit('private_message', {'username': username, 'message': message}, room=recipient_id)
        emit('private_message', {'username': username, 'message': message}, room=sender_id)

if __name__ == '__main__':
    limiter.init_app(app)
    register_error_handlers(app)
    register_headers(app)
    with app.app_context():
        repository.init_db()
    socketio.run(app, debug=True)

