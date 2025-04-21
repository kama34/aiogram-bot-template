from sqlalchemy import create_engine, Column, Integer, String, Sequence, Boolean, DateTime, BigInteger, func, UniqueConstraint, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./database.db"  # Update with your database URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    is_blocked = Column(Boolean, default=False)
    is_exception = Column(Boolean, default=False)  # New field for user exceptions
    created_at = Column(DateTime, default=datetime.now)

class Referral(Base):
    __tablename__ = 'referrals'
    id = Column(Integer, Sequence('referral_id_seq'), primary_key=True)
    user_id = Column(Integer, nullable=False)
    referred_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, Sequence('channel_id_seq'), primary_key=True)
    channel_name = Column(String(100), nullable=False)
    channel_id = Column(String(100), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True)  # New field to control if subscription is required
    added_at = Column(DateTime, default=datetime.now)

class CartItem(Base):
    __tablename__ = 'cart_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_user_product'),
    )

class ProductInventory(Base):
    __tablename__ = 'product_inventory'
    
    product_id = Column(String, primary_key=True)
    stock = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    total_amount = Column(Float, nullable=False)
    payment_id = Column(String, nullable=True)
    shipping_address = Column(String, nullable=True)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношение к пользователю
    user = relationship('User', backref='orders')
    # Отношение к товарам
    items = relationship('OrderItem', backref='order', cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

def get_database_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

# Добавляем класс SessionManager для работы с контекстным менеджером
class SessionManager:
    def __init__(self):
        self.session = get_database_session()
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()