from enum import Enum

class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
    STOP_LOSS = 3
    TAKE_PROFIT = 4
    TRAILING_STOP = 5

class OrderDirection(Enum):
    BUY = 1
    SELL = 2

class OrderStatus(Enum):
    PENDING = 1
    FILLED = 2
    CANCELLED = 3
    REJECTED = 4
    PARTIALLY_FILLED = 5

class OrderSide(Enum):
    LONG = 1
    SHORT = 2

