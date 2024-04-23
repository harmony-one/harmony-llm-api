from typing import Any, Dict, List

class TextBlock:
    def __init__(self, text: str, type: str):
        self.text = text
        self.type = type

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'type': self.type
        }

class Usage:
    def __init__(self, input_tokens: int, output_tokens: int):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens
        }

class ToolsBetaMessage:
    def __init__(self, id: str, content: List[TextBlock], model: str, role: str, stop_reason: str, stop_sequence: Any, type: str, usage: Usage):
        self.id = id
        self.content = content
        self.model = model
        self.role = role
        self.stop_reason = stop_reason
        self.stop_sequence = stop_sequence
        self.type = type
        self.usage = usage

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': [block.to_dict() for block in self.content],
            'model': self.model,
            'role': self.role,
            'stop_reason': self.stop_reason,
            'stop_sequence': self.stop_sequence,
            'type': self.type,
            'usage': self.usage.to_dict()
        }