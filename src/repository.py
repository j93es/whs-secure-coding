# repository.py
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, func, or_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# 데이터베이스 URL (SQLite 사용)
DATABASE_URL = 'sqlite:///market.db'

# SQLAlchemy 엔진 생성 (SQLite의 경우 여러 스레드 사용을 위해 check_same_thread=False 설정)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# 세션 팩토리 및 scoped_session 생성
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# 기본 모델 클래스
Base = declarative_base()

# --------------------- 모델 정의 ---------------------

class User(Base):
    __tablename__ = 'user'
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    bio = Column(Text)
    status = Column(String, default='active')
    wallet = Column(Integer, default=5000)
    failed_attempts = Column(Integer, default=0)
    lockout_until = Column(DateTime, nullable=True)

class Product(Base):
    __tablename__ = 'product'
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(String, nullable=False)
    seller_id = Column(String, nullable=False)

class Report(Base):
    __tablename__ = 'report'
    id = Column(String, primary_key=True, index=True)
    reporter_id = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.current_timestamp())

class Chat(Base):
    __tablename__ = 'chat'
    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, nullable=False)
    recipient_id = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, server_default=func.current_timestamp())

class WalletTransaction(Base):
    __tablename__ = 'wallet_transaction'
    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String, nullable=True)
    recipient_id = Column(String, nullable=True)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)
    timestamp = Column(DateTime, server_default=func.current_timestamp())

# --------------------- 데이터베이스 초기화 함수 ---------------------

def init_db():
    """모든 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)
    
def close_db(e=None):
    SessionLocal.remove()

# --------------------- 사용자 관련 함수 ---------------------

def create_user(username, password):
    """
    새 사용자를 생성합니다.
    wallet은 기본적으로 5000으로 설정됩니다.
    """
    session = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        new_user = User(id=user_id, username=username, password=password)
        session.add(new_user)
        session.commit()
        return user_id
    finally:
        session.close()

def get_user_by_username(username):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()

def get_user_by_id(user_id):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.id == user_id).first()
    finally:
        session.close()

def get_all_users():
    session = SessionLocal()
    try:
        return session.query(User).all()
    finally:
        session.close()

def update_failed_attempts(user_id, count):
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"failed_attempts": count})
        session.commit()
    finally:
        session.close()

def set_lockout(user_id, lockout_until):
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"lockout_until": lockout_until})
        session.commit()
    finally:
        session.close()

def reset_failed_attempts(user_id):
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"failed_attempts": 0, "lockout_until": None})
        session.commit()
    finally:
        session.close()

def update_user_bio(user_id, bio):
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"bio": bio})
        session.commit()
    finally:
        session.close()

def update_user_status(user_id, status):
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"status": status})
        session.commit()
    finally:
        session.close()

def update_user_password(user_id, new_password):
    """
    지정된 사용자에 대해 새 비밀번호를 업데이트합니다.
    """
    session = SessionLocal()
    try:
        session.query(User).filter(User.id == user_id).update({"password": new_password})
        session.commit()
    finally:
        session.close()

# --------------------- 상품 관련 함수 ---------------------

def create_product(title, description, price, seller_id):
    session = SessionLocal()
    try:
        product_id = str(uuid.uuid4())
        new_product = Product(id=product_id, title=title, description=description, price=price, seller_id=seller_id)
        session.add(new_product)
        session.commit()
        return product_id
    finally:
        session.close()

def get_all_products():
    session = SessionLocal()
    try:
        return session.query(Product).all()
    finally:
        session.close()

def get_product_by_id(product_id):
    session = SessionLocal()
    try:
        return session.query(Product).filter(Product.id == product_id).first()
    finally:
        session.close()

def edit_product(product_id, title, description, price):
    session = SessionLocal()
    try:
        session.query(Product).filter(Product.id == product_id).update({
            "title": title,
            "description": description,
            "price": price
        })
        session.commit()
    finally:
        session.close()

def delete_product(product_id):
    session = SessionLocal()
    try:
        session.query(Product).filter(Product.id == product_id).delete()
        session.commit()
    finally:
        session.close()

def search_products(query):
    session = SessionLocal()
    try:
        pattern = f"%{query}%"
        return session.query(Product).filter(Product.title.like(pattern)).all()
    finally:
        session.close()

# --------------------- 신고 관련 함수 ---------------------

def create_report(reporter_id, target_id, reason):
    session = SessionLocal()
    try:
        report_id = str(uuid.uuid4())
        new_report = Report(id=report_id, reporter_id=reporter_id, target_id=target_id, reason=reason)
        session.add(new_report)
        session.commit()
        return report_id
    finally:
        session.close()

def get_all_reports():
    session = SessionLocal()
    try:
        return session.query(Report).all()
    finally:
        session.close()

def get_reports_by_reporter_target(reporter_id, target_id, since):
    session = SessionLocal()
    try:
        return session.query(Report).filter(
            Report.reporter_id == reporter_id,
            Report.target_id == target_id,
            Report.timestamp >= since
        ).all()
    finally:
        session.close()

def get_daily_report_count(reporter_id, since):
    session = SessionLocal()
    try:
        count = session.query(func.count(Report.id)).filter(
            Report.reporter_id == reporter_id,
            Report.timestamp >= since
        ).scalar()
        return count or 0
    finally:
        session.close()

def get_report_count_for_target(target_id, since):
    session = SessionLocal()
    try:
        count = session.query(func.count(Report.id)).filter(
            Report.target_id == target_id,
            Report.timestamp >= since
        ).scalar()
        return count or 0
    finally:
        session.close()

# --------------------- 채팅 관련 함수 ---------------------

def create_chat_message(sender_id, recipient_id, message):
    session = SessionLocal()
    try:
        chat_id = str(uuid.uuid4())
        new_chat = Chat(id=chat_id, sender_id=sender_id, recipient_id=recipient_id, message=message)
        session.add(new_chat)
        session.commit()
        return message
    finally:
        session.close()

def get_private_chat_history(user1, user2, limit=50):
    session = SessionLocal()
    try:
        chats = session.query(Chat).filter(
            or_(
                and_(Chat.sender_id == user1, Chat.recipient_id == user2),
                and_(Chat.sender_id == user2, Chat.recipient_id == user1)
            )
        ).order_by(Chat.timestamp.asc()).limit(limit).all()
        return chats
    finally:
        session.close()

def create_global_chat_message(sender_id, message):
    # 전역 채팅의 경우 recipient_id에 "global"을 사용
    return create_chat_message(sender_id, "global", message)

def get_global_chat_history(limit=50):
    session = SessionLocal()
    try:
        chats = session.query(Chat).filter(Chat.recipient_id == 'global')\
            .order_by(Chat.timestamp.asc()).limit(limit).all()
        return chats
    finally:
        session.close()

def delete_chat_message(chat_id):
    session = SessionLocal()
    try:
        session.query(Chat).filter(Chat.id == chat_id).delete()
        session.commit()
    finally:
        session.close()

# --------------------- 지갑 관련 함수 ---------------------

def create_wallet_transaction(sender_id, recipient_id, amount, transaction_type):
    session = SessionLocal()
    try:
        txn_id = str(uuid.uuid4())
        txn = WalletTransaction(
            id=txn_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            amount=amount,
            transaction_type=transaction_type
        )
        session.add(txn)
        session.commit()
        return txn_id
    finally:
        session.close()

def get_wallet_transactions(user_id, limit=50):
    session = SessionLocal()
    try:
        transactions = session.query(WalletTransaction)\
            .filter(or_(WalletTransaction.sender_id == user_id, WalletTransaction.recipient_id == user_id))\
            .order_by(WalletTransaction.timestamp.desc()).limit(limit).all()
        return transactions
    finally:
        session.close()

def transfer_wallet(sender_id, recipient_id, amount):
    session = SessionLocal()
    try:
        sender = session.query(User).filter(User.id == sender_id).first()
        recipient = session.query(User).filter(User.id == recipient_id).first()
        if sender is None or recipient is None:
            raise Exception("사용자 정보가 없습니다.")
        sender.wallet -= amount
        recipient.wallet += amount
        session.commit()
    finally:
        session.close()

  