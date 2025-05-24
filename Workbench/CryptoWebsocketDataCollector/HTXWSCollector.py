from Workbench.config.ConnectionConstant import HTX_FUTURES_WS_URL
from Workbench.CryptoDataConnector.HTXDataCollector import HTXDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector

class HtxWSCollector(BaseWSCollector):
    """
    HTX (Huobi) WebSocket data collector.
    """

    def __init__(self, url=HTX_FUTURES_WS_URL):
        super().__init__("HtxWS", url)
        self.data_collector = HTXDataCollector()
        self.instrument_info = None
        self.client = None
        self.data = None

    def load_instrument(self):
        obj = self.data_collector.get_contract_details()
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
        Connect to the HTX WebSocket server.
        """
        pass

if __name__ == '__main__':
    obj = HtxWSCollector()
    obj.run()