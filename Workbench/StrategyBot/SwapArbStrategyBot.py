import time
import os
from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.util.PsUtil import kill_process
from Workbench.transport.redis_client import RedisClient
from Workbench.config.ConnectionConstant import REDIS_HOST , REDIS_PORT, REDIS_DB , REDIS_PASSWORD , QUEST_HOST , QUEST_PORT
from Workbench.StrategyBot.BaseBot import BaseBot
from Workbench.util.TimeUtil import get_timestamp


class SwapArbStrategyBot(BaseBot):
    bot_config : SwapArbConfig
    def __init__(self, redis_conn: RedisClient, bot_id:str):
        #set cpu affinity to the core 1-4
        self.publish_mode = False
        super().__init__(redis_conn, bot_id)
        self.logger.info("Initializing SwapArbStrategyBot...")
        self.event_dict = {}
        #self.logger.info(f'SwapArbStrategyBot initialized with bot_id: {bot_id}.Config: {self.bot_config}')
        self.init_market_collector(self.bot_config.exchange_a)
        self.init_market_collector(self.bot_config.exchange_b)
        self.spread_book = {}
        self.init_bot()

    def init_bot(self):
        #start WS
        for key, exchange in self.market_connector.items():
            self.logger.info(f'Initializing exchange: {key}')
            exchange.run()
        self.subscribe_market_data()
        time.sleep(1)
        self.run()

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
        time.sleep(1)
        self.market_connector[self.bot_config.exchange_b].subscribe(self.bot_config.exchange_b_market_list)


    def run(self):
        while self.is_active:
            try:
                self.cal()
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in SwapArbStrategyBot: {e}")
                time.sleep(5)

    def check_connection(self):
        if self.market_connector[self.bot_config.exchange_a].client.is_running and \
                self.market_connector[self.bot_config.exchange_b].client.is_running:
            pass
        else:
            self.logger.error("One of the exchanges is not active. killing the bot...")
            kill_process()

    def cal(self):
        self.check_connection()
        #self.logger.info("Calculating swap arbitrage opportunities...")
        bbo_a = self.market_connector[self.bot_config.exchange_a].tickerbook
        bbo_b = self.market_connector[self.bot_config.exchange_b].tickerbook

        for symbol in bbo_a.keys():
            if symbol not in bbo_b.keys():
                continue
            bid_a = bbo_a[symbol].bid_price
            ask_b = bbo_b[symbol].ask_price
            bid_b = bbo_b[symbol].bid_price
            ask_a = bbo_a[symbol].ask_price

            #calcuate the spread
            spread_bp = (bid_a - ask_b) / ask_b * 10000 if ask_b != 0 else 0
            spread_bp_ask = (bid_b - ask_a) / ask_b * 10000 if ask_b != 0 else 0
            self.spread_book[symbol] = spread_bp
            if abs(spread_bp) > self.bot_config.upper_bound_entry_bp:

                if get_timestamp() - self.event_dict.get(symbol,0) > 1000 or symbol not in self.event_dict:
                    self.logger.info(f"Arbitrage opportunity found for {symbol}: "
                                     f"Bid on {self.bot_config.exchange_a}: {bid_a}, "
                                     f"Ask on {self.bot_config.exchange_b}: {ask_b}, "
                                     f"Spread: {spread_bp:.2f}")
                    self.event_dict[symbol] = get_timestamp()

                """
                1. Send order to exchange A to buy at bid price
                2. Send order to exchange B to sell at ask price
                3. Monitor the orders and ensure they are filled (if mode is market)
                4. If both orders are filled, log the profit and create SwapPosition 
                5. Update BBO and cal the SwapPosition frequently
                
                """
            else:
                pass



if __name__ == "__main__":
    # Example usage
    import sys
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    args = sys.argv[1:]
    bot_id = args[0] if len(args) > 0 else "ALT1"
    print(f"Bot ID: {bot_id}")
    bot = SwapArbStrategyBot(client, bot_id=bot_id)
