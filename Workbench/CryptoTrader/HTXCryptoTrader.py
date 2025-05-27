from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.config.ConnectionConstant import HTX_SPOT_API_URL, HTX_FUTURES_API_URL
from Workbench.config.CredentialConstant import HTX_API_KEY , HTX_API_SECRET
from Workbench.util.OrderUtil import get_htx_signature
from Workbench.transport.websocket_client import WebsocketClient
from Workbench.util.OrderUtil import decode_gzip_message
from threading import Thread
import requests

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
                url="wss://api.huobi.pro/ws",
                callback=self._ws_handler)
        if start_ws:
            self.ws_thread = Thread(target=self.ws_client.start, daemon=True).start()

    def _ws_handler(self, msg):
        """
        WebSocket handler for HTX.
        This method should be overridden to handle WebSocket messages.
        """
        msg = decode_gzip_message(msg)
        if msg.get("ping"):
            pong = {"pong": msg["ping"]}
            self.ws_client.send(pong)


    def place_order(self, order):
        # Implement order placement logic here
        pass

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

    def get_account_status(self):
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
        method = 'POST'
        base_url = 'api.hbdm.com'
        request_path = '/linear-swap-api/v1/swap_account_info'
        url = f'https://{base_url}{request_path}'
        params = {}
        signed_params = get_htx_signature(self.api_key, self.api_secret, method, base_url, request_path, params)
        response = requests.get(url, params=signed_params)
        if response.status_code == 200:
            return response.json()
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