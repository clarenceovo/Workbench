from overrides import overrides

from Workbench.config.ConnectionConstant import HTX_FUTURES_WS_URL, QUEST_HOST , QUEST_PORT
from Workbench.CryptoDataConnector.HTXDataCollector import HTXDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.model.dto.TopOfBook import TopOfBook
from Workbench.util.TimeUtil import get_latency_ms
from Workbench.model.orderbook.BTreeOrderbook import OrderbookCollection, BTreeOrderbook, Order, Side
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.util.OrderUtil import decode_gzip_message
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
    orderbook: OrderbookCollection

    def __init__(self, url=HTX_FUTURES_WS_URL,is_publish=False):
        super().__init__("HtxWS", url)
        self.is_publish = is_publish
        self.data_collector = HTXDataCollector()
        self.load_instrument()
        self.db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)


    def load_instrument(self):
        self.logger.info("Loading instrument info...")
        self.instrument_info = self.data_collector.get_contract_details()
        obj = self.data_collector.get_contract_details()
        self.instrument_info = obj

    def _get_contract_size(self, symbol: str) -> float:
        """
        Get the contract size for a given symbol.
        :param symbol: The trading pair symbol.
        :return: The contract size as a float.
        """
        if self.instrument_info is not None:

            return self.instrument_info.query("contract_code == @symbol")['contract_size'].values[0]
        return 1.0

    def _handle_depth_message(self, msg):
        """
        Handle depth messages from the WebSocket.
        """
        #self.logger.info("Received depth message: %s", msg)
        channel = msg.get("ch", "")
        symbol = channel.split(".")[1] if "." in channel else ""
        if not symbol:
            self.logger.error("Invalid channel format: %s", channel)
            return
        orderbook = self.orderbook.get_orderbook(symbol)
        tick = msg.get("tick", {})
        cts = msg.get("ts", 0)  # Use the timestamp from the message

        conversion = self._get_contract_size(symbol)
        # Process bids
        for bid in tick.get("bids", []):
            price, size = bid
            orderbook.insert_order(Order(cts, float(price), float(size)*float(conversion), Side.BID))

        # Process asks
        for ask in tick.get("asks", []):
            price, size = ask
            orderbook.insert_order(Order(cts, float(price), float(size)*float(conversion), Side.ASK))

        if self.is_publish:
            bbo = TopOfBook(
                timestamp=cts,
                exchange="HTX",
                symbol=symbol,
                bid_price=orderbook.best_bid().price if orderbook.best_bid() else None,
                bid_qty=orderbook.best_bid().qty if orderbook.best_bid() else None,
                ask_price=orderbook.best_ask().price if orderbook.best_ask() else None,
                ask_qty=orderbook.best_ask().qty if orderbook.best_ask() else None
            )

            self.db_client.batch_write(bbo.to_batch())

    def __message_handler(self, msg):
        """
        Handle incoming messages from the WebSocket.
        """
        msg = decode_gzip_message(msg)
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


    def subscribe(self,topic_list=["BTC-USDT"]):
        setattr(self, "orderbook", OrderbookCollection("HTX"))

        topic_template = HTX_WS_TOPICS["market"]['depth']
        for inst in topic_list:
            topic = topic_template.format(symbol=inst, step=0)
            self.orderbook.add_orderbook(inst)
            self.client.send({"sub": topic})
            self.logger.info(f"Subscribed to {topic}")

    def unsubscribe(self, topic: str):
        pass

    def ping(self,msg):
        self.client.send({"pong": msg["ping"]})
        pass

    def run(self):
        self.client.register_callback(self.__message_handler)
        self.client.start()

    def connect(self):
        """
        Connect to the HTX WebSocket server.
        """
        pass



if __name__ == '__main__':
    obj = HtxWSCollector()
    obj.run()
    target_inst = ["BTC-USDT", "ETH-USDT"]  # TODO: load this from redis instrument list
    target_inst.extend(
        ["GRASS-USDT", "PENDLE-USDT", "XMR-USDT", "SOLV-USDT", "SXT-USDT", "NIL-USDT", "DEGEN-USDT", "EPT-USDT",
         "APE-USDT", "ALCH-USDT", "SOL-USDT"])  # Add more instruments as needed
    obj.subscribe(target_inst)