from sqlalchemy.orm import Session
from .database import User, Referral, get_database_session
from datetime import datetime

class UserService:
    def __init__(self):
        self.session: Session = get_database_session()

    def register_user(self, username: str, full_name: str, user_id: int = None) -> User:
        # Check if user with this ID already exists
        if user_id:
            existing_user = self.get_user_by_id(user_id)
            if existing_user:
                return existing_user
                
        # Create new user
        new_user = User(id=user_id, username=username, full_name=full_name)
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def get_user_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> User:
        return self.session.query(User).filter(User.username == username).first()

    def update_user(self, user_id: int, username: str = None, full_name: str = None) -> User:
        user = self.get_user_by_id(user_id)
        if user:
            if username:
                user.username = username
            if full_name:
                user.full_name = full_name
            self.session.commit()
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
        return False
    
    def check_subscription(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        return user is not None

    def close_session(self):
        self.session.close()

    def create_referral(self, user_id: int, referred_by: int = None) -> Referral:
        """Create a referral record"""
        # Check if referral already exists
        existing_referral = self.session.query(Referral).filter(Referral.user_id == user_id).first()
        if existing_referral:
            return existing_referral
            
        # Create new referral with explicit transaction
        try:
            new_referral = Referral(user_id=user_id, referred_by=referred_by)
            self.session.add(new_referral)
            self.session.commit()
            return new_referral
        except Exception as e:
            self.session.rollback()
            print(f"Error creating referral: {e}")
            raise
        
    def get_referral_by_user_id(self, user_id: int) -> Referral:
        """Get referral info by user ID"""
        return self.session.query(Referral).filter(Referral.user_id == user_id).first()
        
    def get_user_referrals(self, user_id: int) -> list:
        """Get all users referred by the given user ID"""
        return self.session.query(Referral).filter(Referral.referred_by == user_id).all()
        
    def count_user_referrals(self, user_id: int) -> int:
        """Count how many users were referred by the given user ID"""
        return self.session.query(Referral).filter(Referral.referred_by == user_id).count()