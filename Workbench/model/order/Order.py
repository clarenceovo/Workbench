from dataclasses import dataclass, field
from typing import Optional

from Workbench.model.OrderEnum import OrderSide , OrderType,OrderDirection
from Workbench.util.OrderUtil import get_uuid


class Order:
    exchange : str
    symbol: str
    client_order_id: str
    price: float
    quantity: float #must be positive
    side: OrderSide
    order_type: OrderType
    direction: str
    deal_ts : int
    is_completed: bool = field(default=False, init=False)
    client_order_id: str = get_uuid()
    order_ref_id: Optional[str] = field(default_factory=None, init=False)


    def to_json(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "client_order_id": self.client_order_id,
            "price": self.price,
            "quantity": self.quantity,
            "side": self.side.value,
            "direction": self.direction,
            "order_type": self.order_type.value,
            "deal_ts": self.deal_ts
        }

    def finish(self,order_ref_id: Optional[str] = None):
        """
        Mark the order as completed.
        """
        self.is_completed = True
        self.order_ref_id = order_ref_id
