from datetime import datetime, timezone
from decimal import Decimal
import uuid

from models import TransactionType, Transactions, ModelType
from models import db
from typing import Optional, List, Dict, Union
from models.llm_data import ChatModel, ImageModel, Provider, ModelParameters
from config import Config
from .llm_models import llm_config

class LLMModelsManager:
    def __init__(self, llm_data: dict):
        self.models: Dict[str, Union[ChatModel, ImageModel]] = {}
        self.load_models(llm_data)
        
    def load_models(self, data: dict) -> None:
        for model_data in data['chat_models'].values():
            model = ChatModel(**model_data)
            self.add_model(model)
            
        for model_data in data['image_models'].values():
            model = ImageModel(**model_data)
            self.add_model(model)

    def add_model(self, model: Union[ChatModel, ImageModel]) -> None:
        self.models[model.version] = model
        
    def get_model(self, version: str) -> Optional[Union[ChatModel, ImageModel]]:
        return self.models.get(version)
        
    def get_chat_model_price(self, model: ChatModel, input_tokens: int, 
                            output_tokens: Optional[int] = None, in_cents: bool = True) -> float:
        price = model.input_price * input_tokens
        if output_tokens is not None:
            price += output_tokens * model.output_price
        else:
            price += model.max_context_tokens * model.output_price
            
        if in_cents:
            price *= 100
        return price / 1000

    def get_prompt_price(self, model_version: str, input_tokens: int, 
                        output_tokens: Optional[int] = None) -> Dict[str, float]:
        model = self.get_model(model_version)
        if not isinstance(model, ChatModel):
            raise ValueError(f"Model {model_version} is not a chat model")
            
        price = self.get_chat_model_price(model, input_tokens, output_tokens)
        price *= Config.PRICE_ADJUSTMENT
        
        return {
            "price": price,
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens or 0
        }

    def estimate_request_cost(self, endpoint: str, request_data: dict) -> float:
        print('fco:::::::: request_data', request_data, endpoint)
        return 0.9
        model_version = request_data.get('model')
        if not model_version:
            raise ValueError("Model version not provided in request")
            
        # Estimate tokens based on input text
        input_text = request_data.get('prompt', '')
        estimated_input_tokens = len(input_text.split()) # Simple estimation
        estimated_output_tokens = None  # Can be refined based on your needs
        
        price_info = self.get_prompt_price(
            model_version, 
            estimated_input_tokens,
            estimated_output_tokens
        )
        
        return price_info["price"]
    
    def record_transaction(self, user_id: int, model_version: str, 
                         input_tokens: int, output_tokens: int,
                         endpoint: str, status: str = 'success',
                         error: str = None) -> Transactions:
        """Record a transaction for API usage"""
        model = self.get_model(model_version)
        if not model:
            raise ValueError(f"Invalid model version: {model_version}")

        # Calculate cost
        price_info = self.get_prompt_price(model_version, input_tokens, output_tokens)
        amount = Decimal(str(price_info['price']))

        # Map provider to ModelType
        model_type_mapping = {
            'openai': ModelType.GPT4 if 'gpt-4' in model_version else ModelType.GPT35,
            'claude': ModelType.CLAUDE,
            'vertex': ModelType.GEMINI
        }
        model_type = model_type_mapping.get(model.provider, ModelType.GPT35)

        transaction = Transactions(
            user_id=user_id,
            type=TransactionType.API_USAGE,
            amount=-amount,  # Negative amount for usage
            model_type=model_type,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            request_id=str(uuid.uuid4()),
            status=status,
            endpoint=endpoint,
            error=error,
            transaction_metadata={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'model_type': model_type.value,
                'model_version': model_version,
                'endpoint': endpoint,
                'estimated_cost': str(amount)
            }
        )
        
        try:
            db.session.add(transaction)
            db.session.commit()
            return transaction
        except Exception as e:
            db.session.rollback()
            raise e

llm_models_manager = LLMModelsManager(llm_data=llm_config)
