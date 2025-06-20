from Workbench.CryptoDataConnector.BaseDataCollector import BaseDataCollector
from enum import Enum

class HyperliquidDataCollector(BaseDataCollector):
    def __init__(self):
        super().__init__("Hyperliquid")
        self.base_url = "https://api.hyperliquid.xyz/info"

    def _post(self, payload):
        headers = {"Content-Type": "application/json"}
        response = self.session.post(self.base_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_kline(self):
        # Hyperliquid does not provide a direct kline endpoint in the info API.
        # This method would need to be implemented using the exchange or websocket API.
        raise NotImplementedError("get_kline is not implemented for Hyperliquid.")

    def get_instrument(self):
        payload = {"type": "meta"}
        return self._post(payload)

    def get_contract_details(self):
        payload = {"type": "metaAndAssetCtxs"}
        return self._post(payload)

    def get_open_interest(self):
        data = self.get_contract_details()
        asset_info = data[0].get("universe", {})
        asset_contexts = data[1]  # The second element contains asset contexts
        open_interest = {ctx.get("coin", f"{asset_info[i].get('name')}"): float(ctx.get("openInterest")) for i, ctx in enumerate(asset_contexts)}
        return open_interest

    def get_funding(self):
        data = self.get_contract_details()
        asset_info = data[0].get("universe", {})
        asset_contexts = data[1]
        funding_rates = {ctx.get("coin", f"{asset_info[i].get('name')}"): float(ctx.get("funding")) for i, ctx in enumerate(asset_contexts)}
        for coin, rate in funding_rates.items():
            funding_rates[coin] = rate * 24 * 365
        #convert hourly funding rates to annualized rates

        return funding_rates

    def get_time(self):
        # Hyperliquid does not provide a direct time endpoint.
        # As a workaround, we can use the current system time.
        import time
        return int(time.time() * 1000)

    def get_depth(self):
        # Hyperliquid does not provide a direct depth endpoint in the info API.
        # This method would need to be implemented using the exchange or websocket API.
        raise NotImplementedError("get_depth is not implemented for Hyperliquid.")

    def get_historical_funding(self, symbol, start_time_ms: int, end_time_ms: int):
        """
        Fetch historical funding rates for a given symbol from Hyperliquid.

        :param symbol: The coin symbol, e.g., 'ETH', 'BTC'.
        :param start_time_ms: Start of the time range in milliseconds (Unix time).
        :param end_time_ms: Optional end time in milliseconds. Defaults to current time.
        :return: List of funding history records.
        """
        payload = {
            "type": "fundingHistory",
            "coin": symbol,
            "startTime": start_time_ms,
            "endTime": end_time_ms
        }

        return self._post(payload)


if __name__ == '__main__':
    collector = HyperliquidDataCollector()
    print(collector.get_instrument())
    print(collector.get_contract_details())
    print(collector.get_open_interest())
    print(collector.get_funding())