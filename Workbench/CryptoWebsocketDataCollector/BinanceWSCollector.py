from Workbench.config.ConnectionConstant import BINANCE_FUTURES_WS_URL , BINANCE_FUTURES_API_URL
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector

class BinanceWSCollector(BaseWSCollector):
    """
    Binance WebSocket data collector.
    """



    def __init__(self, url=BINANCE_FUTURES_WS_URL):
        super().__init__("BinanceWS",url)
        self.data_collector = BinanceDataCollector()
        self.instrument_info = None
        self.client = None
        self.data = None

    def load_instrument(self):
        obj = self.data_collector.get_contract_details()
        #apply PERP filter
        obj = obj[obj['contractType'] == 'PERPETUAL']
        #apply USDT filter
        obj = obj[obj['quoteAsset'] == 'USDT']
        self.instrument_info = obj

    def disconnect(self):
        pass

    def subscribe(self, topic: str):
        pass

    def unsubscribe(self, topic: str):
        pass

    def ping(self):
        pass

    def run(self):
        self.load_instrument()


    def connect(self):
        """
        Connect to the Binance WebSocket server.
        """
        pass

if __name__ == '__main__':
    obj = BinanceWSCollector()
    obj.run()