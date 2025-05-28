from Workbench.model.order.Order import Order
from dataclasses import dataclass , fields
from Workbench.util.OrderUtil import get_uuid

@dataclass
class SwapOrder:
    """
    A class to represent a swap order.
    """
    exchange: str
    symbol: str
    long_leg: Order
    short_leg: Order
    long_price: float
    short_price: float

    def get_basis_bp(self) -> float:
        """
        Calculate the basis in basis points.
        """
        if self.long_leg.price == 0:
            return 0.0
        return (self.short_leg.price - self.long_leg.price) / self.long_leg.price * 10000

    def to_json(self):
        """
        Convert the swap order to a JSON serializable dictionary.
        """
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "long_leg": self.long_leg.to_json(),
            "short_leg": self.short_leg.to_json(),
            "long_price": self.long_price,
            "short_price": self.short_price,
            "basis_bp": self.get_basis_bp()
        }

