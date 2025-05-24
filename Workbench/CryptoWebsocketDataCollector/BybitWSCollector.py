import json
from Workbench.config.ConnectionConstant import BYBIT_FUTURES_WS_URL
from Workbench.CryptoDataConnector.BybitDataCollector import BybitDataCollector
from Workbench.CryptoWebsocketDataCollector import BaseWSCollector
from Workbench.util.TimeUtil import get_latency_ms

BYBIT_WS_TOPICS = {
    "market": {
        "orderbook": "orderbook.{symbol}",                   # Order book updates
        "public_trade": "publicTrade.{symbol}",              # Trade executions
        "ticker": "tickers.{symbol}",                        # 24h rolling stats
        "kline": "kline.{interval}.{symbol}",                # Candlestick data (1m, 5m, 1h, etc.)
        "liquidation": "liquidation.{symbol}",               # Liquidations for a symbol
        "all_liquidation": "allLiquidation",                 # All liquidations
        "insurance": "insurance",                            # Insurance fund balance
        "lt_kline": "ltKline.{interval}.{symbol}",           # Long-term kline
        "lt_ticker": "ltTicker.{symbol}",                    # Long-term ticker
        "lt_nav": "ltNav.{symbol}"                           # Leveraged Token NAV
    }
}

class BybitWSCollector(BaseWSCollector):
    """
    Bybit WebSocket data collector.
    """

    def __init__(self, url=BYBIT_FUTURES_WS_URL):
        super().__init__("BybitWS", url)
        self.data_collector = BybitDataCollector()
        self.load_instrument()

    def load_instrument(self):
        self.instrument_info = self.data_collector.get_contract_details()

    def disconnect(self):
        pass

    def subscribe(self):
        target_inst = ["btcusdt", "ethusdt", "pendleusdt", "solvusdt"]  # TODO: load from Redis
        topic_template = BYBIT_WS_TOPICS["market"]["ticker"]
        for inst in target_inst:
            topic = topic_template.format(symbol=inst)
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

    def _handler_book_ticker(self, msg):
        self.logger.info("Latency: %s", get_latency_ms(msg.get("ts", 0)))
        self.logger.info("Book ticker received: %s", msg)

    def _message_handler(self, raw_msg):
        msg = json.loads(raw_msg)

        if "topic" in msg and "bookTicker" in msg["topic"]:
            for data in msg.get("data", []):
                self._handler_book_ticker(data)

    def run(self):
        self.load_instrument()
        self.client.register_callback(self._message_handler)
        self.subscribe()
        self.client.start()

    def connect(self):
        pass



if __name__ == '__main__':
    obj = BybitWSCollector()
    obj.run()