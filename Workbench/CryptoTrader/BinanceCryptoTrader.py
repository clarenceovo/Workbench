import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from Workbench.CryptoTrader.CryptoTraderBase import CryptoTraderBase
from Workbench.config.ConnectionConstant import BINANCE_FUTURES_API_URL
from Workbench.config.CredentialConstant import BINANCE_API_KEY, BINANCE_API_SECRET


class BinanceCryptoTrader(CryptoTraderBase):
    """
    Binance Futures Crypto Trader implementation.
    """

    def __init__(self, name="BinanceFuturesTrader", api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET):
        super().__init__(name, api_key, api_secret)
        self.base_url = BINANCE_FUTURES_API_URL

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
        response = requests.request(method, url, headers=self._get_headers(), params=params)
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
        self.logger.info(f"Account balance: {result}")
        return result