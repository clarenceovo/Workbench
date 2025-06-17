from abc import ABC, abstractmethod
from requests import Session
class BaseDataCollector(ABC):
    def __init__(self, name):
        self.name = name
        self.session = Session()

    @abstractmethod
    def get_kline(self):
        pass

    @abstractmethod
    def get_instrument(self):
        pass

    @abstractmethod
    def get_contract_details(self):
        pass

    @abstractmethod
    def get_open_interest(self):
        pass

    @abstractmethod
    def get_funding(self):
        pass

    @abstractmethod
    def get_time(self):
        pass

    @abstractmethod
    def get_depth(self):
        pass
