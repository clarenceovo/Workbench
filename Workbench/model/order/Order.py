from dataclasses import dataclass, field
from Workbench.model.OrderEnum import OrderSide , OrderType
class Order:
    exchange : str
    symbol: str
    client_order_id: str
    price: float
    quantity: float #must be positive
    side: OrderSide
    order_type: OrderType
    deal_ts : int

    def to_json(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "client_order_id": self.client_order_id,
            "price": self.price,
            "quantity": self.quantity,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "deal_ts": self.deal_ts
        }

