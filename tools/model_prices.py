# config/model_prices.py
from decimal import Decimal
from models.enums import ModelType

MODEL_PRICES = {
    ModelType.GPT_4: {
        'input_price': Decimal('0.03'),  # Price per 1K input tokens
        'output_price': Decimal('0.06'),  # Price per 1K output tokens
        'min_price': Decimal('0.01')     # Minimum charge per request
    },
    ModelType.GPT_35: {
        'input_price': Decimal('0.0015'),
        'output_price': Decimal('0.002'),
        'min_price': Decimal('0.001')
    },
    ModelType.CLAUDE: {
        'input_price': Decimal('0.008'),
        'output_price': Decimal('0.024'),
        'min_price': Decimal('0.01')
    },
    ModelType.GEMINI: {
        'input_price': Decimal('0.001'),
        'output_price': Decimal('0.002'),
        'min_price': Decimal('0.001')
    }
}

def calculate_cost(model_type: ModelType, input_tokens: int, output_tokens: int) -> Decimal:
    """
    Calculate the cost of an API call based on token usage.
    
    Args:
        model_type: The LLM model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Decimal: Total cost in ONE tokens
    """
    if model_type not in MODEL_PRICES:
        raise ValueError(f"Unknown model type: {model_type}")
        
    prices = MODEL_PRICES[model_type]
    
    # Calculate costs per token type
    input_cost = (Decimal(input_tokens) / 1000) * prices['input_price']
    output_cost = (Decimal(output_tokens) / 1000) * prices['output_price']
    
    # Total cost
    total_cost = input_cost + output_cost
    
    # Apply minimum charge if total is below minimum
    return max(total_cost, prices['min_price'])

# from config.model_prices import calculate_cost, MODEL_PRICES
# from models.enums import ModelType

# When processing an API call:
# def process_api_call(user_id: int, model_type: ModelType, input_tokens: int, output_tokens: int):
#     # Calculate cost
#     cost = calculate_cost(model_type, input_tokens, output_tokens)
    
#     # Check user balance
#     user = User.query.get(user_id)
#     if user.get_balance() < cost:
#         raise InsufficientFundsError()
    
#     # Create transaction for API usage
#     transaction = Transaction(
#         user_id=user_id,
#         type=TransactionType.API_USAGE,
#         amount=cost,
#         metadata={
#             'model': model_type.value,
#             'input_tokens': input_tokens,
#             'output_tokens': output_tokens
#         }
#     )
#     db.session.add(transaction)
#     db.session.commit()