from datetime import datetime, timezone
from . import db
from .enums import TransactionType

class Transactions(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_keyx=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Numeric(precision=18, scale=8), nullable=False)
    tx_hash = db.Column(db.String(66), unique=True, nullable=True)
    model = db.Column(db.String(50), nullable=True)
    tokens_input = db.Column(db.Integer, nullable=True)
    tokens_output = db.Column(db.Integer, nullable=True)
    request_id = db.Column(db.String(36), unique=True, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    endpoint = db.Column(db.String(100), nullable=True)
    error = db.Column(db.Text, nullable=True)
    transaction_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = db.relationship('Users', backref=db.backref('transactions', lazy=True))
    
    def __init__(self, **kwargs):
        if kwargs.get('type') in [TransactionType.API_USAGE, TransactionType.WITHDRAWAL]:
            kwargs['amount'] = -abs(kwargs['amount'])
        super().__init__(**kwargs)