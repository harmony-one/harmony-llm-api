from tools import ToolBase, YahooFinanceTool

class AnthropicHelper:
    tools = []

    def addTools(self, tool: ToolBase):
        self.tools.append(tool)
    
    def getTools(self):
        return self.tools

    def getClaudeToolsDefinition(self):
        definition = []
        for tool in self.tools:
            definition.append(tool.claude_tool_definition())
        
        return definition

    def excecuteTool(self, tool_name):
        for tool in self.tools:
          if tool.is_supported(tool_name):
              return tool
        return None


anthropicHelper = AnthropicHelper()

yft = YahooFinanceTool(
    name='get_ticker_info',
    description="Get the financial information of a ticker symbol"
)

anthropicHelper.addTools(yft)