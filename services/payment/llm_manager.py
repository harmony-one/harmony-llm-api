import uuid

from datetime import datetime, timezone
from decimal import Decimal
from flask import current_app as app
from models import TransactionType, Transactions
from models import db
from typing import Optional, List, Dict, Union
from models.llm_data import ChatModel, ImageModel, Provider, ModelParameters
from config import config
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

    def get_chat_model_price(self, model: ChatModel, input_tokens: int, 
                        output_tokens: Optional[int] = None, 
                        in_cents: bool = True,
                        apply_adjustment: bool = True) -> Decimal:
        """
        Calculate price for chat model usage.
        For TOKEN models: price per 1K tokens
        For CHAR models: price per 1K characters
        Returns: Decimal value in cents if in_cents=True, otherwise in dollars
        """
        input_price = model.input_price * (Decimal(str(input_tokens)) / Decimal('1000'))
        
        if output_tokens is not None:
            output_price = model.output_price * (Decimal(str(output_tokens)) / Decimal('1000'))
        else:
            estimated_output = min(input_tokens * 2, model.max_context_tokens)
            output_price = model.output_price * (Decimal(str(estimated_output)) / Decimal('1000'))
            
        total_price = input_price + output_price
        
        if in_cents:
            total_price *= Decimal('100')
            
        if apply_adjustment:
            total_price *= Decimal(str(config.PRICE_ADJUSTMENT))
            
        return total_price
    
    def get_models_by_provider(self, provider: str) -> List[Union[ChatModel, ImageModel]]:
        """Get all models (chat and image) for a specific provider"""
        return [model for model in self.models.values() if model.provider == provider]

    def get_model_by_name(self, name: str) -> Optional[Union[ChatModel, ImageModel]]:
        """Get a model by its name (not version)"""
        return next(
            (model for model in self.models.values() if model.name == name),
            None
        )

    def get_default_image_model(self, provider: str = "openai") -> Optional[ImageModel]:
        """Get the default image model for a provider"""
        image_models = [
            model for model in self.models.values()
            if isinstance(model, ImageModel) and model.provider == provider
        ]
        return image_models[0] if image_models else None

    def estimate_request_cost(self, endpoint: str, request_data: dict) -> Decimal:
        """
        Estimate request cost based on input size and model type.
        Returns: Decimal value in cents
        """
        app.logger.debug(f'Estimating cost for endpoint: {endpoint} with data: {request_data}')
        
        model_version = request_data.get('model')
        if not model_version:
            raise ValueError("Model version not specified in request data")

        model = self.get_model(model_version)
        if not model:
            raise ValueError(f"Invalid model version: {model_version}")

        if isinstance(model, ImageModel):
            return self._estimate_image_cost(model, request_data)

        messages = request_data.get('messages', [])
        total_input_size = sum(
            len(str(msg.get('content', '') or msg.get('parts', {}).get('text', ''))) 
            for msg in messages
        )
        
        if model.charge_type == "CHAR":
            input_size = total_input_size
            output_size = min(total_input_size * 2, model.max_context_tokens)
            
        elif model.charge_type == "TOKEN":
            # Estimate tokens from characters (roughly 4 chars per token)
            input_size = total_input_size // 4
            output_size = min(input_size * 2, model.max_context_tokens)
            
        else:
            raise ValueError(f"Unknown charge type: {model.charge_type}")

        price = self.get_chat_model_price(
            model,
            input_size,
            output_size,
            in_cents=True
        )
        
        app.logger.debug(
            f'Cost estimate details:\n'
            f'Model: {model_version}\n'
            f'Charge type: {model.charge_type}\n'
            f'Input size: {input_size} {model.charge_type.lower()}s\n'
            f'Estimated output size: {output_size} {model.charge_type.lower()}s\n'
            f'Total estimated cost (cents): {price}'
        )
        
        return price

    # CHANGED: Added new method for image cost estimation
    def _estimate_image_cost(self, model: ImageModel, request_data: dict) -> Decimal:
        """Returns cost in cents as Decimal"""
        size = request_data.get('size', '1024x1024')
        n = request_data.get('n', 1)  

        if size not in ['1024x1024', '1024x1792', '1792x1024']:
            raise ValueError(f"Invalid size parameter: {size}")

        size_price_map = {
            '1024x1024': 'size_1024_1024',
            '1024x1792': 'size_1024_1792',
            '1792x1024': 'size_1792_1024'
        }
        
        price_key = size_price_map[size]
        if price_key not in model.price:
            raise ValueError(f"Price not configured for size: {size}")
        
        return model.price[price_key] * Decimal('100') * Decimal(str(n))
 
    
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

        transaction = Transactions(
            user_id=user_id,
            type=TransactionType.API_USAGE,
            amount=-amount,  # Negative amount for usage
            model=model_version,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            request_id=str(uuid.uuid4()),
            status=status,
            endpoint=endpoint,
            error=error,
            transaction_metadata={
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'model': model_version,
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


       
        # if not model_version:
        #     raise ValueError("Model version not provided in request")
            
        # # Estimate tokens based on input text
        # input_text = request_data.get('prompt', '')
        # estimated_input_tokens = len(input_text.split()) # Simple estimation
        # estimated_output_tokens = None  # Can be refined based on your needs
        
        # price_info = self.get_prompt_price(
        #     model_version, 
        #     estimated_input_tokens,
        #     estimated_output_tokens
        # )
        
        # return price_info["price"]