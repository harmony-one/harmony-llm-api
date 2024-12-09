from datetime import datetime, timezone
from sqlalchemy import func

from .enums import TransactionType, UserType
from .transactions import Transaction

from . import db
    
class SignInRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False)
    nonce = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, default=UserType.WALLET)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    @staticmethod
    def generate_username(address: str) -> str:
        # Similar to the TypeScript implementation
        return address.replace('0x', '')[:6]
    
    def get_balance(self):
        """Calculate current balance from transactions"""
        result = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.id
        ).scalar() or 0
        
        return result

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jti = db.Column(db.String(36), unique=True, nullable=False)  # JWT ID
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))

    def get_usage_stats(self):
        """Helper method to get API usage statistics"""
        if self.type != TransactionType.API_USAGE:
            return None
            
        return {
            'model': self.model_type,
            'tokens_input': self.tokens_input,
            'tokens_output': self.tokens_output,
            'cost': self.amount,
            'endpoint': self.endpoint,
            'status': self.status
        }