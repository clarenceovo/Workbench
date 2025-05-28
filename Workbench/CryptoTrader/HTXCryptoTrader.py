from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.config.ConnectionConstant import HTX_SPOT_API_URL, HTX_FUTURES_API_URL , HTX_TRADE_WS_URL
from Workbench.config.CredentialConstant import HTX_API_KEY , HTX_API_SECRET
from Workbench.util.OrderUtil import get_htx_signature
from Workbench.transport.websocket_client import WebsocketClient
from Workbench.model.order.Order import Order
from Workbench.util.OrderUtil import decode_gzip_message
from threading import Thread
import pandas as pd
import requests


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

        self.ws_client = WebsocketClient(
                url=HTX_TRADE_WS_URL,
                callback=self._trade_ws_handler)
        if start_ws:
            self.ws_thread = Thread(target=self.ws_client.start, daemon=True).start()

    def _trade_ws_handler(self, msg):
        """
        WebSocket handler for HTX.
        This method should be overridden to handle WebSocket messages.
        """
        msg = decode_gzip_message(msg)
        self.logger.info(f"Received message: {msg}")
        if msg.get("ping"):
            pong = {"pong": msg["ping"]}
            self.ws_client.send(pong)
        else:
            # Handle other messages such as order updates, trades, etc.
            self.logger.info(f"Received message: {msg}")
            # You can implement specific handling logic here based on the message type


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

    def _load_futures_position(self, symbol: str):
        method = 'POST'
        host = 'api.hbdm.com'
        path = '/linear-swap-api/v1/swap_position_info'
        url = f'https://{host}{path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, host, path, params)
        data = {
            'contract_code': symbol
        }
        response = requests.post(url, params=signed_params, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to load position: {response.text}")

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
if __name__ == '__main__':
    # Example usage
    trader = HTXCryptoTrader()
    try:
        account_info = trader.get_account_balance()
        print("Account Info:", account_info)
    except Exception as e:
        print(f"Error fetching account info: {e}")