from datetime import datetime, timezone
from sqlalchemy import func

from .enums import UserType
from .transactions import Transactions

from . import db
    
class SignInRequests(db.Model):
    __tablename__ = 'sign_in_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False)
    nonce = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
class Users(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, default=UserType.WALLET)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @staticmethod
    def generate_username(address: str) -> str:
        return address.replace('0x', '')[:6]
    
    def get_balance(self):
        """Calculate current balance from transactions"""
        result = db.session.query(func.sum(Transactions.amount)).filter(
            Transactions.user_id == self.id
        ).scalar() or 0
        
        return result

class Tokens(db.Model):
    __tablename__ = 'tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    jti = db.Column(db.String(36), unique=True, nullable=False)  # JWT ID
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('Users', backref=db.backref('tokens', lazy=True))