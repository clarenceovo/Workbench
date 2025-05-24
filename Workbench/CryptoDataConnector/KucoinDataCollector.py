import requests
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector

class KucoinDataCollector(BaseDataCollector):
    def __init__(self, name="KucoinDataCollector"):
        super().__init__(name)
        self.spot_base_url = "https://api.kucoin.com"
        self.futures_base_url = "https://api-futures.kucoin.com"
        self.headers = {"Content-Type": "application/json"}

    def get_kline(self, symbol="BTC-USDT", interval="1min", limit=100):
        url = f"{self.spot_base_url}/api/v1/market/candles"
        params = {
            "symbol": symbol,
            "type": interval,
            "limit": limit
        }
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_instrument(self):
        url = f"{self.spot_base_url}/api/v1/symbols"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_contract_details(self):
        url = f"{self.futures_base_url}/api/v1/contracts/active"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_open_interest(self, symbol="XBTUSDTM"):
        url = f"{self.futures_base_url}/api/v1/openInterest"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_funding(self, symbol="XBTUSDTM"):
        url = f"{self.futures_base_url}/api/v1/funding-rate"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_time(self):
        url = f"{self.spot_base_url}/api/v1/timestamp"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("data")