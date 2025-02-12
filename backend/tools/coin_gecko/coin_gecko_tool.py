import requests
from typing import Any, Dict, List

from .coin_gecko_helper import CoinGeckoHelper

from ..tool_base import ToolBase
from ..tool_box_base import ToolBoxBase

helper = CoinGeckoHelper()

class CoinGeckoPrice(ToolBase):
    
    def __init__(self):
        super(CoinGeckoPrice, self).__init__(
            name='get_coin_price_info',
            description="Uses the coingecko API to retrieve the prices in USD of one or more coins by using their unique coin ID, e.g., IDs like bitcoin (for Bitcoin, BTC) or harmony (for Harmony, ONE)")
        
    def claude_tool_definition(self) -> Dict[str, Any]:
       return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The ID of the coin price to retrieve, e.g. IDs like 'harmony' or 'bitcoin'"
                    }
                },
                "required": ["id"]
            }
        }
    
    def run(self, tool_input) -> Dict[str, Any]:
        try:
            price = helper.get_price(tool_input.get('id'))
            return price

        except Exception as e:
            print(f"An error occurred: {e}")
            return "There was an error while trying to retrieve the information"
   

class CoinGeckoID(ToolBase):
    
    def __init__(self):
        super(CoinGeckoID, self).__init__(
            name='get_coin_id',
            description="Get the unique ID of a give coin name or symbol, e.g. for Bitcoin (symbol btc), the id is 'bitcoin'"
        )
        
    def claude_tool_definition(self) -> Dict[str, Any]:
       return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "coin": {
                        "type": "string",
                        "description": "A coin name or symbol, e.g. ('Bitcoin', 'btc')"
                    }
                },
                "required": ["coin"]
            }
        }
    
    def run(self, tool_input) -> Dict[str, Any]:
        try:
            id = helper.get_id(tool_input.get('coin'))
            return id
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return "There was an error while trying to retrieve the information"


coin_gecko_tool_box = ToolBoxBase(
    name="Coin Gecko Tool Box",
    description="Tool box to retrieve token finance data"
)

coin_gecko_tool_box.add_tool(CoinGeckoID())
coin_gecko_tool_box.add_tool(CoinGeckoPrice())

