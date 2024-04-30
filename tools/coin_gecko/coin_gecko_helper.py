import requests

COIN_GECKO_URL = "https://api.coingecko.com/api/v3"

class CoinGeckoHelper:
    def __init__(self):
        self.coins_data = []
        self.load_coins_data()

    def load_coins_data(self):
        endpoint = f"{COIN_GECKO_URL}/coins/list"
        response = requests.get(endpoint)
        if response.status_code == 200:
            self.coins_data = response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")

    def get_id(self, symbol):
        symbol = symbol.lower()
        for coin in self.coins_data:
            if coin.get("symbol").lower() == symbol or coin.get("name").lower() == symbol:
                return coin.get("id")
        return None
    
    def get_price(self, ids):
        endpoint = f"{COIN_GECKO_URL}/simple/price?ids={ids.lower()}&vs_currencies=usd"
        response = requests.get(endpoint)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")

