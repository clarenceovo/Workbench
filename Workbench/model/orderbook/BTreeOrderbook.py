from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, OrderedDict
import bisect


class Side(str, Enum):
    BID = "Bid"
    ASK = "Ask"


@dataclass
class Order:
    timestamp: int
    price: float
    qty: float
    side: Side


class BTreeOrderbook:
    def __init__(self, instrument: str):
        self.instrument = instrument
        self.bids = OrderedDict()  # descending prices
        self.asks = OrderedDict()  # ascending prices

    def insert_order(self, order: Order):
        book = self.bids if order.side == Side.BID else self.asks
        if order.qty == 0.0:
            book.pop(order.price, None)
        else:
            book[order.price] = [order]  # overwrite existing

        self._sort_book(order.side)

    def _sort_book(self, side: Side):
        book = self.bids if side == Side.BID else self.asks
        reverse = side == Side.BID
        sorted_items = sorted(book.items(), reverse=reverse)
        book.clear()
        book.update(sorted_items)

    def best_bid(self):
        return next(iter(self.bids.values()), [None])[0]

    def best_ask(self):
        return next(iter(self.asks.values()), [None])[0]

    def get_bo_spread_in_bp(self):
        bid = self.best_bid()
        ask = self.best_ask()
        if bid and ask:
            mid = (bid.price + ask.price) / 2.0
            return (ask.price - bid.price) / mid * 10_000.0 if mid > 0 else None
        return None

    def get_depth_by_pct(self, pct: float):
        bid = self.best_bid()
        ask = self.best_ask()
        if not bid or not ask:
            return 0.0, 0.0

        mid = (bid.price + ask.price) / 2.0
        threshold = mid * (pct / 100.0)
        bid_cutoff = mid - threshold
        ask_cutoff = mid + threshold

        bid_depth = sum(
            order.qty
            for price, orders in self.bids.items()
            if price >= bid_cutoff
            for order in orders
        )
        ask_depth = sum(
            order.qty
            for price, orders in self.asks.items()
            if price <= ask_cutoff
            for order in orders
        )
        return bid_depth, ask_depth

    def clear_bids(self):
        self.bids.clear()

    def clear_asks(self):
        self.asks.clear()


class OrderbookCollection:
    orderbooks: dict[str, BTreeOrderbook]

    def __init__(self, exchange: str):
        self.exchange = exchange
        self.orderbooks = {}

    def add_orderbook(self, instrument: str):
        if instrument not in self.orderbooks:
            self.orderbooks[instrument] = BTreeOrderbook(instrument)

    def get_orderbook(self, instrument: str):
        return self.orderbooks.get(instrument)
