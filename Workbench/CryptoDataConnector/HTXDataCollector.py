import requests
import time
from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector

class HTXDataCollector(BaseDataCollector):
    def __init__(self, name="HTXDataCollector"):
        super().__init__(name)
        self.spot_base_url = "https://api.huobi.pro"
        self.futures_base_url = "https://api.hbdm.com"

    def get_kline(self, symbol="btcusdt", period="1min", size=100):
        url = f"{self.spot_base_url}/market/history/kline"
        params = {
            "symbol": symbol,
            "period": period,
            "size": size
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_instrument(self):
        url = f"{self.spot_base_url}/v1/common/symbols"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_contract_details(self):
        url = f"{self.futures_base_url}/api/v1/contract_contract_info"
        resp = requests.get(url)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_open_interest(self, contract_code="BTC-USDT"):
        url = f"{self.futures_base_url}/api/v1/contract_open_interest"
        params = {"contract_code": contract_code}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("data", [])

    def get_funding(self, contract_code="BTC-USDT"):
        url = f"{self.futures_base_url}/linear-swap-api/v1/swap_funding_rate"
        params = {"contract_code": contract_code}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("data", {})

    def get_time(self):
        # HTX doesn't provide a dedicated time API, use local time as fallback
        return int(time.time() * 1000)