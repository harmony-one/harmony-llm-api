from enum import Enum

class UserType(Enum):
    WALLET = 'wallet'    # Prepaid users who need to deposit ONE tokens
    API_KEY = 'api_key'  # Free tier with API key access

class TransactionType(Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    API_USAGE = 'api_usage'
    REFUND = 'refund'

class ModelType(Enum):
    GPT_4 = 'gpt-4'
    GPT_35 = 'gpt-3.5-turbo'
    CLAUDE = 'claude'
    GEMINI = 'gemini'