from Workbench.transport.redis_client import RedisClient
from Workbench.util.TimeUtil import get_utc_now_ms
from Workbench.model.config.SwapArbConfig import SwapArbConfig
import json
import logging
class BaseBot(object):

    def __init__(self, redis_conn: RedisClient, bot_id: str):
        self.logger = logging.getLogger(type(self).__name__)
        self.redis_conn = redis_conn
        self.bot_id = bot_id
        self.is_active = True
        self.last_update_config = None
        self.last_alert = None
        self.last_ts = get_utc_now_ms()
        self.bot_config = None
        self.reload_config()

    def reload_config(self):
        """
        Reload the configuration from Redis.
        This method should be implemented by subclasses.
        """
        if self.redis_conn is None:
            raise ValueError("Redis connection is not initialized.")
        if self.redis_conn.client.ping() is False:
            raise ConnectionError("Redis connection is not available.")
        KEY = "StrategyBot:SwapArb:{}".format(self.bot_id)
        t = self.redis_conn.client.get(KEY)
        if t is None:
            raise ValueError("Configuration not found in Redis for bot_id: {}".format(self.bot_id))

        config = json.loads(t)
        config = SwapArbConfig(**config)
        self.bot_config = config

    def refresh_ts(self):
        """
        Refresh the last timestamp to the current UTC time in milliseconds.
        """
        self.last_ts = get_utc_now_ms()