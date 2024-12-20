from dataclasses import dataclass
from typing import Dict, List, Optional, TypedDict, Literal
from enum import Enum

class Provider(str, Enum):
    VERTEX = "vertex"
    CLAUDE = "claude" 
    OPENAI = "openai"
    XAI = "xai"
    LUMA = "luma"

class ChargeType(str, Enum):
    TOKEN = "TOKEN"
    CHAR = "CHAR"

@dataclass
class ModelParameters:
    temperature: float
    max_tokens: int

@dataclass
class BaseModel:
    provider: Provider
    name: str
    full_name: str
    bot_name: str
    version: str
    commands: List[str]
    prefix: Optional[List[str]]
    api_spec: str

@dataclass
class ChatModel(BaseModel):
    input_price: float
    output_price: float
    max_context_tokens: int
    charge_type: ChargeType
    stream: bool

@dataclass
class ImageModel(BaseModel):
    price: Dict[str, float]

class ProviderParameters(TypedDict):
    default_parameters: ModelParameters
    model_overrides: Optional[Dict[str, ModelParameters]]


__all__ = [
    'Provider',
    'ChargeType',
    'ModelParameters',
    'BaseModel',
    'ChatModel',
    'ImageModel',
    'ProviderParameters'
]