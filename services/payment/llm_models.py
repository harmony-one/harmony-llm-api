# config.py
from decimal import Decimal
from typing import Literal, Optional, TypedDict, Dict, List, Union
from dataclasses import dataclass

class ModelPrice(TypedDict):
    size_1024_1024: Decimal
    size_1024_1792: Decimal
    size_1792_1024: Decimal

class ChatModelConfig(TypedDict):
    provider: str
    name: str
    full_name: str
    bot_name: str
    version: str
    commands: List[str]
    prefix: Optional[List[str]]
    api_spec: str
    input_price: Decimal
    output_price: Decimal
    max_context_tokens: int
    charge_type: Literal["TOKEN", "CHAR"]
    stream: bool

class ImageModelConfig(TypedDict):
    provider: str
    name: str
    full_name: str
    bot_name: str
    version: str
    commands: List[str]
    prefix: Optional[List[str]]
    api_spec: str
    price: ModelPrice

class ProviderConfig(TypedDict):
    default_parameters: Dict
    model_overrides: Optional[Dict[str, Dict]]

class LLMConfig(TypedDict):
    chat_models: Dict[str, ChatModelConfig]
    image_models: Dict[str, ImageModelConfig]
    provider_parameters: Dict[str, ProviderConfig]

# Dictionary containing all model configurations
llm_config: LLMConfig = {
    "chat_models": {
        "gemini-15": {
            "provider": "vertex",
            "name": "gemini-15",
            "full_name": "gemini-1.5-pro-latest",
            "bot_name": "VertexBot",
            "version": "gemini-1.5-pro-latest",
            "commands": ["gemini15", "g"],
            "prefix": ["g. "],
            "api_spec": "https://deepmind.google/technologies/gemini/pro/",
            "input_price": Decimal("0.0025"),
            "output_price": Decimal("0.0075"),
            "max_context_tokens": 1048576,
            "charge_type": "CHAR",
            "stream": True
        },
        "gemini-10": {
            "provider": "vertex",
            "name": "gemini-10",
            "full_name": "gemini-1.0-pro",
            "bot_name": "VertexBot",
            "version": "gemini-1.0-pro",
            "commands": ["gemini", "g10"],
            "prefix": ["g10. "],
            "api_spec": "https://deepmind.google/technologies/gemini/pro/",
            "input_price": Decimal("0.000125"),
            "output_price": Decimal("0.000375"),
            "max_context_tokens": 30720,
            "charge_type": "CHAR",
            "stream": True
        },
        "claude-35-sonnet": {
            "provider": "claude",
            "name": "claude-35-sonnet",
            "full_name": "Claude Sonnet 3.5",
            "bot_name": "ClaudeBot",
            "version": "claude-3-5-sonnet-20241022",
            "commands": ["sonnet", "claude", "s", "stool", "c", "ctool", "c0"],
            "prefix": ["s. ", "c. ", "c0. "],
            "api_spec": "https://www.anthropic.com/news/claude-3-5-sonnet",
            "input_price": Decimal("0.003"),
            "output_price": Decimal("0.015"),
            "max_context_tokens": 8192,
            "charge_type": "TOKEN",
            "stream": True
        },
        "claude-3-opus": {
            "provider": "claude",
            "name": "claude-3-opus",
            "full_name": "Claude Opus",
            "bot_name": "ClaudeBot",
            "version": "claude-3-opus-20240229",
            "commands": ["opus", "o", "otool"],
            "prefix": ["o. "],
            "api_spec": "https://www.anthropic.com/news/claude-3-family",
            "input_price": Decimal("0.015"),
            "output_price": Decimal("0.075"),
            "max_context_tokens": 4096,
            "charge_type": "TOKEN",
            "stream": True
        },
        "claude-3-5-haiku": {
            "provider": "claude",
            "name": "claude-3-5-haiku",
            "full_name": "Claude Haiku",
            "bot_name": "ClaudeBot",
            "version": "claude-3-5-haiku-20241022",
            "commands": ["haiku", "h"],
            "prefix": ["h. "],
            "api_spec": "https://www.anthropic.com/news/claude-3-family",
            "input_price": Decimal("0.001"),
            "output_price": Decimal("0.005"),
            "max_context_tokens": 8192,
            "charge_type": "TOKEN",
            "stream": True
        },
        "gpt-4o": {
            "provider": "openai",
            "name": "gpt-4o",
            "full_name": "GPT-4o",
            "bot_name": "OpenAIBot",
            "version": "gpt-4o",
            "commands": ["gpto", "ask", "chat", "gpt", "a"],
            "prefix": ["a. ", ". "],
            "api_spec": "https://platform.openai.com/docs/models/gpt-4o",
            "input_price": Decimal("0.005"),
            "output_price": Decimal("0.0015"),
            "max_context_tokens": 128000,
            "charge_type": "TOKEN",
            "stream": True
        },
        "gpt-4": {
            "provider": "openai",
            "name": "gpt-4",
            "full_name": "GPT-4",
            "bot_name": "OpenAIBot",
            "version": "gpt-4",
            "commands": ["gpt4"],
            "prefix": None,
            "api_spec": "https://openai.com/index/gpt-4/",
            "input_price": Decimal("0.03"),
            "output_price": Decimal("0.06"),
            "max_context_tokens": 8192,
            "charge_type": "TOKEN",
            "stream": True
        },
        "gpt-35-turbo": {
            "provider": "openai",
            "name": "gpt-35-turbo",
            "full_name": "GPT-3.5 Turbo",
            "bot_name": "OpenAIBot",
            "version": "gpt-3.5-turbo",
            "commands": ["ask35"],
            "prefix": None,
            "api_spec": "https://platform.openai.com/docs/models/gpt-3-5-turbo",
            "input_price": Decimal("0.0015"),
            "output_price": Decimal("0.002"),
            "max_context_tokens": 4000,
            "charge_type": "TOKEN",
            "stream": True
        },
        "gpt-4-vision": {
            "provider": "openai",
            "name": "gpt-4-vision",
            "full_name": "GPT-4 Vision",
            "bot_name": "OpenAIBot",
            "version": "gpt-4-vision-preview",
            "commands": ["vision", "v"],
            "prefix": ["v. "],
            "api_spec": "https://platform.openai.com/docs/guides/vision",
            "input_price": Decimal("0.03"),
            "output_price": Decimal("0.06"),
            "max_context_tokens": 16000,
            "charge_type": "TOKEN",
            "stream": True
        },
        "o1": {
            "provider": "openai",
            "name": "o1",
            "full_name": "O1 Preview",
            "bot_name": "OpenAIBot",
            "version": "o1-preview",
            "commands": ["o1", "ask1"],
            "prefix": ["o1. "],
            "api_spec": "https://platform.openai.com/docs/models/o1",
            "input_price": Decimal("0.015"),
            "output_price": Decimal("0.06"),
            "max_context_tokens": 128000,
            "charge_type": "TOKEN",
            "stream": False
        },
        "o1-mini": {
            "provider": "openai",
            "name": "o1-mini",
            "full_name": "O1 Mini",
            "bot_name": "OpenAIBot",
            "version": "o1-mini-2024-09-12",
            "commands": ["omini"],
            "prefix": None,
            "api_spec": "https://platform.openai.com/docs/models/o1",
            "input_price": Decimal("0.003"),
            "output_price": Decimal("0.012"),
            "max_context_tokens": 128000,
            "charge_type": "TOKEN",
            "stream": False
        },
        "grok": {
            "provider": "xai",
            "name": "grok",
            "full_name": "Grok",
            "bot_name": "xAIBot",
            "version": "grok-beta",
            "commands": ["gk", "grok", "x"],
            "prefix": ["gk. ", "x. "],
            "api_spec": "https://docs.x.ai/api#introduction",
            "input_price": Decimal("0.005"),
            "output_price": Decimal("0.015"),
            "max_context_tokens": 131072,
            "charge_type": "TOKEN",
            "stream": False
        }
    },
    "image_models": {
        "dalle-3": {
            "provider": "openai",
            "name": "dalle-3",
            "full_name": "DALL-E 3",
            "bot_name": "DalleBot",
            "version": "dall-e-3",
            "commands": ["dalle", "image", "img", "i"],
            "prefix": ["i. ", ", ", "d. "],
            "api_spec": "https://openai.com/index/dall-e-3/",
            "price": {
                "size_1024_1024": Decimal("0.08"),
                "size_1024_1792": Decimal("0.12"),
                "size_1792_1024": Decimal("0.12")
            }
        },
        "lumaai": {
            "provider": "luma",
            "name": "Luma AI",
            "full_name": "Luma AI",
            "bot_name": "LumaBot",
            "version": "lumaai-1-0-2",
            "commands": ["luma", "l"],
            "prefix": ["l. "],
            "api_spec": "https://docs.lumalabs.ai/docs/welcome",
            "price": {
                "size_1024_1024": Decimal("0.08"),
                "size_1024_1792": Decimal("0.12"),
                "size_1792_1024": Decimal("0.12")
            }
        }
    },
    "provider_parameters": {
        "openai": {
            "default_parameters": {
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "model_overrides": {
                "o1": {"temperature": 1}
            }
        },
        "claude": {
            "default_parameters": {
                "max_tokens": 2000
            }
        },
        "xai": {
            "default_parameters": {
                "max_tokens": 2000
            }
        },
        "vertex": {
            "default_parameters": {
                "max_tokens": 2000
            }
        },
        "luma": {
            "default_parameters": {
                "max_tokens": 2000
            }
        }
    }
}