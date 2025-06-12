from Workbench.model.position.positions import Position
from dataclasses import dataclass

from Workbench.util.TimeUtil import get_utc_now_ms


@dataclass
class SwapPosition:
    """
    Represents a swap position in a trading system.
    This class is used to manage the details of a swap position, including its ID, type, and associated trade ID.
    """
    symbol : str
    long_leg : Position
    short_leg : Position

    @property
    def price(self):
        """
        Calculate the price difference of the swap position.
        Calculate the price in basis points.
        """
        if self.long_leg and self.short_leg:
            price_diff = self.short_leg.entryPrice - self.long_leg.entryPrice
            basis_points = (price_diff / self.long_leg.entryPrice) * 10000
            return basis_points
        return 0.0

    def __repr__(self):
        return f'SwapPosition(long_leg={self.long_leg},\n short_leg={self.short_leg})'

class SwapPositionBook:
    """
    A class to manage a collection of swap positions.
    This class allows adding, removing, and retrieving swap positions by their symbol.
    """
    def __init__(self):
        self.positions = {}
        self.last_ts = get_utc_now_ms()

    def add_position(self, position: SwapPosition):
        self.last_ts = get_utc_now_ms()
        self.positions[position.symbol] = position

    def get_position(self, symbol: str) -> SwapPosition:
        return self.positions.get(symbol)

    def remove_position(self, symbol: str):
        self.last_ts = get_utc_now_ms()
        if symbol in self.positions:
            del self.positions[symbol]

    @property
    def position_symbols(self):
        return list(self.positions.keys())

    @property
    def position_prices(self):
        return {symbol: position.price for symbol, position in self.positions.items()}

    def to_json(self):
        return {
            "positions": {symbol: {
                "long_leg": self.positions[symbol].long_leg.to_dict(),
                "short_leg": self.positions[symbol].short_leg.to_dict()
            } for symbol in self.positions}
        }