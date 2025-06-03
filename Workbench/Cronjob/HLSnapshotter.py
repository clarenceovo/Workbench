import time

import schedule
from Workbench.CryptoDataConnector.HyperliquidDataCollector import HyperliquidDataCollector
from Workbench.CryptoWebsocketDataCollector.HyperliquidWSCollector import HyperliquidWSCollector
from Workbench.model.dto.FundingRate import FundingRate
from Workbench.model.dto.OpenInterest import OpenInterest
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.config.ConnectionConstant import QUEST_PORT , QUEST_HOST
from Workbench.util.TimeUtil import get_timestamp, get_now, get_now_utc


def get_funding(client: HyperliquidDataCollector , db_client: QuestDBClient):
    print("Getting funding from Hyperliquid")
    funding_rate = client.get_funding()
    if funding_rate:
        for coin, rate in funding_rate.items():
            funding_rate = FundingRate(
                timestamp=get_timestamp(),
                exchange="Hyperliquid",
                symbol=coin,
                annual_funding_rate=round(rate * 100, 4),
            )
            funding_batch = funding_rate.to_batch()
            if funding_batch:
                db_client.batch_write(funding_batch)

def get_open_interest(client: HyperliquidDataCollector, db_client: QuestDBClient):
    print("Fetching open interest data...")
    open_interest = client.get_open_interest()
    if open_interest:
        for coin, oi in open_interest.items():
            open_interest = OpenInterest(
                timestamp=get_now_utc(),
                exchange="Hyperliquid",
                symbol=coin,
                open_interest=round(oi , 2),
            )
            oi_batch = open_interest.to_batch()
            if oi_batch:
                db_client.batch_write(oi_batch)
if __name__ == "__main__":
    db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)
    data_client = HyperliquidDataCollector()
    #register the collector
    schedule.every().minute.at(":00").do(lambda: get_open_interest(data_client, db_client))
    schedule.every().hour.at(":00").do(lambda: get_funding(data_client, db_client))
    schedule.run_all()
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Error in HLSnapshotter: {e}")
        finally:
            schedule.run_pending()

