from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ToolBase(ABC):
    
    def __init__(self, name, description):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, tool_name, tool_input):
       pass

    @abstractmethod   
    def claude_tool_definition(self) -> Dict[str, Any]:
        pass
    
    def is_supported(self, name):
       if (self.name == name):
           return self
       return None
    #    eturn self.name == name

