import json
import threading
import time
import os

from Workbench.model.OrderEnum import OrderType, OrderDirection
from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.model.order.Order import Order
from Workbench.util.PsUtil import kill_process
from Workbench.transport.redis_client import RedisClient
from Workbench.config.ConnectionConstant import REDIS_HOST , REDIS_PORT, REDIS_DB , REDIS_PASSWORD , QUEST_HOST , QUEST_PORT
from Workbench.StrategyBot.BaseBot import BaseBot
from Workbench.util.TimeUtil import get_timestamp, get_utc_now_ms
from Workbench.util.OrderUtil import trim_trailing_zeros
from Workbench.CryptoTrader.BinanceCryptoTrader import BinanceCryptoTrader
from Workbench.CryptoTrader.HTXCryptoTrader import HTXCryptoTrader


class SwapArbStrategyBot(BaseBot):
    bot_config : SwapArbConfig
    def __init__(self, redis_conn: RedisClient, bot_id:str):
        self.publish_mode = False
        super().__init__(redis_conn, bot_id)
        self.logger.info("Initializing SwapArbStrategyBot...")
        self.event_dict = {}
        self.last_trade_ts = {}
        self.init_market_collector(self.bot_config.exchange_a)
        self.init_market_collector(self.bot_config.exchange_b)
        self.trader_client_a = BinanceCryptoTrader(name=self.bot_config.exchange_a)
        self.trader_client_b = HTXCryptoTrader(name=self.bot_config.exchange_b)
        self.position_thread = None
        self.spread_book = {}
        self.working_pair = []
        self.position_count = 0
        self.init_bot()

    def __publish_position(self):
        KEY = f'StrategyBot:SwapArb:Position:{self.bot_id}'
        SPREAD_BOOK_KEY = f'StrategyBot:SwapArb:SpreadBook:{self.bot_id}'
        while True:
            book = {"ts": get_utc_now_ms()}
            for position in self.trader_client_a.position_book.positions.values():
                book[position.symbol] = position.to_dict()
            for position in self.trader_client_b.position_book.positions.values():
                book[position.symbol] = position.to_dict()
            self.redis_conn.set(KEY, json.dumps(book, indent=4))
            self.redis_conn.set(SPREAD_BOOK_KEY, json.dumps(self.spread_book, indent=4))
            time.sleep(1)

    def init_bot(self):
        for key, exchange in self.market_connector.items():
            self.logger.info(f'Initializing exchange: {key}')
            exchange.run()
        self.subscribe_market_data()
        self.position_thread = threading.Thread(target=self.__publish_position, daemon=True).start()
        time.sleep(1)
        self.run()

    def subscribe_market_data(self):
        if self.bot_config.exchange_a not in self.market_connector:
            raise ValueError(f"Exchange {self.bot_config.exchange_a} is not initialized.")
        if self.bot_config.exchange_b not in self.market_connector:
            raise ValueError(f"Exchange {self.bot_config.exchange_b} is not initialized.")

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

    def cal_quantity(self, symbol: str, price: float, notional: float) -> (float, float):
        raw_qty = notional / price
        a_qty = self.trader_client_a.get_order_size(symbol, raw_qty)
        b_qty = self.trader_client_b.get_order_size(symbol, raw_qty)
        return (trim_trailing_zeros(a_qty), trim_trailing_zeros(b_qty))

    def cal(self):
        self.check_connection()
        bbo_a = self.market_connector[self.bot_config.exchange_a].tickerbook
        bbo_b = self.market_connector[self.bot_config.exchange_b].tickerbook

        for symbol in bbo_a.keys():
            if symbol not in bbo_b:
                continue

            bid_a = bbo_a[symbol].bid_price
            ask_b = bbo_b[symbol].ask_price
            bid_b = bbo_b[symbol].bid_price
            ask_a = bbo_a[symbol].ask_price

            spread_bp = (bid_a - ask_b) / ask_b * 10000 if ask_b != 0 else 0
            self.spread_book[symbol] = spread_bp

            if abs(spread_bp) > self.bot_config.upper_bound_entry_bp:
                now = get_timestamp()
                cooldown_ms = 2000

                if now - self.last_trade_ts.get(symbol, 0) < cooldown_ms:
                    self.logger.info(f"Trade cooldown active for {symbol}, skipping trade.")
                    continue

                self.last_trade_ts[symbol] = now

                if now - self.event_dict.get(symbol, 0) > 1000 or symbol not in self.event_dict:
                    self.logger.info(f"Arbitrage opportunity found for {symbol}: "
                                     f"Bid on {self.bot_config.exchange_a}: {bid_a}, "
                                     f"Ask on {self.bot_config.exchange_b}: {ask_b}, "
                                     f"Spread: {spread_bp:.2f}")
                    self.event_dict[symbol] = now

                if self.position_count > self.bot_config.max_position:
                    continue
                if not self.bot_config.is_trading:
                    continue

                order_qty = self.cal_quantity(symbol, bid_a, 100)
                self.logger.info(f"Calculated order quantity for {symbol}: {order_qty}")

                if symbol in self.working_pair:
                    self.logger.info(f"Already working on {symbol}, skipping...")
                    continue

                self.working_pair.append(symbol)

                try:
                    if spread_bp > 0:
                        self.logger.info(f"Placing orders for {symbol} - Buy on {self.bot_config.exchange_a} at {bid_a}, "
                                         f"Sell on {self.bot_config.exchange_b} at {ask_b}")
                        order_a = Order(
                            exchange="Binance",
                            symbol=symbol,
                            direction=OrderDirection.SELL,
                            order_type=OrderType.MARKET,
                            quantity=order_qty[0],
                        )
                        order_b = Order(
                            exchange="HTX",
                            symbol=symbol.replace("USDT", "-USDT"),
                            direction=OrderDirection.BUY,
                            order_type=OrderType.MARKET,
                            quantity=order_qty[1],
                        )
                    else:
                        self.logger.info(f"Placing orders for {symbol} - Sell on {self.bot_config.exchange_a} at {ask_a}, "
                                         f"Buy on {self.bot_config.exchange_b} at {bid_b}")
                        order_a = Order(
                            exchange="Binance",
                            symbol=symbol,
                            direction=OrderDirection.BUY,
                            order_type=OrderType.MARKET,
                            quantity=order_qty[0],
                            is_market_order=True
                        )
                        order_b = Order(
                            exchange="HTX",
                            symbol=symbol.replace("USDT", "-USDT"),
                            direction=OrderDirection.SELL,
                            order_type=OrderType.MARKET,
                            quantity=order_qty[1],
                        )

                    self.trader_client_a.ws_place_order(order_a)
                    self.trader_client_b.ws_place_order(order_b)
                    self.position_count += 1
                finally:
                    self.working_pair.remove(symbol)
            else:
                pass


if __name__ == "__main__":
    import sys
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    args = sys.argv[1:]
    bot_id = args[0] if len(args) > 0 else "ALT1"
    bot = SwapArbStrategyBot(client, bot_id=bot_id)