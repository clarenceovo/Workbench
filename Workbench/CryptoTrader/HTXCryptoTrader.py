import math

from overrides import overrides

from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.CryptoDataConnector.HTXDataCollector import HTXDataCollector
from Workbench.config.ConnectionConstant import HTX_SPOT_API_URL, HTX_FUTURES_API_URL , HTX_TRADE_WS_URL, HTX_SWAP_WS_NOTIFICATION_URL
from Workbench.config.CredentialConstant import HTX_API_KEY , HTX_API_SECRET
from Workbench.model.position.positions import Position
from Workbench.util.OrderUtil import get_htx_signature
from Workbench.transport.websocket_client import WebsocketClient
from Workbench.model.order.Order import Order
from Workbench.model.OrderEnum import OrderSide , OrderType,OrderDirection
from Workbench.util.OrderUtil import decode_gzip_message
from threading import Thread
import pandas as pd
import requests
import time

DEFAULT_LEVERAGE_RATE = 5  # Default leverage rate for HTX
class HTXCryptoTrader(CryptoTraderBase):
    """
    HTX Crypto Trader class for trading on HTX exchange.
    """

    def __init__(self, name="HTXCryptoTrader",
                 api_key=HTX_API_KEY,
                 api_secret=HTX_API_SECRET,
                 start_ws=True):
        super().__init__(name, api_key, api_secret)
        self.spot_base_url = HTX_SPOT_API_URL
        self.futures_base_url = HTX_FUTURES_API_URL
        self.account_url = f"{self.futures_base_url}/v1/account/accounts"

        self._create_contract_size_cache()
        if start_ws:
            self.ws_trade_client = WebsocketClient(
                url=HTX_TRADE_WS_URL,
                callback=self._trade_ws_handler)
            self.ws_noti_client = WebsocketClient(
                url=HTX_SWAP_WS_NOTIFICATION_URL,
                callback=self._noti_ws_handler)
            self.ws_thread = Thread(target=self.ws_trade_client.start, daemon=True).start()
            self.ws_noti_thread = Thread(target=self.ws_noti_client.start, daemon=True).start()
            self.logger.info("HTX WebSocket clients started.")
            time.sleep(1)
            self._trade_ws_subscribe()
            self._noti_ws_subscribe()

    def _create_contract_size_cache(self):
        self.contract_info = HTXDataCollector().get_contract_details()
        tmp = {}
        for index, row in self.contract_info.iterrows():
            code = row['contract_code'].replace('-','')
            tmp[code] = (row['contract_size'],row['price_tick'])

        setattr(self,"contract_reference",tmp)

    def get_order_size(self, symbol: str,quantity :float,price:float) -> float:

        detail = self.contract_reference.get(symbol,None)
        raw_quantity = quantity / price
        if detail is None:
            self.logger.error(f"Symbol {symbol} not found in contract details.")
            return 0
        contract_size = float(detail[0])
        step_size = float(detail[1])
        raw_size = raw_quantity / contract_size
        # Round to nearest step_size
        precision = int(round(-math.log10(step_size)))
        order_size = round(raw_size, precision)
        return int(order_size)

    def _noti_ws_subscribe(self):
        """
        Subscribe to HTX WebSocket notification channels.
        This method subscribes to the notification channel for real-time updates.
        """
        self._noti_ws_authenticate()
        self.logger.info("Subscribing to HTX WebSocket notification channels...")
        self.ws_noti_client.send({
            "op": "sub",
            "topic": "orders.*",
            "cid": "orders_sub_all"
        })
        self.ws_noti_client.send({
            "op": "sub",
            "topic": "positions_cross.*",
            "cid": "positions_cross_sub_all"
        })
    def _trade_ws_subscribe(self):
        """
        Subscribe to HTX WebSocket channels.
        This method subscribes to the trade channel for real-time updates.
        """
        self._trade_ws_authenticate()
        self.logger.info("Subscribing to HTX WebSocket channels...")


    def _trade_ws_authenticate(self):
        """
        Authenticate the WebSocket connection with HTX.
        This method should be called after the WebSocket connection is established.
        """
        self.logger.info("Authenticating HTX WebSocket connection...")
        payload = get_htx_signature(self.api_key, self.api_secret,"GET", "api.hbdm.com", "/linear-swap-trade", {},is_ws=True)
        self.ws_trade_client.send(payload)
        self.logger.info("HTX WebSocket authentication message sent.")

    def _noti_ws_authenticate(self):
        """
        Authenticate the WebSocket connection with HTX.
        This method should be called after the WebSocket connection is established.
        """
        self.logger.info("Authenticating HTX Notification WebSocket connection...")
        payload = get_htx_signature(self.api_key, self.api_secret,"GET", "api.hbdm.com", "/linear-swap-notification", {},is_ws=True)
        self.ws_noti_client.send(payload)
        self.logger.info("HTX Notification WebSocket authentication message sent.")

    def _trade_ws_handler(self, msg):
        """
        WebSocket handler for HTX.
        This method should be overridden to handle WebSocket messages.
        """
        msg = decode_gzip_message(msg)

        if msg.get("op"):
            if msg.get("op") == "ping":
                pong = {"op":"pong", "ts": msg["ts"]}
                self.ws_trade_client.send(pong)
        else:
            #self.logger.info(f"Received message: {msg}")
            if msg.get("status", None) == "ok":
                data = msg.get("data", {})
                if data.get("order_id"):
                    self.logger.info(f"HTX Order {data.get("order_id")} processed successfully.")


    def _noti_ws_handler(self, msg):
        """
        WebSocket handler for HTX notifications.
        This method should be overridden to handle WebSocket messages.
        """
        msg = decode_gzip_message(msg)
        if msg.get("op"):
            if msg.get("op") == "ping":
                pong = {"op":"pong", "ts": msg["ts"]}
                self.ws_noti_client.send(pong)
            elif msg.get("op") == "notify":
                self._ws_position_handler(msg.get("data", []))

    def _ws_position_handler(self, msg: list):
        if len(msg) == 0:
            return
        for item in msg:
            if item.get('available') >0:
                contract_size = self.contract_reference[item['contract_code'].replace('-','')][0]
                item['contract_size'] = contract_size
                item['available'] = item.get('available', 0)
                self.position_book.add_position(Position.from_htx_position(item))


    def ws_place_order(self, order: Order):
        """
        Place an order via WebSocket.
        :param order: Order object containing order details.
        :param is_market_order: Boolean indicating if the order is a market order.
        :param mode: Order type, either 'limit' or 'market'.
        :return: Response from the WebSocket server.
        """
        if '-' not in order.symbol:
            order.symbol = order.symbol.replace('USDT','-USDT')
        payload = order.to_htx_order()

        self.logger.info(f"Placing order {order.client_order_id} via WebSocket: {payload}")
        self.ws_trade_client.send(payload)


    def place_order(self, order: Order, is_market_order: bool = False,mode: str = 'limit'):
        method = 'POST'
        host = 'api.hbdm.com'
        path = "/linear-swap-api/v1/swap_order"
        url = f'https://{host}{path}'

        order_mode = mode
        if is_market_order:
            order_mode = "market"

        params = {
                    "contract_code":order.symbol,
                    "direction":order.direction,
                    "price":order.price,
                    "lever_rate":DEFAULT_LEVERAGE_RATE,
                    "volume":1,
                    "order_price_type": order_mode

        }
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, host, path, params)
        response = requests.post(url, params=signed_params, json=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to place order: {response.text}")

    def load_position(self, symbol: str,model: str = 'futures'):
        # Implement position loading logic here
        if model == 'futures':
            return self._load_futures_position(symbol)
        elif model == 'spot':
            return self._load_spot_position(symbol)

    def _load_spot_position(self, symbol: str):
        method = 'GET'
        host = 'api.huobi.pro'
        path = '/v1/account/accounts'
        url = f'https://{host}{path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, host, path, params)
        response = requests.get(url, params=signed_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to load position: {response.text}")

    def get_asset_valuation(self):
        method = 'GET'
        host = 'api.huobi.pro'
        path = '/v2/account/asset-valuation'
        url = f'https://{host}{path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, host, path, params)
        response = requests.get(url, params=signed_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get asset valuation: {response.text}")

    def _load_futures_position(self, symbol: str=None):
        method = 'POST'
        host = 'api.hbdm.com'
        path = '/linear-swap-api/v1/swap_position_info'
        url = f'https://{host}{path}'
        params = {"contract":"BTC-USDT"} if symbol is None else {"contract": symbol}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, host, path, params)
        data = {
            'contract': "BTC-USDT" if symbol is None else symbol,
        }
        response = requests.post(url, params=signed_params, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to load position: {response.text}")

    def get_swap_position_info(self):
        method = 'POST'
        base_url = 'api.hbdm.com'
        request_path = '/linear-swap-api/v1/swap_position_info'
        url = f'https://{base_url}{request_path}'
        # Leave params empty to query all positions
        params = {}

        signed_params = get_htx_signature(self.api_key, self.api_secret, method, base_url, request_path, params)
        response = requests.post(url, params=signed_params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get all positions: {response.text}")

    def get_account_status(self, model: str = 'futures'):
        if model == 'futures':
            return self.get_future_account_info()
        method = 'GET'
        base_url = 'api.hbdm.com'
        request_path = '/v1/account/accounts'
        url = f'https://{base_url}{request_path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, base_url, request_path, params)
        response = requests.get(url, params=signed_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get account info: {response.text}")

    def get_account_balance(self):
        pass

    def get_accounts(self):
        method = 'GET'
        base_url = 'api.hbdm.com'
        request_path = '/v1/account/accounts'
        url = f'https://{base_url}{request_path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, base_url, request_path, params)
        response = requests.get(url, params=signed_params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get accounts: {response.text}")

    def get_future_account_info(self):
        method = 'POST'
        base_url = 'api.hbdm.com'
        request_path = '/linear-swap-api/v1/swap_cross_account_info'
        url = f'https://{base_url}{request_path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, base_url, request_path, params)
        response = requests.post(url, params=signed_params)
        if response.status_code == 200:
            return pd.DataFrame.from_dict(response.json()['data'])
        else:
            raise Exception(f"Failed to get account balance: {response.text}")

    def get_active_position_symbol(self):
        position = list(self.get_future_account_info()['contract_detail'].values[0])
        ret = []
        for pos in position:
            if pos['margin_position'] > 0:
                ret.append(pos['contract_code'].replace('-',''))
        return ret

    def get_order_by_id(self, symbol: str, order_id: str):
        method = 'POST'
        base_url = 'api.hbdm.com'
        request_path = '/linear-swap-api/v1/swap_order_info'
        url = f'https://{base_url}{request_path}'

        params = {
            "order_id": order_id,
            "pair": symbol
        }

        signed_params = get_htx_signature(
            self.api_key,
            self.api_secret,
            method,
            base_url,
            request_path,
            params
        )

        response = requests.post(url, params=signed_params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                return data["data"][0]  # Assuming it's a list of one order
            else:
                raise Exception(f"HTX API returned error: {data}")
        else:
            raise Exception(f"Failed to get order info: {response.status_code} - {response.text}")

if __name__ == '__main__':
    # Example usage
    # todo : remove this after testing


    trader = HTXCryptoTrader()
    time.sleep(1)

    order = Order(
        exchange="HTX",
        symbol="AAVE-USDT",
        direction=OrderDirection.SELL,
        order_type=OrderType.MARKET,
        quantity=3,
        reduce_only=True,
        is_close_order=True

    )
    #sz = trader.get_order_size("BTCUSDT",100,100500)
    #print(sz)
    trader.ws_place_order(order)



    try:
        account_info = trader.get_future_account_info()
        print("Account Info:", account_info)
    except Exception as e:
        print(f"Error fetching account info: {e}")