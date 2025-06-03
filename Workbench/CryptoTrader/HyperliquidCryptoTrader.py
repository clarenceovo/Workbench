from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.CryptoDataConnector.HyperliquidDataCollector import HyperliquidDataCollector
from Workbench.config.ConnectionConstant import HYPERLIQUID_FUTURES_API_URL, HYPERLIQUID_FUTURES_WS_URL
from Workbench.config.CredentialConstant import HYPERLIQUID_PUBLIC_WALLET, HYPERLIQUID_API_WALLET, HYPERLIQUID_API_PRIVATE_KEY
from Workbench.model.order.Order import Order
from Workbench.model.OrderEnum import OrderSide, OrderType, OrderDirection
from Workbench.transport.websocket_client import WebsocketClient
from threading import Thread
import pandas as pd
import requests
import time
import json
import hmac
import hashlib
import base64

class HyperliquidCryptoTrader(CryptoTraderBase):
    """
    Hyperliquid Crypto Trader class for trading on Hyperliquid exchange.
    """



    def __init__(self, name="HyperliquidCryptoTrader",
                 api_key=HYPERLIQUID_API_WALLET,
                 api_secret=HYPERLIQUID_API_PRIVATE_KEY,
                 public_address=HYPERLIQUID_PUBLIC_WALLET,
                 start_ws=True):
        super().__init__(name, api_key, api_secret)
        self.base_url = HYPERLIQUID_FUTURES_API_URL
        self.api_wallet = self.api_key           # for placing orders
        self.public_address = public_address     # for info requests
        self.data_collector = HyperliquidDataCollector()

        if start_ws:
            self.ws_client = WebsocketClient(
                url=HYPERLIQUID_FUTURES_WS_URL,
                callback=self._ws_handler)
            self.ws_thread = Thread(target=self.ws_client.start, daemon=True).start()
            self.ping_thread = Thread(target=self._send_ping, daemon=True).start()
            self.logger.info("Hyperliquid WebSocket client started.")
            time.sleep(1)
            self._ws_subscribe()

    def _send_ping(self):
        while True:
            if self.ws_client.is_running:
                self.ws_client.send({"method": "ping"})
                self.logger.debug("Ping sent to Hyperliquid WebSocket.")
            time.sleep(30)

    def _ws_subscribe(self):
        self.logger.info("Subscribing to Hyperliquid WebSocket channels...")

        # Subscribe to user-specific updates
        user_subscriptions = [
            {"type": "orderUpdates", "user": self.public_address},
            {"type": "userFills", "user": self.public_address},
            {"type": "userFundings", "user": self.public_address},
            {"type": "userNonFundingLedgerUpdates", "user": self.public_address}
        ]

        for subscription in user_subscriptions:
            self.ws_client.send({
                "method": "subscribe",
                "subscription": subscription
            })

        # Subscribe to public data streams (e.g., trades and order book for BTC)
        """
        public_subscriptions = [
            {"type": "trades", "coin": "BTC"},
            {"type": "l2Book", "coin": "BTC"}
        ]

        for subscription in public_subscriptions:
            self.ws_client.send({
                "method": "subscribe",
                "subscription": subscription
            })
        """


    def _ws_handler(self, msg):
        """
        WebSocket message received: {'channel': 'userFills', 'data': {'user': '0xf933820e69fa1ff3cfc2aea16b187d8c608f9ad4', 'fills': [{'coin': 'SOPH', 'px': '0.067366', 'sz': '1626.0', 'side': 'A', 'time': 1748962205038, 'startPosition': '0.0', 'dir': 'Open Short', 'closedPnl': '0.0', 'hash': '0xac46eb583d9e8ce6660d0424c49eb301eb00939f59136ba0981d81c311b7f2b7', 'oid': 99565090533, 'crossed': True, 'fee': '0.049291', 'tid': 834202338833147, 'feeToken': 'USDC'}]}}
        WebSocket message received: {'channel': 'orderUpdates', 'data': [{'order': {'coin': 'SOPH', 'side': 'A', 'limitPx': '0.06733', 'sz': '1626.0', 'oid': 99565090533, 'timestamp': 1748962205038, 'origSz': '1626.0'}, 'status': 'open', 'statusTimestamp': 1748962205038}, {'order': {'coin': 'SOPH', 'side': 'A', 'limitPx': '0.06733', 'sz': '0.0', 'oid': 99565090533, 'timestamp': 1748962205038, 'origSz': '1626.0'}, 'status': 'filled', 'statusTimestamp': 1748962205038}]}
        :param msg:
        :return:
        """
        try:
            data = json.loads(msg)
        except Exception as e:
            self.logger.error(f"Failed to decode WS message: {e}")
            return

        match data.get("channel"):
            case "pong":
                self.logger.debug("Received pong from WebSocket.")
            case "userFills":
                fills = data.get("data", {}).get("fills", [])
                for fill in fills:
                    self.logger.info(f"Fill received: {fill}")
                    # Process fill data here
            case "orderUpdates":
                orders = data.get("data", [])
                for order_update in orders:
                    order = order_update.get("order", {})
                    status = order_update.get("status")
                    self.logger.info(f"Order update: {order}, Status: {status}")
                    # Process order update here

            case _:
                self.logger.debug(f"Unhandled WebSocket message: {data}")


    def place_order(self, order: Order, is_market_order=False, mode='limit'):
        url = f"{self.base_url}/exchange"
        order_payload = {
            "method": "order",
            "params": {
                "coin": order.symbol,
                "isBuy": order.direction == OrderDirection.BUY,
                "sz": str(order.quantity),
                "limitPx": None if is_market_order else str(order.price),
                "orderType": "market" if is_market_order else "limit",
                "reduceOnly": False
            },
            "id": int(time.time()),
        }

        signed_payload = self._sign_payload(order_payload)
        response = requests.post(url, json=signed_payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to place order: {response.text}")

    def load_position(self, symbol: str):
        url = f"{self.base_url}/info"
        response = requests.post(url, json={
            "method": "userPositions",
            "params": {"user": self.public_address}
        })
        if response.status_code == 200:
            data = response.json()
            return [p for p in data if p["coin"] == symbol]
        else:
            raise Exception(f"Failed to load position: {response.text}")

    def get_account_balance(self):
        url = f"{self.base_url}info"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "type": "clearinghouseState",
            "user": self.public_address  # Ensure this is your main account's public address

        }
        response = requests.post(url, json=payload,headers=headers)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                raise Exception(f"Failed to decode response JSON: {response.text}")
        else:
            raise Exception(f"Failed to get account balance: {response.status_code} {response.text}")

    def get_account_status(self):
        pass

    def _sign_payload(self, payload):
        """
        Sign the payload using HMAC-SHA256 as per Hyperliquid's signing requirements.
        """
        message = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        payload['signature'] = signature
        return payload

if __name__ == "__main__":
    client = HyperliquidCryptoTrader(start_ws=True)
    account = client.get_account_balance()
    print(account)