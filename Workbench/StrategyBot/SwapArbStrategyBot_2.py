from Workbench.StrategyBot.SwapArbStrategyBot import SwapArbStrategyBot
from Workbench.transport.redis_client import RedisClient
from Workbench.config.ConnectionConstant import REDIS_HOST , REDIS_PORT, REDIS_DB , REDIS_PASSWORD , QUEST_HOST , QUEST_PORT
from Workbench.transport.telegram_postman import TelegramPostman



if __name__ == "__main__":
    import sys
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    tg = TelegramPostman()
    args = sys.argv[1:]
    print(f'Args: {args}')
    bot_id = args[0] if len(args) > 0 else "ALT2"
    bot = SwapArbStrategyBot(client,messenger=tg, bot_id=bot_id)