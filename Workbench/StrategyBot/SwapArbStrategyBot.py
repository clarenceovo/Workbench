import json
import threading
from threading import Lock
import time
import os

from Workbench.model.OrderEnum import OrderType, OrderDirection
from Workbench.model.config.SwapArbConfig import SwapArbConfig
from Workbench.model.order.Order import Order
from Workbench.util.PsUtil import kill_process
from Workbench.transport.redis_client import RedisClient
from Workbench.model.position.SwapPosition import SwapPosition , SwapPositionBook
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
        self.entry_lock = Lock()
        self.unwind_lock = Lock()
        self.swap_position_book = SwapPositionBook()
        self.working_pair = []
        self.unwinding_pair = []
        self.position_count = 0
        self.init_bot()

    def __publish_position(self):
        KEY = f'StrategyBot:SwapArb:Position:{self.bot_id}'
        SPREAD_BOOK_KEY = f'StrategyBot:SwapArb:SpreadBook:{self.bot_id}'
        self.reload_config()
        while True:
            book = {"ts": get_utc_now_ms(),self.bot_config.exchange_a: {}, self.bot_config.exchange_b: {}}
            for position in self.trader_client_a.position_book.positions.values():
                book[self.bot_config.exchange_a][position.symbol.replace('-','')] = position
            for position in self.trader_client_b.position_book.positions.values():
                book[self.bot_config.exchange_b][position.symbol.replace('-','')] = position
            self._check_swap_position(book)
            #convert positions to dict
            for symbol, position in book[self.bot_config.exchange_a].items():
                book[self.bot_config.exchange_a][symbol] = position.to_dict()
            for symbol, position in book[self.bot_config.exchange_b].items():
                book[self.bot_config.exchange_b][symbol] = position.to_dict()
            self.redis_conn.set(KEY, json.dumps(book, indent=4))
            self.redis_conn.set(SPREAD_BOOK_KEY, json.dumps(self.spread_book, indent=4))

            time.sleep(1)

    def _check_swap_position(self, book):
        #check the common pairs in both exchanges
        common_symbols = set(book[self.bot_config.exchange_a].keys()).intersection(set(book[self.bot_config.exchange_b].keys()))
        for symbol in common_symbols:
            position_a = book[self.bot_config.exchange_a][symbol]
            position_b = book[self.bot_config.exchange_b][symbol.replace("-","")]
            if position_a.quantity != 0 or position_b.quantity != 0:
                if position_a.direction == OrderDirection.BUY and position_b.direction == OrderDirection.SELL:
                    long_leg = position_a
                    short_leg = position_b
                elif position_a.direction == OrderDirection.SELL and position_b.direction == OrderDirection.BUY:
                    long_leg = position_b
                    short_leg = position_a
                else:
                    self.logger.error(f"Invalid position directions for symbol {symbol}: "
                                      f"position_a.direction={position_a.direction}, position_b.direction={position_b.direction}")
                    return

                swap_position = SwapPosition(
                    symbol=symbol,
                    long_leg=long_leg,
                    short_leg=short_leg
                )
                self.swap_position_book.add_position(swap_position)


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
                time.sleep(0.001)
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

    def _check_position_unwind(self):
        if self.bot_config.is_trading is False:
            #self.logger.info("Trading is disabled, skipping position unwind check.")
            return
        position_entry = self.swap_position_book.position_prices
        for symbol, price in position_entry.items():
            if symbol not in self.spread_book.keys():
                continue
            current_spread = self.spread_book[symbol]
            position_spread = price
            spread = current_spread - position_spread
            if (abs(spread) > self.bot_config.exit_bp) and symbol not in self.unwinding_pair:
                self.logger.info(f"Unwinding position for {symbol} due to low spread: {spread:.2f}")
                self.unwinding_pair.append(symbol)
                with self.unwind_lock:
                    position_a = self.trader_client_a.position_book.get_position(symbol)
                    position_b = self.trader_client_b.position_book.get_position(symbol.replace("USDT", "-USDT"))
                    if position_a and position_b:
                        order_a = Order(
                            exchange=self.bot_config.exchange_a,
                            symbol=position_a.symbol,
                            direction=OrderDirection.SELL if position_a.direction == OrderDirection.BUY else OrderDirection.BUY,
                            order_type=OrderType.MARKET,
                            quantity=abs(position_a.quantity),
                            is_market_order=True,
                            reduce_only=True,
                            is_close_order=True
                        )
                        order_b = Order(
                            exchange=self.bot_config.exchange_b,
                            symbol=position_b.symbol,
                            direction=OrderDirection.SELL if position_b.direction == OrderDirection.BUY else OrderDirection.BUY,
                            order_type=OrderType.MARKET,
                            quantity=abs(position_b.quantity),
                            reduce_only=True,
                            is_close_order=True
                        )
                        print(f'Unwinding orders:{symbol}')
                        self.trader_client_a.ws_place_order(order_a)
                        self.trader_client_b.ws_place_order(order_b)


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
            self._check_position_unwind()
            if abs(spread_bp) > self.bot_config.upper_bound_entry_bp:
                now = get_timestamp()
                cooldown_ms = 2000

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
                #Hot logic
                if now - self.last_trade_ts.get(symbol, 0) < cooldown_ms:
                    self.logger.info(f"Trade cooldown active for {symbol}, skipping trade.")
                    continue
                with self.entry_lock:

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
                                exchange=self.bot_config.exchange_a,
                                symbol=symbol,
                                direction=OrderDirection.SELL,
                                order_type=OrderType.MARKET,
                                quantity=order_qty[0],
                            )
                            order_b = Order(
                                exchange=self.bot_config.exchange_b,
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