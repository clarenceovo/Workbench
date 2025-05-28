from abc import ABC, abstractmethod
import logging
class CryptoTraderBase(ABC):
    """
    Base class for CryptoTrader, providing common functionality.
    """

    def __init__(self, name: str, api_key: str = None, api_secret: str = None):
        self.create_ts = None
        self.exchange = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logging.getLogger(name)

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
    def get_account_status(self):
        pass

    @abstractmethod
    def get_account_balance(self):
        """
        Abstract method to get the account status.
        Must be implemented by subclasses.
        """
        pass