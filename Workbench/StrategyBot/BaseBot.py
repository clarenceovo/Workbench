from Workbench.transport.redis_client import RedisClient
from Workbench.util.TimeUtil import get_utc_now_ms
from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.CryptoDataConnector import *
from Workbench.CryptoWebsocketDataCollector import *
import json
import logging
class BaseBot(object):
    KEY = "StrategyBot:SwapArb:{}"  # Placeholder for the Redis key format
    def __init__(self, redis_conn: RedisClient, bot_id: str,messenger=None):
        self.logger = logging.getLogger(type(self).__name__)
        self.redis_conn = redis_conn
        self.bot_id = bot_id
        self.is_active = True
        self.last_update_config = None
        self.messenger = messenger  # Optional messenger for alerts
        self.last_alert = None
        self.last_ts = get_utc_now_ms()
        self.bot_config = None
        self.reload_config()
        self.market_connector = {}

    def reload_config(self):
        """
        Reload the configuration from Redis.
        This method should be implemented by subclasses.
        """
        if self.redis_conn is None:
            raise ValueError("Redis connection is not initialized.")
        if self.redis_conn.client.ping() is False:
            raise ConnectionError("Redis connection is not available.")
        KEY = "StrategyBot:SwapArb:{}".format(self.bot_id) #TODO : change the strategy name to variable
        t = self.redis_conn.client.get(KEY)
        if t is None:
            raise ValueError("Configuration not found in Redis for bot_id: {}".format(self.bot_id))

        config = json.loads(t)
        config = SwapArbConfig(**config)
        #check if the config is same as the last one
        if config == self.bot_config:
            #self.logger.info("Configuration has not changed, skipping reload.")
            return
        if self.bot_config is None:
            self.logger.info(f"Initializing configuration for bot_id: {self.bot_id}")
            self.bot_config = config
            self.last_update_config = config
        else :
            updated_fields = SwapArbConfig.get_updated_field(config,self.bot_config)
            if updated_fields:
                self.logger.info(f"Configuration updated for bot_id: {self.bot_id}, changed fields: {updated_fields}")
                self.send_message('Configuration updated for bot_id: {}, changed fields: {}'.format(self.bot_id, updated_fields))
            else:
                self.logger.info(f"No changes in configuration for bot_id: {self.bot_id}")
            self.bot_config = config
            self.last_update_config = config

    def save_config(self):
        self.logger.info("Saving configuration for bot_id: {}".format(self.bot_id))
        key = "StrategyBot:SwapArb:{}".format(self.bot_id)
        self.redis_conn.client.set(key, json.dumps(self.bot_config.to_dict(),indent=4))

    def disable_trading(self):
        if self.bot_config:
            self.bot_config.is_trading = False
            self.save_config()
            self.logger.info("Disabled trading and saved configuration for bot_id: {}".format(self.bot_id))


    def refresh_ts(self):
        """
        Refresh the last timestamp to the current UTC time in milliseconds.
        """
        self.last_ts = get_utc_now_ms()

    def init_market_collector(self,exchange_name:str):
        """
        Initialize the market data collector for the specified exchange.
        This method should be implemented by subclasses.
        :param exchange_name: The name of the exchange to collect market data from.

        set attribute `self.market_data_collector` to an instance of the market data collector.
        """
        if exchange_name == "Binance":
            self.market_connector['Binance'] = BinanceWSCollector()
        elif exchange_name == "HTX":
            self.market_connector['HTX'] = HtxWSCollector()
        elif exchange_name == "Bybit":
            self.market_connector['Bybit'] = BybitWSCollector()
        elif exchange_name == "Kucoin":
            raise ValueError("Kucoin market collector is not implemented yet.")
        else:
            raise ValueError("Unknown exchange name: {}".format(exchange_name))


    def send_message(self, message: str):
        if self.messenger is None:
            self.logger.warning("Messenger is not initialized, cannot send message.")
            return
        self.messenger.send_message(text=message)

    def init_trader(self, exchange_name:str):
        """
        Initialize the trader for the specified exchange.
        This method should be implemented by subclasses.
        :param exchange_name: The name of the exchange to trade on.
        """
        pass
