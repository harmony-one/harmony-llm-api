from datetime import datetime, timezone
from enum import Enum
from . import db
from .enums import ModelType, TransactionType

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.Enum(TransactionType), nullable=False)
    amount = db.Column(db.Numeric(precision=18, scale=8), nullable=False)
    tx_hash = db.Column(db.String(66), unique=True, nullable=True)  # For blockchain transactions
    
    # Fields for API usage transactions
    model_type = db.Column(db.Enum(ModelType), nullable=True)  # Only for API_USAGE
    tokens_input = db.Column(db.Integer, nullable=True)        # Only for API_USAGE
    tokens_output = db.Column(db.Integer, nullable=True)       # Only for API_USAGE
    request_id = db.Column(db.String(36), unique=True, nullable=True)  # For API request tracking
    status = db.Column(db.String(20), nullable=True)          # For API call status
    endpoint = db.Column(db.String(100), nullable=True)       # API endpoint used
    error = db.Column(db.Text, nullable=True)                 # For failed API calls

    # Additional metadata as JSON for flexibility
    transaction_metadata = db.Column(db.JSON)  

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        # Ensure amount is negative for usage and withdrawals
        if kwargs.get('type') in [TransactionType.API_USAGE, TransactionType.WITHDRAWAL]:
            kwargs['amount'] = -abs(kwargs['amount'])
        super().__init__(**kwargs)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))