from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from binance.client import Client
class TickerType(Enum):
    STOCK = 1
    INDEX = 2
    FUTURE = 3
    FX = 4
    CRYPTO_SPOT = 5
    CRYPTO_FUTURE = 6
    CRYPTO_SWAP = 7

@dataclass
class TickerSeries(Enum):
    DAILY = 1
    H1 = 2
    H4 = 3
    H8 = 4
    M5 = 5
    M15 = 6
    M30 = 7
    M1 = 8

    @staticmethod
    def from_binance_interval(interval):
        if interval == Client.KLINE_INTERVAL_1DAY:
            return TickerSeries.DAILY
        elif interval == Client.KLINE_INTERVAL_1HOUR:
            return TickerSeries.H1
        elif interval == Client.KLINE_INTERVAL_4HOUR:
            return TickerSeries.H4
        elif interval == Client.KLINE_INTERVAL_8HOUR:
            return TickerSeries.H8
        elif interval == Client.KLINE_INTERVAL_5MINUTE:
            return TickerSeries.M5
        elif interval == Client.KLINE_INTERVAL_15MINUTE:
            return TickerSeries.M15
        elif interval == Client.KLINE_INTERVAL_30MINUTE:
            return TickerSeries.M30
        elif interval == Client.KLINE_INTERVAL_1MINUTE:
            return TickerSeries.M1
        else:
            return None
@dataclass
class CryptoTicker:
    tickerId: int
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    series_type: TickerSeries

    def to_tuple(self):
        return (str(self.tickerId),self.time,self.open,self.high,self.low,self.close,self.volume,self.series_type.value)