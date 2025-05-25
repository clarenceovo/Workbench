from overrides import overrides

from Workbench.config.ConnectionConstant import HTX_FUTURES_WS_URL, QUEST_HOST , QUEST_PORT
from Workbench.CryptoDataConnector.HTXDataCollector import HTXDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.util.TimeUtil import get_latency_ms
from Workbench.model.orderbook.BTreeOrderbook import OrderbookCollection, BTreeOrderbook, Order, Side
from Workbench.transport.QuestClient import QuestDBClient
import gzip
import json
from io import BytesIO

HTX_WS_TOPICS = {
    "market": {
        "kline": "market.{symbol}.kline.{period}",               # e.g. period: 1min, 5min
        "depth": "market.{symbol}.depth.step{step}",             # e.g. step: step0, step1
        "trade": "market.{symbol}.trade.detail",
        "ticker": "market.{symbol}.detail",
        "basis": "market.{symbol}.basis.{period}"                # e.g. period: 1min, 5min
    },
    "account": {
        "order_update": "orders.{symbol}",                       # Requires authentication
        "account_update": "accounts.{symbol}",                   # Requires authentication
    },
    "system": {
        "status": "public.system.status"                         # System status
    }

}
class HtxWSCollector(BaseWSCollector):
    """
    HTX (Huobi) WebSocket data collector.
    """

    def __init__(self, url=HTX_FUTURES_WS_URL):
        super().__init__("HtxWS", url)
        self.data_collector = HTXDataCollector()
        self.load_instrument()
        self.db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)


    def load_instrument(self):
        self.logger.info("Loading instrument info...")
        self.instrument_info = self.data_collector.get_contract_details()
        obj = self.data_collector.get_contract_details()
        self.instrument_info = obj

    def _handle_depth_message(self, msg):
        """
        Handle depth messages from the WebSocket.
        """
        #self.logger.info("Received depth message: %s", msg)
        ts = msg["ts"]
        self.logger.info("Latency: %s", get_latency_ms(ts))

    def __message_handler(self, msg):
        """
        Handle incoming messages from the WebSocket.
        """
        msg = HtxWSCollector.decode_gzip_message(msg)
        if msg.get("ping"):
            self.ping(msg)
            return
        if msg.get("ch"):
            topic = msg["ch"]
            if topic.startswith("market") and "depth" in topic:
                self._handle_depth_message(msg)

            """
            elif topic.startswith("market") and "trade" in topic:
                self.handle_trade_message(msg)
            elif topic.startswith("market") and "ticker" in topic:
                self.handle_ticker_message(msg)
            elif topic.startswith("orders"):
                self.handle_order_update(msg)
            elif topic.startswith("accounts"):
                self.handle_account_update(msg)
            """



    def disconnect(self):
        pass


    def subscribe(self):
        setattr(self, "orderbook", OrderbookCollection("HTX"))
        target_inst = ["BTC-USDT","ETH-USDT"] #TODO: load this from redis instrument list
        target_inst.extend(["GRASS-USDT", "PENDLE-USDT", "XMR-USDT", "SOLV-USDT", "SXT-USDT", "NIL-USDT", "DEGEN-USDT", "EPT-USDT",
         "APE-USDT", "ALCH-USDT"])
        topic_template = HTX_WS_TOPICS["market"]['depth']
        for inst in target_inst:
            topic = topic_template.format(symbol=inst, step=0)
            self.client.send({"sub": topic})
            self.logger.info(f"Subscribed to {topic}")



    def unsubscribe(self, topic: str):
        pass


    def ping(self,msg):
        self.client.send({"pong": msg["ping"]})
        pass

    def run(self):
        self.client.register_callback(self.__message_handler)
        self.subscribe()
        self.client.start()

    def connect(self):
        """
        Connect to the HTX WebSocket server.
        """
        pass

    @staticmethod
    def decode_gzip_message(message: bytes) -> dict:
        buf = BytesIO(message)
        with gzip.GzipFile(fileobj=buf) as f:
            decoded_bytes = f.read()
        return json.loads(decoded_bytes.decode('utf-8'))

if __name__ == '__main__':
    obj = HtxWSCollector()
    obj.run()