from abc import ABC, abstractmethod

class CryptoTraderBase(ABC):
    """
    Base class for CryptoTrader, providing common functionality.
    """

    def __init__(self, name: str):
        self.create_ts = None
        self.exchange = name

    @abstractmethod
    def place_order(self, order):
        """
        Abstract method to place an order.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def load_position(self, symbol: str):
        """
        Abstract method to get the position for a given symbol.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def