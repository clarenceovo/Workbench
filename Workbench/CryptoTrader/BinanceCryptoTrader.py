import json
import time
import hmac
import hashlib
import math
from urllib.parse import urlencode

from overrides import overrides

from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.config.ConnectionConstant import (BINANCE_FUTURES_API_URL,
                                                 BINANCE_FUTURE_TRADE_WS_URL)
from Workbench.config.CredentialConstant import BINANCE_API_KEY, BINANCE_API_SECRET
from Workbench.model.OrderEnum import OrderSide, OrderDirection, OrderType
from Workbench.model.order.Order import Order
from Workbench.model.position.positions import Position, PositionBooks
from Workbench.transport.websocket_client import WebsocketClient
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from threading import Thread

from Workbench.util.OrderUtil import get_uuid


class BinanceCryptoTrader(CryptoTraderBase):
    """
    Binance Futures Crypto Trader implementation.
    """

    def __init__(self, name="BinanceFuturesTrader",
                 api_key=BINANCE_API_KEY,
                 api_secret=BINANCE_API_SECRET,
                 start_ws=True):
        super().__init__(name, api_key, api_secret)
        self.base_url = BINANCE_FUTURES_API_URL
        self.order_book = {}
        self.event_id = {}
        self._create_contract_size_cache()
        if start_ws:
            self.ws_trade_client = WebsocketClient(
                url=BINANCE_FUTURE_TRADE_WS_URL,
                callback=self._trade_ws_handler,
            )
            self.ws_thread = Thread(target=self.ws_trade_client.start, daemon=True).start()
            time.sleep(1)
            self.position_thread = Thread(target=self.get_position, daemon=True).start()
            self.logger.info("Binance Futures WebSocket client started.")
            time.sleep(1)

    def _create_contract_size_cache(self):
        """
        Create a cache for contract sizes.
        This method can be used to pre-load contract sizes and map to a dict for O(1) access.
        """
        self.contract_info = BinanceDataCollector().get_contract_details()
        tmp = {}
        for index, row in self.contract_info.iterrows():
            tmp[row['symbol']] = row['filters']
        setattr(self, "filter_reference", tmp)

    @staticmethod
    def generate_signature(secret, params):
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    def get_account_token_balance(self):
        ret = self.get_account_balance()
        return [{asset['asset'] : asset['balance']} for asset in ret if float(asset['balance']) > 0]

    def ws_place_order(self, order: Order):
        order_param = {
            "apiKey": self.api_key,
            "quantity": order.quantity,  # Example quantity, adjust as needed
            "side": "BUY" if order.direction == OrderDirection.BUY else "SELL",
            "symbol": order.symbol.replace('-', ''),
            "timestamp": int(time.time() * 1000),
            "type": "MARKET" if order.order_type == OrderType.MARKET else "LIMIT",
        }
        if order.is_market_order is False:
            order_param["price"] = order.price
        order_param = dict(sorted(order_param.items()))
        order_param["signature"] = self._sign(order_param)
        order_payload = {
            "id": get_uuid(),
            "method": "order.place",
            "params": order_param
        }
        self.order_book[order_payload['id']] = order_payload
        self.event_id[order_payload['id']] = "order.place"
        self.logger.info(f"Sending order:{order_payload}")
        self.ws_trade_client.send(order_payload)

    def get_order_size(self, symbol: str, quantity: float, price: float) -> float:
        """
        Get the contract size for a given symbol.
        :param symbol: The trading pair symbol.
        :return: The contract size.
        """
        filters = self.filter_reference.get(symbol, None)
        if filters:
            for f in filters:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    # Round to the nearest step size
                    raw_contracts = quantity / price
                    adjusted_quantity = round(raw_contracts / step_size) * step_size
                    precision = int(round(-math.log10(step_size)))
                    return max(round(adjusted_quantity, precision), min_qty)
        return 0

    def _trade_ws_handler(self, msg):
        """
        Handle messages from the Binance Futures trade WebSocket.
        """
        # Implement the logic to handle trade messages
        msg = json.loads(msg)
        action = self.event_id.get(msg['id'], None)
        status = msg['status']
        if status != 200:
            self.logger.error(f"Error in message: {msg}")
            return
        match action:
            case "order.place":
                if msg.get('status') == 200:
                    self.logger.info(f"Order placed successfully: {msg['result']}")
                else:
                    self.logger.error(f"Failed to place order: {msg['result']}")
            case "account.position":
                if msg.get('status') == 200:
                    self._position_handler(msg['result'])
                else:
                    self.logger.error(f"Failed to get position data: {msg['result']}")
            case None:
                self.logger.error(f"Received message with unknown id: {msg['id']}, message: {msg}")
            case _:
                self.logger.info(f"Unhandled action: {action}, message: {msg}")

    def get_position(self):
        while True:
            self._ws_get_position()
            time.sleep(1)

    def _position_handler(self, msg: list):
        for item in msg:
            if item['updateTime'] > 0:
                position = Position.from_binance_position(item)
                if abs(position.quantity) == 0:
                    continue
                self.position_book.add_position(position)

    def _ws_get_position(self):
        id = get_uuid()
        params = {
            "apiKey": self.api_key,
            "timestamp": int(time.time() * 1000)
        }
        params["signature"] = self._sign(params)
        payload = {
            "id": id,
            "method": "account.position",
            "params": params
        }
        self.event_id[id] = "account.position"
        self.ws_trade_client.send(payload)

    def _sign(self, params: dict) -> str:
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _get_headers(self):
        return {
            'X-MBX-APIKEY': self.api_key
        }

    def _send_signed_request(self, method: str, endpoint: str, params: dict = None):
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, headers=self._get_headers(), params=params)
        if response.status_code != 200:
            self.logger.error(f"Request failed: {response.text}")
        return response.json()

    def place_order(self, order: dict):
        """
        Place an order on Binance Futures.
        Required fields: symbol, side, type, quantity
        Optional: price, timeInForce, etc.
        """
        endpoint = "/fapi/v1/order"
        result = self._send_signed_request("POST", endpoint, order)
        self.logger.info(f"Order placed: {result}")
        return result

    def load_position(self, symbol: str):
        """
        Get position information for a given symbol.
        """
        endpoint = "/fapi/v2/positionRisk"
        params = {"symbol": symbol.upper()}
        result = self._send_signed_request("GET", endpoint, params)
        self.logger.info(f"Position for {symbol}: {result}")
        return result

    def get_all_positions(self):
        """
        Fetch all positions with non-zero quantities from Binance Futures.
        """
        endpoint = "/fapi/v2/positionRisk"
        result = self._send_signed_request("GET", endpoint)

        # Filter positions with non-zero quantity
        available_positions = [pos for pos in result if float(pos['positionAmt']) != 0]
        return

    def get_active_position_symbol(self):
        ret = []
        pos = self.get_all_positions()
        for p in pos:
            ret.append(p['symbol'])
        return ret

    def get_account_status(self):
        """
        Get the current account information and status.
        """
        endpoint = "/fapi/v2/account"
        result = self._send_signed_request("GET", endpoint)
        self.logger.info(f"Account status: {result}")
        return result

    def get_account_balance(self):
        """
        Get USDT balance of the futures account.
        """
        endpoint = "/fapi/v2/balance"
        result = self._send_signed_request("GET", endpoint)
        # self.logger.info(f"Account balance: {result}")
        return result

    def get_order_by_id(self, symbol: str, order_id: str):
        endpoint = "/fapi/v1/order"
        url = self.base_url + endpoint

        params = {
            "symbol": symbol.upper(),
            "timestamp": int(time.time() * 1000)
        }
        params["signature"] = self._sign(params)

        result = self._send_signed_request("GET", endpoint, params)
        return result


if __name__ == "__main__":
    trader = BinanceCryptoTrader(start_ws=True)
    time.sleep(1)
    order = Order(
        exchange="BINANCE",
        symbol="XMRUSDT",
        direction=OrderDirection.SELL,
        quantity=0.715,
        price=0.8,  # Example price, adjust as needed
        order_type=OrderType.MARKET,
        is_market_order=True,
        is_close_order=True
    )
    # sz =trader.get_order_size("BTCUSDT",1500,10500.0)
    # print(f"Adjusted order size: {sz}")
    trader.ws_place_order(order)

    # Example usage
    ##print(trader.get_account_status())
    # print(trader.get_account_balance())
    # Place a sample order (make sure to adjust the parameters)
