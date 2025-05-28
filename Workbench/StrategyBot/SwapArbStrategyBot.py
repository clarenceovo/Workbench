from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.transport.redis_client import RedisClient
from Workbench.config.ConnectionConstant import REDIS_HOST , REDIS_PORT, REDIS_DB , REDIS_PASSWORD
from Workbench.StrategyBot.BaseBot import BaseBot
class SwapArbStrategyBot(BaseBot):
    def __init__(self, redis_conn: RedisClient, bot_id:str):
        super().__init__(redis_conn, bot_id)
        self.logger.info("Initializing SwapArbStrategyBot...")
        self.logger.info(f'SwapArbStrategyBot initialized with bot_id: {bot_id}.Config: {self.bot_config}')


if __name__ == "__main__":
    # Example usage
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    bot = SwapArbStrategyBot(client, bot_id="ALT1")
