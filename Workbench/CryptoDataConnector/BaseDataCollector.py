from abc import ABC, abstractmethod

class BaseDataCollector(ABC):
    def __init__(self, name):
        super().__init__(name)

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

