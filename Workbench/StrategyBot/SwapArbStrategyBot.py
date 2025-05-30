import time

from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.transport.redis_client import RedisClient
from Workbench.config.ConnectionConstant import REDIS_HOST , REDIS_PORT, REDIS_DB , REDIS_PASSWORD
from Workbench.StrategyBot.BaseBot import BaseBot
class SwapArbStrategyBot(BaseBot):
    bot_config : SwapArbConfig
    def __init__(self, redis_conn: RedisClient, bot_id:str):
        super().__init__(redis_conn, bot_id)
        self.logger.info("Initializing SwapArbStrategyBot...")
        self.logger.info(f'SwapArbStrategyBot initialized with bot_id: {bot_id}.Config: {self.bot_config}')
        self.init_market_collector(self.bot_config.exchange_a)
        self.init_market_collector(self.bot_config.exchange_b)
        self.init_bot()

    def init_bot(self):

        self.subscribe_market_data()
        time.sleep(1)

    def subscribe_market_data(self):
        """
        Subscribe to market data for the exchanges specified in the bot configuration.
        This method should be implemented by subclasses.
        """
        if self.bot_config.exchange_a not in self.market_connector:
            raise ValueError(f"Exchange {self.bot_config.exchange_a} is not initialized.")
        if self.bot_config.exchange_b not in self.market_connector:
            raise ValueError(f"Exchange {self.bot_config.exchange_b} is not initialized.")

        # Example subscription logic
        self.market_connector[self.bot_config.exchange_a].subscribe(self.bot_config.exchange_a_market_list)
        self.market_connector[self.bot_config.exchange_b].subscribe(self.bot_config.exchange_b_market_list)

if __name__ == "__main__":
    # Example usage
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    bot = SwapArbStrategyBot(client, bot_id="ALT1")
