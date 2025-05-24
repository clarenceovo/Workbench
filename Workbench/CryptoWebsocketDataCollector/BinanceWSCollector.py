from Workbench.config.ConnectionConstant import BINANCE_FUTURES_WS_URL , BINANCE_FUTURES_API_URL
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector

class BinanceWSCollector(BaseWSCollector):
    """
    Binance WebSocket data collector.
    """
    def __init__(self, url="wss://stream.binance.com:9443/ws"):
        super().__init__("BinanceWS",url)
        self.data_collector = BinanceDataCollector()

        self.client = None
        self.data = None

    def connect(self):
        """
        Connect to the Binance WebSocket server.
        """
        self.client = super().connect()