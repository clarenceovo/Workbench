import json
import time
from Workbench.config.ConnectionConstant import BINANCE_FUTURES_WS_URL, BINANCE_FUTURES_API_URL, QUEST_HOST, QUEST_PORT
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.util.TimeUtil import get_latency_ms, get_utc_now_ms
from Workbench.model.orderbook.BTreeOrderbook import OrderbookCollection, BTreeOrderbook, Order, Side
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.model.dto.TopOfBook import TopOfBook

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
    orderbook: OrderbookCollection

    def __init__(self, url=BINANCE_FUTURES_WS_URL, start_quest = True):
        super().__init__("BinanceWS", url)
        self.data_collector = BinanceDataCollector()
        self.load_instrument()
        self.last_publish = {}
        self.tickerbook = {}
        if start_quest:
            self.db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)

    def load_instrument(self):
        obj = self.data_collector.get_contract_details()
        # apply PERP filter
        obj = obj[obj['contractType'] == 'PERPETUAL']
        # apply USDT filter
        obj = obj[obj['quoteAsset'] == 'USDT']
        self.instrument_info = obj

    def disconnect(self):
        pass

    def subscribe(self,topic_list: list = None):
        setattr(self, "orderbook", OrderbookCollection("Binance"))
        if topic_list is None:
            return
        topic_list = [inst.replace("-", "").lower() for inst in topic_list]
        topic_template = BINANCE_WS_TOPICS['market']["book_ticker"]
        for inst in topic_list:
            self.logger.info("Subscribing to topic {}".format(inst))
            self.orderbook.add_orderbook(inst)
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

    def _get_contract_size(self, symbol: str):
        """
        Get the contract size for a given symbol.
        :param symbol: The trading pair symbol.
        :return: The contract size.
        """
        contract_info = self.instrument_info[self.instrument_info['symbol'] == symbol]
        if not contract_info.empty:
            return float(contract_info['contractSize'].values[0])
        return None

    def _handler_book_ticker(self, msg):
        """
        Handle book ticker messages from the WebSocket.
        :param msg:
        :return:
        """
        # self.logger.info(msg)
        # contract_size = self._get_contract_size(msg["s"])
        bbo = TopOfBook(
            timestamp=msg.get("E"),
            exchange="Binance",
            symbol=msg.get('s'),
            bid_price=float(msg.get('b')),
            bid_qty=float(msg.get('B')),
            ask_price=float(msg.get('a')),
            ask_qty=float(msg.get('A')),
        )
        self.tickerbook[msg.get('s')] = bbo
        bbo = bbo.to_batch()
        if get_utc_now_ms() - self.last_publish.get(msg.get('s'), 0) > 10:
            self.last_publish[msg.get('s')] = get_utc_now_ms()
            self.db_client.batch_write(bbo)

    def _message_handler(self, msg):
        """
        Handle incoming messages from the WebSocket.
        """
        #self.logger.info("Received message: %s", msg)
        msg = json.loads(msg)
        if msg.get("stream", None):
            topic = msg["stream"]
            if "bookTicker" in topic:

                self._handler_book_ticker(msg['data'])

    def run(self):
        self.load_instrument()
        self.client.register_callback(self._message_handler)
        self.client.start()
        time.sleep(1)
        self.subscribe()

    def connect(self):
        """
        Connect to the Binance WebSocket server.
        """
        pass


if __name__ == '__main__':
    obj = BinanceWSCollector()
    obj.run()
