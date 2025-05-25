from dataclasses import dataclass
from Workbench.transport.QuestClient import QuestBatch
from datetime import datetime
@dataclass
class TopOfBook:
    timestamp: int
    exchange: str
    symbol: str
    bid_price: float
    bid_qty: float
    ask_price: float
    ask_qty: float

    def to_tuple(self):
        return (self.timestamp, self.exchange, self.symbol, self.bid_price, self.bid_qty, self.ask_price, self.ask_qty)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "bid_price": self.bid_price,
            "bid_qty": self.bid_qty,
            "ask_price": self.ask_price,
            "ask_qty": self.ask_qty
        }

    def to_batch(self):
        try:
            return QuestBatch(
                topic="top_of_book",
                symbol={"symbol":self.symbol, "exchange": self.exchange},
                columns={
                    "bid_price": self.bid_price,
                    "bid_qty": self.bid_qty,
                    "ask_price": self.ask_price,
                    "ask_qty": self.ask_qty
                },
                timestamp = datetime.fromtimestamp(self.timestamp/1000.0)
            )
        except Exception as e:
            print(f"Error converting TopOfBook to batch: {e}")
            return None