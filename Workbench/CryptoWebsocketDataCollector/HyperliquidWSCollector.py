import json
import time
import websocket
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.CryptoDataConnector.HyperliquidDataCollector import HyperliquidDataCollector
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.model.dto.TopOfBook import TopOfBook
from Workbench.model.orderbook.BTreeOrderbook import OrderbookCollection
from Workbench.util.TimeUtil import get_utc_now_ms
from Workbench.config.ConnectionConstant import HYPERLIQUID_FUTURES_WS_URL, QUEST_HOST, QUEST_PORT

class HyperliquidWSCollector(BaseWSCollector):
    """
    Hyperliquid WebSocket data collector.
    """
    orderbook: OrderbookCollection

    def __init__(self, url=HYPERLIQUID_FUTURES_WS_URL): #deafault URL for Hyperliquid WebSocket
        super().__init__("HyperliquidWS", url)
        self.data_collector = HyperliquidDataCollector()
        self.load_instrument()
        self.last_publish = {}
        self.db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)

    def load_instrument(self):
        self.instrument_info = self.data_collector.get_contract_details()

    def subscribe(self, topic_list: list = None):
        setattr(self, "orderbook", OrderbookCollection("Hyperliquid"))
        if topic_list is None:
            topic_list = ["BTC", "ETH"]  # default symbols
        for inst in topic_list:
            self.logger.info(f"Subscribing to l2Book for {inst}")
            self.orderbook.add_orderbook(inst)
            topic = ["subscribe", {"type": "l2Book", "coin": inst}]
            self.client.send(topic)

    def _handler_l2book(self, msg):
        symbol = msg["coin"]
        bbo = TopOfBook(
            timestamp=int(msg["time"]),
            exchange="Hyperliquid",
            symbol=symbol,
            bid_price=float(msg["levels"][0][0]['px']),
            bid_qty=float(msg["levels"][0][0]['sz']),
            ask_price=float(msg["levels"][1][0]['px']),
            ask_qty=float(msg["levels"][1][0]['sz']),
        )
        bbo = bbo.to_batch()
        self.last_publish[symbol] = bbo
        if get_utc_now_ms() - self.last_publish.get(symbol, 0) > 10:
            self.last_publish[symbol] = get_utc_now_ms()
            #self.db_client.batch_write(bbo)

    def _message_handler(self, msg):
        msg = json.loads(msg)
        if msg.get("channel") == "l2Book":
            self._handler_l2book(msg["data"])
        elif msg.get("channel") == "subscriptionResponse":
            self.logger.info(f"Subscribing to l2Book for {msg}")

    def run(self):
        self.load_instrument()
        self.client.register_callback(self._message_handler)
        self.client.start()
        time.sleep(1)
        self.subscribe()

    def disconnect(self):
        pass

    def unsubscribe(self, topic: str):
        pass

    def ping(self):
        pass

    def connect(self):
        pass


if __name__ == '__main__':
    obj = HyperliquidWSCollector()
    obj.run()