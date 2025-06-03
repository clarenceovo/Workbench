import requests
import pandas as pd
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector

class BybitDataCollector(BaseDataCollector):
    def __init__(self, name="BybitDataCollector"):
        super().__init__(name)
        self.base_url = "https://api.bybit.com"
        self.headers = {"Content-Type": "application/json"}

    def get_kline(self, category="linear", symbol="BTCUSDT", interval="1", limit=200):
        """
        category: 'spot', 'linear', 'inverse'
        interval: in minutes ('1', '3', '5', etc)
        """
        url = f"{self.base_url}/v5/market/kline"
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("result", {}).get("list", [])

    def get_instrument(self):
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {"category": "spot"}
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        ret =  resp.json().get("result", {}).get("list", [])
        return pd.DataFrame.from_dict(ret)

    def get_contract_details(self):
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {"category": "linear"}  # Can change to 'inverse'
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        ret =  resp.json().get("result", {}).get("list", [])
        return pd.DataFrame.from_dict(ret)

    def get_open_interest(self, symbol="BTCUSDT", category="linear",limit=50):
        url = f"{self.base_url}/v5/market/open-interest"
        params = {
            "symbol": symbol,
            "category": category,
            "intervalTime": "5min",  # 5 minute interval
            "limit": limit  # Limit to the latest data point
        }
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("result", {})

    def get_funding(self, symbol="BTCUSDT", category="linear"):
        url = f"{self.base_url}/v5/market/funding/history"
        params = {
            "symbol": symbol,
            "category": category,
            "limit": 1
        }
        resp = requests.get(url, params=params, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("result", {}).get("list", [])

    def get_time(self):
        url = f"{self.base_url}/v5/market/time"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json().get("time")

    def get_depth(self):
        pass