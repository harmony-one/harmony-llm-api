import yfinance as yf
from typing import Any, Dict, List

from models import StockInfo

from .tool_base import ToolBase

class YahooFinanceTool(ToolBase):
    
    def __init__(self, name, description):
        super(YahooFinanceTool, self).__init__(name=name, description=description)
    
    def claude_tool_definition(self) -> Dict[str, Any]:
       return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "A ticker symbol, e.g. ('APPL', 'GOOGL')"
                    }
                },
                "required": ["ticker"]
            }
        }
    
    def run(self, tool_input) -> Dict[str, Any]:
        try:
            ticker = tool_input.get('ticker')
            stock = yf.Ticker(ticker)
            info = stock.info
            stock = StockInfo(info)
            return stock.to_dict()

        except Exception as e:
            print(f"An error occurred: {e}")
            return "There was an error while trying to retrieve the information"

    