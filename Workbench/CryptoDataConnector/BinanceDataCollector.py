import pandas as pd
from datetime import datetime, timedelta
from Workbench.model.option.option import Option
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector
from Workbench.config.ConnectionConstant import BINANCE_FUTURES_API_URL , BINANCE_SPOT_WS_URL
from enum import Enum

class Mode(Enum):
    SPOT = "spot"
    FUTURES = "futures"

class BinanceDataCollector(BaseDataCollector):
    def __init__(self, name="BinanceDataCollector", mode=Mode.FUTURES):
        super().__init__(name)
        self.mode = mode
        self.base_spot_url = BINANCE_SPOT_WS_URL
        self.base_futures_url = BINANCE_FUTURES_API_URL


    def get_depth(self):
        pass  # To be implemented if needed

    def get_kline(self, symbol="BTCUSDT", interval="1m", limit=100):
        url = f"{self.base_spot_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_instrument(self) -> pd.DataFrame:
        url = f"{self.base_spot_url}/api/v3/exchangeInfo"
        resp = self.session.get(url)
        resp.raise_for_status()
        return pd.DataFrame.from_dict(resp.json()['symbols'])

    def get_contract_details(self) -> pd.DataFrame:
        url = f"{self.base_futures_url}/fapi/v1/exchangeInfo"
        resp = self.session.get(url)
        resp.raise_for_status()
        return pd.DataFrame.from_dict(resp.json()['symbols'])

    def get_open_interest(self, symbol):
        url = f"{self.base_futures_url}/fapi/v1/openInterest"
        params = {"symbol": symbol}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_funding(self, symbol, limit):
        url = f"{self.base_futures_url}/fapi/v1/fundingRate"
        params = {"symbol": symbol, "limit": limit}
        resp = self.session.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_time(self):
        url = f"{self.base_spot_url}/api/v3/time"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()["serverTime"]

    def get_option_chain(self, symbol='BTCUSDT'):
        """
        Get the option chain for a given symbol.
        """
        url = "https://eapi.binance.com/eapi/v1/exchangeInfo"
        resp = self.session.get(url)
        resp.raise_for_status()
        data = resp.json()

        # Filter contracts for the given underlying symbol
        return [opt for opt in data['optionSymbols'] if opt['underlying'] == symbol]

    def get_option_open_interest(self,symbol: str):
        url = "https://eapi.binance.com/eapi/v1/openInterest"
        params = {"symbol": symbol}
        resp = self.session.get(url,params=params)
        resp.raise_for_status()
        return resp.json()

    def get_option_ticker(self,symbol):
        url = "https://eapi.binance.com/eapi/v1/ticker"
        params = {"symbol": symbol}
        resp = self.session.get(url,params=params)
        resp.raise_for_status()
        return resp.json()

    def get_option_by_symbol(self, symbol_info:dict):

        symbol = symbol_info["symbol"]
        try:
            ticker = self.get_option_ticker(symbol)
            oi = self.get_option_open_interest(symbol)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

        return Option(
            contractSymbol=symbol,
            strike=float(symbol_info["strikePrice"]),
            lastPrice=float(ticker["lastPrice"]),
            bid=float(ticker["bidPrice"]),
            ask=float(ticker["askPrice"]),
            change=float(ticker["priceChange"]),
            percentChange=float(ticker["priceChangePercent"]),
            openInterest=oi,
            impliedVolatility=float(ticker["impliedVolatility"]),
            inTheMoney=bool(symbol_info["inTheMoney"]),
            lastTradeDate=datetime.utcfromtimestamp(int(ticker["time"]) / 1000),
            expiration=datetime.strptime(symbol_info["expiryDate"], "%Y-%m-%d"),
            currency="USDT",  # Binance options are quoted in USDT
            volume=int(ticker["volume"])
        )