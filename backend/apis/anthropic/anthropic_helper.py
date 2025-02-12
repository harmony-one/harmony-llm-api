from typing import Any, Dict, List
from tools import ToolBase, ToolBoxBase, YahooFinanceTool, coin_gecko_tool_box
from app_types import RunningTool, ToolsBetaMessage

class AnthropicHelper:
    running_tools = []
    tools = []

    def add_tool(self, tool: ToolBase | ToolBoxBase):
        self.tools.append(tool)
    
    def get_tools(self):
        return self.tools
    
    def get_claude_tools_definition(self):
        definition = []
        for tool in self.tools:
            if isinstance(tool, ToolBoxBase):
                definition.extend(tool.claude_tool_definition())
            else:
                definition.append(tool.claude_tool_definition())
        
        return definition

    def excecute_tool(self, tool_name):
        for tool in self.tools:
          t = tool.is_supported(tool_name)
          if t:
              return t
        return None
    
    def add_running_tool(self, id: str): 
        tool = RunningTool(id)
        self.running_tools.append(tool)
    
    def add_running_tool_result(self, id: str, result: ToolsBetaMessage):
        for tool in self.running_tools:
            if (tool.id == id):
                tool.add_result(result)
          
    def get_running_tool(self, id: str):
        for tool in self.running_tools:
            if (tool.id == id):
                return tool
        return None
    
    def delete_running_tool(self, id: str):
        self.running_tools = [elem for elem in self.running_tools if elem.id != id]


anthropicHelper = AnthropicHelper()

yft = YahooFinanceTool()

anthropicHelper.add_tool(yft)
anthropicHelper.add_tool(coin_gecko_tool_box)