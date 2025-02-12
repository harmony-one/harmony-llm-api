from typing import Any, Dict, List
class StockInfo:
    def __init__(self, stock_info: Dict[str, Any]):
        self.name = stock_info.get("longName", "")
        self.symbol = stock_info.get("symbol", "")
        self.current_price = stock_info.get("currentPrice", 0.0)
        self.previous_close = stock_info.get("regularMarketPreviousClose", 0.0)
        self.open = stock_info.get("regularMarketOpen", 0.0)
        self.day_high = stock_info.get("regularMarketDayHigh", 0.0)
        self.day_low = stock_info.get("regularMarketDayLow", 0.0)
        self.week_52_high = stock_info.get("fiftyTwoWeekHigh", 0.0)
        self.week_52_low = stock_info.get("fiftyTwoWeekLow", 0.0)
        self.market_cap = stock_info.get("marketCap", 0.0)
        self.volume = stock_info.get("regularMarketVolume", 0.0)
        self.pe_ratio = stock_info.get("trailingPE", 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Name": self.name,
            "Symbol": self.symbol,
            "Current Price": self.current_price,
            "Previous Close": self.previous_close,
            "Open": self.open,
            "Day High": self.day_high,
            "Day Low": self.day_low,
            "52-Week High": self.week_52_high,
            "52-Week Low": self.week_52_low,
            "Market Cap": self.market_cap,
            "Volume": self.volume,
            "PE Ratio": self.pe_ratio,
        }