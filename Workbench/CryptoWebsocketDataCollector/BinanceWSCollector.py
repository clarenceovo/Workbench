import json

from Workbench.config.ConnectionConstant import BINANCE_FUTURES_WS_URL, BINANCE_FUTURES_API_URL
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.util.TimeUtil import get_latency_ms

BINANCE_WS_TOPICS = {
    "market": {
        "aggregate_trade": "{symbol}@aggTrade",
        "mark_price": "{symbol}@markPrice",
        "mark_price_all": "!markPrice@arr",
        "kline": "{symbol}@kline_{interval}",
        "continuous_kline": "{pair}@continuousKline_{contractType}_{interval}",
        "mini_ticker": "{symbol}@miniTicker",
        "mini_ticker_all": "!miniTicker@arr",
        "ticker": "{symbol}@ticker",
        "ticker_all": "!ticker@arr",
        "book_ticker": "{symbol}@bookTicker",
        "book_ticker_all": "!bookTicker@arr",
        "liquidation": "{symbol}@forceOrder",
        "liquidation_all": "!forceOrder@arr",
        "partial_book_depth": "{symbol}@depth{levels}@{speed}",
        "diff_book_depth": "{symbol}@depth@{speed}",
        "composite_index": "{symbol}@compositeIndex",
        "contract_info": "{symbol}@contractInfo",
        "multi_assets_mode_asset_index": "multiAssetsMode@assetIndex"
    },
    "user_data": {
        "listen_key": "<generated_listenKey>"
    }
}


class BinanceWSCollector(BaseWSCollector):
    """
    Binance WebSocket data collector.
    """

    def __init__(self, url=BINANCE_FUTURES_WS_URL):
        super().__init__("BinanceWS", url)
        self.data_collector = BinanceDataCollector()
        self.load_instrument()

    def load_instrument(self):
        obj = self.data_collector.get_contract_details()
        # apply PERP filter
        obj = obj[obj['contractType'] == 'PERPETUAL']
        # apply USDT filter
        obj = obj[obj['quoteAsset'] == 'USDT']
        self.instrument_info = obj

    def disconnect(self):
        pass

    def subscribe(self):
        target_inst = ['btcusdt', 'ethusdt',"pendleusdt","solvusdt","pendleusdt"]  # TODO: load this from redis instrument list
        topic_template = BINANCE_WS_TOPICS['market']["book_ticker"]
        for inst in target_inst:
            topic = topic_template.format(symbol=inst)
            self.client.send({
                "method": "SUBSCRIBE",
                "params": [topic],
                "id": 1
            })

    def unsubscribe(self, topic: str):
        pass

    def ping(self):
        pass

    def _handler_book_ticker(self, msg):
        """
        Handle book ticker messages from the WebSocket.
        :param msg:
        :return:
        """
        self.logger.info("Latency: %s", get_latency_ms(msg["E"]))
        self.logger.info("Book ticker received: {}".format(msg))

    def _message_handler(self, msg):
        """
        Handle incoming messages from the WebSocket.
        """
        # self.logger.info("Received message: %s", msg)
        msg = json.loads(msg)
        if msg.get("stream", None):
            topic = msg["stream"]
            if "bookTicker" in topic:
                self._handler_book_ticker(msg['data'])

    def run(self):
        self.load_instrument()
        self.client.register_callback(self._message_handler)
        self.subscribe()
        self.client.start()

    def connect(self):
        """
        Connect to the Binance WebSocket server.
        """
        pass


if __name__ == '__main__':
    obj = BinanceWSCollector()
    obj.run()
