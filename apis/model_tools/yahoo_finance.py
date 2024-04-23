import yfinance as yf

def get_ticker_info(ticker):
  ticker = yf.Ticker(ticker).info
  # print('FCO', ticker)
  market_price = ticker['currentPrice']
  # previous_close_price = ticker['regularMarketPreviousClose']
  # print('Ticker: GOOGL')
  # print('Market Price:', market_price)
  # print('Previous Close Price:', previous_close_price)
  return f"Market price: {market_price}"
  return str(ticker)


def tool_def():
  return {
    "name": "get_ticker_info",
    "description": "Get the financial information of a ticker symbol",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The ticker symbol",
            }
        },
        "required": ["ticker"],
    },
  }