import time

from binance.client import Client
from datetime import datetime
import pandas as pd
import logging
from binance.enums import HistoricalKlinesType
from typing import Union
class BinanceDataCollector:
    def __init__(self, key :str , secret:str):
        super().__init__()
        self.logger = logging.getLogger("BinanceDataCollector")
        self.api_key = {
                    "api_key": key,
                    "api_secret": secret
                  }
        self.client = Client(self.api_key['api_key'], self.api_key['api_secret'])
        self.ticker_id_cache = None

    def get_spot_historical_klines(self, symbol, interval, start:datetime,end:datetime=None)->pd.DataFrame:
        self.logger.info(f"Fetching historical data for {symbol} with interval {interval}")
        start_str = start.strftime("%-d %b, %Y")
        if end:
            end_str = end.strftime("%-d %b, %Y")
        else:
            end_str = None

        data =  self.client.get_historical_klines(symbol, interval, start_str=start_str,end_str=end_str)
        data = pd.DataFrame(data, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time",
                                            "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                                            "Taker buy quote asset volume", "Ignore"])
        return data

    def get_future_historical_klines(self, symbol, interval, start:datetime,end:datetime=None)->pd.DataFrame:
        self.logger.info(f"Fetching historical data for {symbol} with interval {interval}")
        start_str = start.strftime("%-d %b, %Y")
        if end:
            end_str = end.strftime("%-d %b, %Y")
        else:
            end_str = None

        data =  self.client.get_historical_klines(symbol, interval, start_str=start_str,end_str=end_str,klines_type=HistoricalKlinesType.FUTURES)
        data = pd.DataFrame(data, columns=["Open time", "Open", "High", "Low", "Close", "Volume", "Close time",
                                            "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                                            "Taker buy quote asset volume", "Ignore"])
        return data



    def get_funding(self,symbol:str)->Union[float,None]:
        self.logger.info(f"Fetching funding rate for {symbol}")
        data = self.client.futures_funding_rate(symbol=symbol,limit=1000)
        if len(data) == 0:
            return None
        else:
            df = pd.DataFrame(data,columns=["symbol","fundingTime","fundingRate","markPrice"])
            df['fundingTime'] = pd.to_datetime(df['fundingTime'],unit='ms')
            df['fundingRate'] = df['fundingRate'].astype(float)
            df['markPrice'] = df['markPrice'].astype(float)
            return df

    def get_whole_market(self):
        self.logger.info("Fetching all the prices")
        prices = self.client.get_all_tickers()
        return prices

