import json
import time
import threading
from Workbench.config.ConnectionConstant import BYBIT_FUTURES_WS_URL, QUEST_HOST, QUEST_PORT
from Workbench.CryptoDataConnector.BybitDataCollector import BybitDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.model.orderbook.BTreeOrderbook import OrderbookCollection, BTreeOrderbook, Order, Side
from Workbench.model.dto.TopOfBook import TopOfBook
from Workbench.util.TimeUtil import get_latency_ms
from Workbench.transport.QuestClient import QuestDBClient

BYBIT_WS_TOPICS = {
    "market": {
        "orderbook": "orderbook.{depth}.{symbol}",  # Order book updates
        "public_trade": "publicTrade.{symbol}",  # Trade executions
        "ticker": "tickers.{symbol}",  # 24h rolling stats
        "kline": "kline.{interval}.{symbol}",  # Candlestick data (1m, 5m, 1h, etc.)
        "liquidation": "liquidation.{symbol}",  # Liquidations for a symbol
        "all_liquidation": "allLiquidation",  # All liquidations
        "insurance": "insurance",  # Insurance fund balance
        "lt_kline": "ltKline.{interval}.{symbol}",  # Long-term kline
        "lt_ticker": "ltTicker.{symbol}",  # Long-term ticker
        "lt_nav": "ltNav.{symbol}"  # Leveraged Token NAV
    }
}


class BatchInsert:
    topic: str
    symbol: dict
    columns: dict


class BybitWSCollector(BaseWSCollector):
    """
    Bybit WebSocket data collector.
    """
    orderbook: OrderbookCollection

    def __init__(self, url=BYBIT_FUTURES_WS_URL):
        super().__init__("BybitWS", url)
        self.data_collector = BybitDataCollector()
        self.load_instrument()
        self._ping_thread = threading.Thread(target=self.send_ping, daemon=True)
        self.db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)

    def load_instrument(self):
        self.instrument_info = self.data_collector.get_contract_details()

    def disconnect(self):
        pass

    def subscribe(self):
        setattr(self, "orderbook", OrderbookCollection("Bybit"))
        target_inst = ["BTCUSDT", "ETHUSDT", "PENDLEUSDT", "SOLVUSDT"]  # TODO: load from Redis
        topic_template = BYBIT_WS_TOPICS["market"]["orderbook"]
        for inst in target_inst:
            topic = topic_template.format(depth=50, symbol=inst.upper())
            self.orderbook.add_orderbook(inst)
            self.client.send({
                "op": "subscribe",
                "args": [topic]
            })
            self.logger.info(f"Subscribed to {topic}")

    def unsubscribe(self, topic: str):
        self.client.send({
            "op": "unsubscribe",
            "args": [topic]
        })

    def ping(self):
        self.client.send({"op": "ping"})


    def _handler_orderbook(self, msg):
        data = msg.get("data", {})
        symbol = data.get("s")
        cts = msg.get("cts", 0)
        book = self.orderbook.get_orderbook(symbol)
        for bids in data.get("b", []):
            price, size = bids
            book.insert_order(Order(cts, float(price), float(size), Side.BID))

        for asks in data.get("a", []):
            price, size = asks
            book.insert_order(Order(cts, float(price), float(size), Side.ASK))

        bbo = TopOfBook(
            timestamp=cts,
            exchange="Bybit",
            symbol=symbol,
            bid_price=book.best_bid().price if book.best_bid() else None,
            bid_qty=book.best_bid().qty if book.best_bid() else None,
            ask_price=book.best_ask().price if book.best_ask() else None,
            ask_qty=book.best_ask().qty if book.best_ask() else None
        )
        bbo = bbo.to_batch()


        self.db_client.batch_write(bbo)

    def _message_handler(self, raw_msg):
        msg = json.loads(raw_msg)
        if "topic" in msg and "orderbook" in msg["topic"]:
            self._handler_orderbook(msg)

    def run(self):
        self.load_instrument()
        self.client.register_callback(self._message_handler)
        self.client.start()
        self._ping_thread.start()
        time.sleep(2)
        self.subscribe()

    def connect(self):
        pass

    def send_ping(self):
        while True:
            self.client.send({"op": "ping"})
            time.sleep(10)


if __name__ == '__main__':
    obj = BybitWSCollector()
    obj.run()
