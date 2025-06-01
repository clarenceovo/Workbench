import schedule
from Workbench.CryptoDataConnector.HyperliquidDataCollector import HyperliquidDataCollector
from Workbench.CryptoWebsocketDataCollector.HyperliquidWSCollector import HyperliquidWSCollector



config = {
    "name": "HLSnapshotter",
    "funding_interval": 1,
    "oi_interval": 30,
}