import time
from datetime import datetime
import schedule
from Workbench.CryptoDataConnector.BybitDataCollector import BybitDataCollector
from Workbench.model.dto.FundingRate import FundingRate
from Workbench.model.dto.OpenInterest import OpenInterest
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.config.ConnectionConstant import QUEST_PORT, QUEST_HOST
from Workbench.util.TimeUtil import get_timestamp, get_now, get_now_utc

target_base = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LTC", "LINK", "POL",
               "AVAX","AAVE", "UNI", "XLM", "SUI", "ALGO", "XMR","DOGE",]

def get_funding(client: BybitDataCollector, db_client: QuestDBClient):
    print("Getting funding from Bybit")
    funding_rates = client.get_funding()
    if funding_rates:
        for coin, rate in funding_rates.items():
            funding_rate = FundingRate(
                timestamp=get_now_utc(),
                exchange="Bybit",
                symbol=coin,
                annual_funding_rate=round(rate * 100, 4),
            )
            funding_batch = funding_rate.to_batch()
            if funding_batch:
                db_client.batch_write(funding_batch)


def get_open_interest(client: BybitDataCollector, db_client: QuestDBClient):
    print("Fetching open interest data from Bybit...")
    contract = client.get_contract_details()
    contract = contract[contract['baseCoin'].isin(target_base)]
    contract = contract[contract['quoteCoin'] == "USDT"]
    contract = contract[contract['contractType'] == "LinearPerpetual"]
    symbols = list(contract['symbol'].values)
    for sym in symbols:
        open_interest = client.get_open_interest(symbol=sym, limit=1)
        if open_interest:
            open_interest = open_interest['list']
            for item in open_interest:

                open_interest = OpenInterest(
                    timestamp=datetime.fromtimestamp(int(item['timestamp']) / 1000),
                    exchange="Bybit",
                    symbol=sym,
                    open_interest=round(float(item['openInterest']), 2),
                )
                oi_batch = open_interest.to_batch()
                if oi_batch:
                    db_client.batch_write(oi_batch)


if __name__ == "__main__":
    db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)
    data_client = BybitDataCollector()
    # Register the collector
    schedule.every(5).minutes.at(":00").do(lambda: get_open_interest(data_client, db_client))
    #schedule.every().hour.at(":00").do(lambda: get_funding(data_client, db_client))
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Error in BybitSnapshotter: {e}")
        finally:
            schedule.run_pending()