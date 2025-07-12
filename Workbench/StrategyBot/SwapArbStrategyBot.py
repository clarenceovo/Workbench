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
from Workbench.util.TimeUtil import get_timestamp, get_utc_now_ms, get_now_hkt_string
from Workbench.util.OrderUtil import trim_trailing_zeros
from Workbench.CryptoTrader.BinanceCryptoTrader import BinanceCryptoTrader
from Workbench.CryptoTrader.HTXCryptoTrader import HTXCryptoTrader
from Workbench.transport.telegram_postman import TelegramPostman


class SwapArbStrategyBot(BaseBot):
    bot_config : SwapArbConfig
    def __init__(self, redis_conn: RedisClient,messenger, bot_id:str):
        self.publish_mode = False
        super().__init__(redis_conn, bot_id,messenger)
        self.logger.info("Initializing SwapArbStrategyBot...")
        self.event_dict = {}
        self.last_trade_ts = {}
        self.init_market_collector(self.bot_config.exchange_a)
        self.init_market_collector(self.bot_config.exchange_b)
        self.trader_client_a = BinanceCryptoTrader(name=self.bot_config.exchange_a)
        self.trader_client_b = HTXCryptoTrader(name=self.bot_config.exchange_b)
        try:
            self.logger.info(f'A balance :{self.trader_client_a.get_account_token_balance()}')
            self.logger.info(f'B:{self.trader_client_b.get_account_token_balance()}')
        except:
            pass
        self.target_pair = set(self.bot_config.exchange_a_market_list).intersection(set(self.bot_config.exchange_b_market_list))
        self.target_pair = [item.replace('-', '') for item in self.target_pair]
        self.logger.info(f'Target:{self.target_pair}')
        self.position_thread = None
        self.spread_book = {}
        self.entry_lock = Lock()
        self.unwind_lock = Lock()
        self.swap_position_book = SwapPositionBook()
        self.working_pair = []
        self.unwinding_pair = []
        self.last_unwind_ts = {}
        self._unwind_lock = Lock()
        self.position_count = 0
        self.send_message("Initialized SwapArbStrategyBot with ID: {} @ {}".format(self.bot_id, get_utc_now_ms()))
        self.init_bot()




    def __publish_position(self):
        KEY = f'StrategyBot:SwapArb:Position:{self.bot_id}'
        SPREAD_BOOK_KEY = f'StrategyBot:SwapArb:SpreadBook:{self.bot_id}'
        while True:
            self.reload_config()
            book = {"ts": get_utc_now_ms(),self.bot_config.exchange_a: {}, self.bot_config.exchange_b: {}}
            for position in self.trader_client_a.position_book.positions.values():
                if position.symbol.replace('-', '') not in self.target_pair:
                    continue
                book[self.bot_config.exchange_a][position.symbol.replace('-','')] = position
            for position in self.trader_client_b.position_book.positions.values():
                if position.symbol.replace('-', '') not in self.target_pair:
                    continue
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
            if position_a.quantity == 0 or position_b.quantity == 0:
                continue

            # New: enforce directions are strictly opposite
            if position_a.direction == position_b.direction:
                #self.logger.warning(
                #    f"Position direction mismatch for {symbol}: {position_a.direction} vs {position_b.direction}")
                continue
            #if notional difference of both positions are 50% different, skip
            if position_a.direction == OrderDirection.BUY and position_b.direction == OrderDirection.SELL:
                long_leg = position_a
                short_leg = position_b
            elif position_a.direction == OrderDirection.SELL and position_b.direction == OrderDirection.BUY:
                long_leg = position_b
                short_leg = position_a
            else:
                #self.logger.warning(f"Position direction mismatch for {symbol}: {position_a.direction} vs {position_b.direction}")
                continue
            swap_position = SwapPosition(
                symbol=symbol,
                long_leg=long_leg,
                short_leg=short_leg
            )
            self.swap_position_book.add_position(swap_position)
        self.redis_conn.set(f'StrategyBot:SwapArb:SwapPositionBook:{self.bot_id}',
                            json.dumps(self.swap_position_book.to_json(), indent=4))

    def init_bot(self):
        for key, exchange in self.market_connector.items():
            self.logger.info(f'Initializing exchange: {key}')
            exchange.run()
        self.subscribe_market_data()
        self.position_thread = threading.Thread(target=self.__publish_position, daemon=True).start()
        time.sleep(0.5)
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
        self.logger.info('Sleep 10 seconds to load all position data')
        time.sleep(10)
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
            self.disable_trading()
            kill_process()
        if (self.trader_client_a.ws_trade_client.is_running and self.trader_client_b.ws_trade_client.is_running):
            pass
        else:
            self.logger.error("One of the traders is not active. killing the bot... and disable trading")
            self.disable_trading()
            kill_process()

    def _check_position_unwind(self):
        now_ms = get_utc_now_ms()
        if self.bot_config.is_trading is False:
            return

        position_entry = self.swap_position_book.position_prices
        for symbol, price in position_entry.items():
            if symbol not in self.spread_book:
                continue
            current_spread = self.spread_book[symbol]
            position_spread = price
            spread = current_spread - position_spread

            # 1. Skip if symbol recently unwinded
            if symbol in self.last_unwind_ts and now_ms - self.last_unwind_ts.get(symbol,0) < 100000:
                continue

            # 2. Proceed if spread trigger met
            if abs(spread) > self.bot_config.exit_bp and abs(spread) < 5000:
                self.logger.info(
                    f"Checking position unwind for {symbol} | Position Spread: {position_spread:.2f} | Current Spread: {current_spread:.2f} @ {get_now_hkt_string()}")

                with self.unwind_lock:
                    if symbol not in self.swap_position_book.positions.keys():
                        continue
                    swap = self.swap_position_book.positions[symbol]
                    position_long = swap.long_leg
                    position_short = swap.short_leg

                    del self.swap_position_book.positions[symbol]
                    if position_long and position_short:

                        order_long = Order(
                            exchange=position_long.exchange,
                            symbol=position_long.symbol,
                            direction=OrderDirection.SELL,
                            order_type=OrderType.MARKET,
                            quantity=abs(position_long.quantity),
                            is_market_order=True,
                            reduce_only=True,
                            is_close_order=True,

                        )
                        order_short = Order(
                            exchange=position_short.exchange,
                            symbol=position_short.symbol,
                            direction=OrderDirection.BUY,
                            order_type=OrderType.MARKET,
                            quantity=abs(position_short.quantity),
                            reduce_only=True,
                            is_close_order=True,
                            is_market_order=True,
                        )
                        if order_long.exchange == self.trader_client_a.exchange:
                            self.trader_client_a.ws_place_order(order_long)
                        else:
                            self.trader_client_b.ws_place_order(order_long)

                        if order_short.exchange == self.trader_client_a.exchange:
                            self.trader_client_a.ws_place_order(order_short)
                        else:
                            self.trader_client_b.ws_place_order(order_short)

                        self.send_message(
                            f"Unwinded position for {symbol} | Position Spread: {position_spread:.2f} | Current Spread: {current_spread:.2f} @ {get_now_hkt_string()}")
                        self.logger.info(f"Unwind position for {symbol} @ {get_now_hkt_string()}")
                        time.sleep(5)
                        self._clean_position_book(symbol)
                        self.last_unwind_ts[symbol] = now_ms


    def _clean_position_book(self,symbol):
        try:
            self.swap_position_book.remove_position(symbol)
            self.trader_client_a.position_book.remove_position(symbol)
            self.trader_client_b.position_book.remove_position(symbol)
        except Exception as e:
            self.logger.error(f"Error in SwapArbStrategyBot: {e}")
        finally:
            self.logger.info(f"Cleaned position book for {symbol}")




    def cal_quantity(self, symbol: str, price: float, notional: float) -> (float, float):
        a_qty = self.trader_client_a.get_order_size(symbol, notional,price)
        b_qty = self.trader_client_b.get_order_size(symbol, notional,price)
        return (float(trim_trailing_zeros(a_qty)), float(trim_trailing_zeros(b_qty)))

    def cal(self):
        self.check_connection()
        bbo_a = self.market_connector[self.bot_config.exchange_a].tickerbook
        bbo_b = self.market_connector[self.bot_config.exchange_b].tickerbook
        self._check_position_unwind()
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

                if now - self.event_dict.get(symbol, 0) > 10 or symbol not in self.event_dict:
                    bo_spread_a = (ask_a-bid_a)/ask_a * 10000
                    bo_spread_b = (ask_b-bid_b)/ask_b * 10000
                    self.logger.info(f"Arbitrage opportunity found for {symbol}: "
                                     f"Bid on {self.bot_config.exchange_a}: {bid_a}, "
                                     f"Ask on {self.bot_config.exchange_b}: {ask_b}, "
                                     f"Spread: {spread_bp:.2f}\n"
                                     f'A BO:{bo_spread_a:.2f} | B BO:{bo_spread_b:.2f} @ {get_now_hkt_string()}')

                    #check bo spread
                    if bo_spread_a > self.bot_config.depth_threshold or bo_spread_b > self.bot_config.depth_threshold:
                        self.logger.info(f"BO spread breached theshold for {symbol}|{self.bot_config.depth_threshold}, skipping...")
                        continue

                    self.event_dict[symbol] = now

                if not self.bot_config.is_trading:
                    continue
                if symbol in self.swap_position_book.positions.keys():
                    self.logger.info(f"Already working on {symbol}, skipping...")
                    continue
                #Hot logic

                with self.entry_lock:
                    self.last_trade_ts[symbol] = now
                    try:
                        order_qty = self.cal_quantity(symbol, bid_a, self.bot_config.max_trade_size_usd)
                        self.logger.info(f"Calculated order quantity for {symbol}: {order_qty}")
                        if order_qty[0] == 0 or order_qty[1] == 0:
                            self.logger.warning(f"Order quantity for {symbol} is zero, skipping...")
                            continue
                        if symbol in self.working_pair:
                            self.logger.info(f"Already working on {symbol}, skipping...")
                            continue
                        if spread_bp > 0:
                            order_a = Order(
                                exchange=self.bot_config.exchange_a,
                                symbol=symbol,
                                direction=OrderDirection.SELL,
                                order_type=OrderType.MARKET,
                                quantity=order_qty[0],
                                is_market_order=True
                            )
                            order_b = Order(
                                exchange=self.bot_config.exchange_b,
                                symbol=symbol.replace("USDT", "-USDT"),
                                direction=OrderDirection.BUY,
                                order_type=OrderType.MARKET,
                                quantity=order_qty[1],
                            )
                        else:
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
                        self.send_message(
                            "Calculated order quantity for {}: {} @ {}".format(symbol, order_qty, get_now_hkt_string()))
                    except Exception as e:
                        self.logger.error(f"Error in SwapArbStrategyBot: {e}")

            else:
                pass


if __name__ == "__main__":
    import sys
    client = RedisClient(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)
    tg = TelegramPostman()
    args = sys.argv[1:]
    bot_id = args[0] if len(args) > 0 else "ALT1"
    bot = SwapArbStrategyBot(client,messenger=tg, bot_id=bot_id)