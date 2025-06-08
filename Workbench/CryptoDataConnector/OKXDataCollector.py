from typing import override

import pandas as pd
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector
from Workbench.config.ConnectionConstant import OKX_API_URL
from enum import Enum

class Mode(Enum):
    SPOT = "spot"
    FUTURES = "futures"

class OKXDataCollector(BaseDataCollector):
    def get_depth(self):
        pass

    def __init__(self, name="OKXDataCollector", mode=Mode.FUTURES):
        super().__init__(name)
        self.mode = mode
        self.base_url = OKX_API_URL

    def get_kline(self, symbol="BTC-USDT", interval="1m", limit=100):
        granularity_map = {
            "1m": 60,
            "3m": 180,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
        }
        if interval not in granularity_map:
            raise ValueError(f"Unsupported interval: {interval}")
        granularity = granularity_map[interval]

        instId = symbol.replace("USDT", "-USDT")  # "BTCUSDT" → "BTC-USDT"
        url = f"{self.base_url}/api/v5/market/candles"
        params = {"instId": instId, "bar": interval, "limit": limit}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()["data"]

    def get_instrument(self) -> pd.DataFrame:
        instType = "SPOT" if self.mode == Mode.SPOT else "SWAP"
        url = f"{self.base_url}/api/v5/public/instruments"
        params = {"instType": instType}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return pd.DataFrame.from_dict(resp.json()["data"])

    def get_contract_details(self) -> pd.DataFrame:
        return self.get_instrument()

    @override
    def get_open_interest(self, symbol):
        """Fetch swap open interest data."""
        url = f"{self.base_url}/api/v5/public/open-interest"
        params = {
            "uly": symbol,
            "instType": "SWAP" if self.mode == Mode.FUTURES else "SPOT"
        }
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("data", [])

    @override
    def get_funding(self, symbol, limit):
        instId = symbol.replace("USDT", "-USDT")
        url = f"{self.base_url}/api/v5/public/funding-rate-history"
        params = {"instId": instId, "limit": limit}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()["data"]

    def get_time(self):
        url = f"{self.base_url}/api/v5/public/time"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()["data"][0]["ts"]