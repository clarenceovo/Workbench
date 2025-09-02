import abc
import pandas as pd
import logging

import redis

from Workbench.config.ConnectionConstant import *
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.transport.redis_client import RedisClient


class BaseMarketDataCollector(abc.ABC):
    def __init__(self, exchange_name,data_collector):
        self._logger = logging.getLogger(__name__)
        self.name = exchange_name
        self.client = QuestDBClient(host=CLARENCE_QUEST_HOST,
                                    port=9009,
                                    read_only=True)
        self.redis_client = RedisClient(host=CLARENCE_REDIS_HOST,
                                        port=CLARENCE_REDIS_PORT,
                                        db=CLARENCE_REDIS_DB,
                                        password=CLARENCE_REDIS_PASSWORD)
        self.data_collector = data_collector

    @abc.abstractmethod
    def init_client(self):
        """
        Initialize API client (exchange SDK, requests session, etc.)
        Should be implemented by subclasses.
        """
        pass

    @abc.abstractmethod
    def fetch_data(self, symbol):
        pass

    @abc.abstractmethod
    def save_db(self, df: pd.DataFrame, tbl: str, symbol):
        pass
