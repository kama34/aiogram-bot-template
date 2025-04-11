from sqlalchemy import create_engine, Column, Integer, String, Sequence, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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

def get_database_session():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()