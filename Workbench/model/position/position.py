from Workbench.model.OrderEnum import OrderSide, OrderType, OrderDirection
from Workbench.util.OrderUtil import get_uuid
from Workbench.util.TimeUtil import get_utc_now_ms

class Position:
    exchange: str
    symbol: str
    quantity: float  # must be positive
    order_type: OrderType
    direction: OrderDirection
