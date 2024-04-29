from tools import ToolBase, YahooFinanceTool
from models import RunningTool, ToolsBetaMessage

class AnthropicHelper:
    running_tools = []
    tools = []

    def add_tool(self, tool: ToolBase):
        self.tools.append(tool)
    
    def get_tools(self):
        return self.tools
    
    def get_claude_tools_definition(self):
        definition = []
        for tool in self.tools:
            definition.append(tool.claude_tool_definition())
        
        return definition

    def excecute_tool(self, tool_name):
        for tool in self.tools:
          if tool.is_supported(tool_name):
              return tool
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


anthropicHelper = AnthropicHelper()

yft = YahooFinanceTool(
    name='get_ticker_info',
    description="Get the financial information of a ticker symbol"
)

anthropicHelper.add_tool(yft)