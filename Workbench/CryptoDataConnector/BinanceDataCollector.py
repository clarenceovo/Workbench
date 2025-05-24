import requests
import pandas as pd
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector
from enum import Enum

class Mode(Enum):
    SPOT = "spot"
    FUTURES = "futures"

class BinanceDataCollector(BaseDataCollector):
    def get_depth(self):
        pass

    def __init__(self, name="BinanceDataCollector",mode=Mode.FUTURES):
        super().__init__(name)
        self.base_spot_url = "https://api.binance.com"
        self.base_futures_url = "https://fapi.binance.com"

    def get_kline(self, symbol="BTCUSDT", interval="1m", limit=100):
        url = f"{self.base_spot_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_instrument(self)->pd.DataFrame:
        url = f"{self.base_spot_url}/api/v3/exchangeInfo"
        resp = requests.get(url)
        resp.raise_for_status()
        return pd.DataFrame.from_dict(resp.json()['symbols'])

    def get_contract_details(self)-> pd.DataFrame:
        url = f"{self.base_futures_url}/fapi/v1/exchangeInfo"
        resp = requests.get(url)
        resp.raise_for_status()
        return pd.DataFrame.from_dict(resp.json()['symbols'])

    def get_open_interest(self, symbol):
        url = f"{self.base_futures_url}/fapi/v1/openInterest"
        params = {"symbol": symbol}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_funding(self, symbol, limit):
        url = f"{self.base_futures_url}/fapi/v1/fundingRate"
        params = {"symbol": symbol, "limit": limit}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_time(self):
        url = f"{self.base_spot_url}/api/v3/time"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json()["serverTime"]