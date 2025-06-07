from dataclasses import dataclass, field
from typing import Optional

from Workbench.model.OrderEnum import OrderSide , OrderType,OrderDirection
from Workbench.util.OrderUtil import get_uuid
from Workbench.util.TimeUtil import get_utc_now_ms

@dataclass
class Order:
    exchange : str
    symbol: str
    quantity: float #must be positive
    order_type: OrderType
    direction: OrderDirection
    deal_ts : int = field(default_factory= get_utc_now_ms, init=True)  # Default to 0 for market orders
    price: float = field(default=0.0)  # Default to 0.0 for market orders
    is_completed: bool = field(default=False, init=False)
    is_market_order: bool = field(default=False)
    client_order_id: str = get_uuid()
    order_ref_id: Optional[str] = None
    reduce_only: bool = False  # Default to False, can be set to True for reduce-only orders
    is_close_order: bool = False  # Default to False, can be set to True for close orders
    def to_json(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "client_order_id": self.client_order_id,
            "price": self.price,
            "quantity": self.quantity,
            "direction": self.direction,
            "order_type": self.order_type.value,
            "deal_ts": self.deal_ts
        }

    def to_htx_order(self):
        return {
            "op": "create_cross_order",
            "cid": self.client_order_id,
            "data":{
                'contract_code': self.symbol,
                'direction': self.direction.name.lower(),
                "price": self.price if self.order_type == OrderType.LIMIT else 0.0,
                "volume": self.quantity,
                "offset": "close" if self.is_close_order else "open" ,
                "lever_rate": "10",
                "order_price_type" : "limit" if self.order_type == OrderType.LIMIT else "market",
                #"reduce_only": self.reduce_only,
            }
        }

    def to_binance_order(self):
        """
        Convert the order to a format suitable for Binance.
        """
        return {
            "apiKey": self.exchange,
            "quantity": self.quantity,
            "side": "BUY" if self.direction == OrderDirection.BUY else "SELL",
            "symbol": self.symbol,
            "timestamp": int(get_utc_now_ms()),
            "type": "MARKET" if self.is_market_order else "LIMIT",
            "price": self.price if not self.is_market_order else None,
            "signature": None  # Signature will be added later
        }

    def finish(self,order_ref_id: Optional[str] = None):
        """
        Mark the order as completed.
        """
        self.is_completed = True
        self.order_ref_id = order_ref_id
