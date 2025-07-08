import json
import time
import hmac
import hashlib
from urllib.parse import urlencode
from threading import Thread

from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.config.CredentialConstant import BYBIT_API_KEY, BYBIT_API_SECRET
from Workbench.config.ConnectionConstant import BYBIT_FUTURES_API_URL, BYBIT_FUTURE_TRADE_WS_URL
from Workbench.model.OrderEnum import OrderSide, OrderDirection, OrderType
from Workbench.model.order.Order import Order
from Workbench.model.position.positions import Position
from Workbench.transport.websocket_client import WebsocketClient
from Workbench.util.OrderUtil import get_uuid


class BybitCryptoTrader(CryptoTraderBase):


    def __init__(self, name="BybitFuturesTrader",
                 api_key=BYBIT_API_KEY,
                 api_secret=BYBIT_API_SECRET,
                 start_ws=True):
        super().__init__(name, api_key, api_secret)
        self.base_url = BYBIT_FUTURES_API_URL
        self.order_book = {}
        self.event_id = {}
        if start_ws:
            self.ws_trade_client = WebsocketClient(
                url=BYBIT_FUTURE_TRADE_WS_URL,
                callback=self._trade_ws_handler,
            )
            self.ws_thread = Thread(target=self.ws_trade_client.start, daemon=True).start()
            time.sleep(1)
            self.position_thread = Thread(target=self.get_position, daemon=True).start()
            self.logger.info("Bybit Futures WebSocket client started.")
            time.sleep(1)

    def get_account_status(self):
        endpoint = "/v5/account/info"
        timestamp = str(int(time.time() * 1000))
        recv_window = str(5000)

        prehash = timestamp + self.api_key + recv_window
        signature = hmac.new(self.api_secret.encode(), prehash.encode(), hashlib.sha256).hexdigest()

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": signature,
        }

        url = f"{self.base_url}{endpoint}"
        resp = self.session.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            raise Exception(f"Failed to get account status: {data}")
        return data["result"]

    def get_account_tiering(self, category: str = "linear", symbol: str = None):
        endpoint = "/v5/account/fee-rate"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"

        params = {"category": category}
        if symbol:
            params["symbol"] = symbol.upper()

        # Step 1: build query string with sorted keys
        query_string = urlencode(sorted(params.items()))

        # Step 2: construct signature payload
        sign_payload = timestamp + self.api_key + recv_window + query_string

        # Step 3: generate signature
        sign = hmac.new(
            self.api_secret.encode(),
            sign_payload.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "X-BAPI-SIGN": sign,
        }

        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        if data.get("retCode") != 0:
            raise Exception(f"Error fetching fee rate: {data.get('retMsg')}")

        return data["result"]["list"]

    def generate_signature(self, params: dict) -> str:
        query = urlencode(params)
        return hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

    def _sign(self, params: dict) -> str:
        return self.generate_signature(params)

    def _get_headers(self):
        return {
            'X-BYBIT-API-KEY': self.api_key
        }

    def _send_signed_request(self, method: str, endpoint: str, params: dict = None):
        params = params or {}
        params["api_key"] = self.api_key
        params["timestamp"] = int(time.time() * 1000)
        params["sign"] = self._sign(params)

        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, headers=self._get_headers(), params=params)
        if response.status_code != 200:
            self.logger.error(f"Request failed: {response.text}")
        return response.json()

    def ws_place_order(self, order: Order, reduce_only=False):
        order_param = {
            "api_key": self.api_key,
            "side": "Sell" if order.direction == OrderDirection.SELL else "Buy",
            "symbol": order.symbol,
            "order_type": "Market" if order.order_type == OrderType.MARKET else "Limit",
            "qty": order.quantity,
            "time_in_force": "GoodTillCancel",
            "timestamp": int(time.time() * 1000),
        }
        if not order.is_market_order:
            order_param["price"] = order.price
        if reduce_only:
            order_param["reduce_only"] = True

        order_param["sign"] = self._sign(order_param)
        order_payload = {
            "id": get_uuid(),
            "method": "order.place",
            "params": order_param
        }
        self.order_book[order_payload['id']] = order_payload
        self.event_id[order_payload['id']] = "order.place"
        self.logger.info(f"Sending order: {order_payload}")
        self.ws_trade_client.send(order_payload)

    def _trade_ws_handler(self, msg):
        msg = json.loads(msg)
        action = self.event_id.get(msg.get('id'), None)
        if msg.get("ret_code", 0) != 0:
            self.logger.error(f"Error in message: {msg}")
            return
        match action:
            case "order.place":
                self.logger.info(f"Order placed: {msg.get('result')}")
            case "account.position":
                self._position_handler(msg.get('result'))
            case _:
                self.logger.info(f"Unhandled action: {action}, message: {msg}")

    def get_position(self):
        while True:
            self._ws_get_position()
            time.sleep(1)

    def _ws_get_position(self):
        id = get_uuid()
        params = {
            "api_key": self.api_key,
            "timestamp": int(time.time() * 1000),
        }
        params["sign"] = self._sign(params)
        payload = {
            "id": id,
            "method": "account.position",
            "params": params
        }
        self.event_id[id] = "account.position"
        self.ws_trade_client.send(payload)

    def _position_handler(self, msg: list):
        for item in msg:
            if abs(float(item.get("size", 0))) > 0:
                position = Position.from_bybit_position(item)
                self.position_book.add_position(position)

    def get_account_balance(self):
        endpoint = "/v2/private/wallet/balance"
        return self._send_signed_request("GET", endpoint)

    def place_order(self, order: dict):
        endpoint = "/v2/private/order/create"
        return self._send_signed_request("POST", endpoint, order)

    def get_order_by_id(self, symbol: str, order_id: str):
        endpoint = "/v2/private/order"
        return self._send_signed_request("GET", endpoint, {
            "order_id": order_id,
            "symbol": symbol
        })

    def load_position(self, symbol: str):
        endpoint = "/v2/private/position/list"
        return self._send_signed_request("GET", endpoint, {"symbol": symbol})


if __name__ == "__main__":
    trader = BybitCryptoTrader()
    time.sleep(1)
    order = Order(
        exchange="BYBIT",
        symbol="XMRUSDT",
        direction=OrderDirection.SELL,
        quantity=0.715,
        price=0.8,
        order_type=OrderType.MARKET,
        is_market_order=True,
        is_close_order=True
    )
    #trader.ws_place_order(order)