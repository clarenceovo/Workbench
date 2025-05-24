from dataclasses import dataclass

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