from typing import Any, Dict, List

from .tool_base import ToolBase

class ToolBoxBase():
    tools = []

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def add_tool(self, tool: ToolBase):
        self.tools.append(tool)
    
    def is_supported(self, tool_name) -> ToolBase:
        for tool in self.tools:
            if tool.is_supported(tool_name):
                return tool
        return None
  
    def claude_tool_definition(self) -> List[Dict[str, Any]]:
        tool_definition: List[Dict[str, Any]] = []
        for tool in self.tools:
            tool_definition.append(tool.claude_tool_definition())
        return tool_definition
    
