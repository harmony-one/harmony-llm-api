from enum import Enum

class UserType(Enum):
    WALLET = 'wallet'    # Prepaid users who need to deposit ONE tokens
    API_KEY = 'api_key'  # Free tier with API key access

class TransactionType(Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    API_USAGE = 'api_usage'
    REFUND = 'refund'
