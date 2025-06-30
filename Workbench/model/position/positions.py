from typing import Optional

from Workbench.model.OrderEnum import OrderSide, OrderType, OrderDirection
from Workbench.util.OrderUtil import get_uuid
from Workbench.util.TimeUtil import get_utc_now_ms
from dataclasses import dataclass


@dataclass
class Position:
    exchange: str
    symbol: str
    quantity: float  # must be positive
    notional: float
    entryPrice: float
    markPrice: float
    lastUpdate_ts: int
    order_type: str
    direction: OrderDirection
    contract_size: Optional[float] = 1  # Optional contract size, if applicable

    @property
    def pnl(self):
        """
        Calculate the profit and loss of the position.
        :return: PnL value.
        """
        return round((self.markPrice - self.entryPrice) * self.quantity * self.contract_size,3)

    @staticmethod
    def from_binance_position(data: dict):
        return Position(
            exchange="Binance",
            symbol=data["symbol"],
            quantity=float(data["positionAmt"]),
            notional=float(data["notional"]),
            entryPrice=float(data["entryPrice"]),
            markPrice=float(data["markPrice"]),
            lastUpdate_ts=int(data["updateTime"]),
            order_type= data["marginType"],
            direction=OrderDirection.BUY if float(data["positionAmt"]) > 0 else OrderDirection.SELL
        )

    @staticmethod
    def from_htx_position(data: dict):
        """
        Converts HTX position data into a Position object.
        :param data: Dictionary containing HTX position details.
        :return: Position object.
        """
        return Position(
            exchange="HTX",
            symbol=data["contract_code"],
            quantity=float(data["available"]),
            notional=float(data["available"])*data.get('contract_size')*float(data['last_price']),
            entryPrice=float(data["cost_open"]),
            markPrice=float(data["last_price"]),
            lastUpdate_ts=get_utc_now_ms(),  # HTX data does not provide a timestamp for updates
            order_type="cross",
            direction=OrderDirection.BUY if data["direction"] == "buy" else OrderDirection.SELL,
            contract_size=float(data.get("contract_size", 1.0))  # Default to 1 if not provided
        )

    def to_dict(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "notional": self.notional,
            "entryPrice": self.entryPrice,
            "markPrice": self.markPrice,
            "lastUpdate_ts": self.lastUpdate_ts,
            "order_type": self.order_type,
            "direction": self.direction.value,
            "pnl": self.pnl
        }

    def __str__(self):
        return (f"Position(exchange={self.exchange}, symbol={self.symbol}, quantity={self.quantity}, "
                f"notional={self.notional}, entryPrice={self.entryPrice}, markPrice={self.markPrice}, "
                f"lastUpdate_ts={self.lastUpdate_ts}, order_type={self.order_type}, direction={self.direction})"
                f" PnL={self.pnl}")

    def __dict__(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "notional": self.notional,
            "entryPrice": self.entryPrice,
            "markPrice": self.markPrice,
            "lastUpdate_ts": self.lastUpdate_ts,
            "order_type": self.order_type,
            "direction": self.direction.value,
            "pnl": self.pnl
        }

class PositionBooks:
    def __init__(self,exchange: str):
        self.exchange = exchange
        self.last_update = get_utc_now_ms()
        self.positions = {}

    def add_position(self, position: Position):
        self.update_ts()
        key = position.symbol
        self.positions[key] = position

    def get_pnl(self, symbol: str=None) -> float:
        if symbol is None:
            return sum(self.get_pnl(s) for s in self.positions)
        else:
            position = self.get_position(symbol)
            if position:
                return (position.markPrice - position.entryPrice) * position.quantity
        return 0.0

    def update_ts(self):
        self.last_update = get_utc_now_ms()

    def get_position(self, symbol: str) -> Optional[Position]:
        return self.positions.get(symbol, None)

    def remove_position(self, symbol: str):
        if symbol in self.positions:
            _ = self.positions.pop(symbol)
        else:
            pass

    def to_dict(self):
        return {
            "exchange": self.exchange,
            "last_update": self.last_update,
            "positions": {k: v.to_dict() for k, v in self.positions.items()}
        }
