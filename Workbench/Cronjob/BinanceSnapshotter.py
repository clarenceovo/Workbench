import time

import schedule
from Workbench.CryptoDataConnector.BinanceDataCollector import BinanceDataCollector
from Workbench.model.dto.FundingRate import FundingRate
from Workbench.model.dto.OpenInterest import OpenInterest
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.config.ConnectionConstant import QUEST_PORT, QUEST_HOST, CLARENCE_QUEST_HOST, CLARENCE_QUEST_PORT
from Workbench.util.TimeUtil import get_timestamp, get_now, get_now_utc


def get_funding(client: BinanceDataCollector, db_client: QuestDBClient):
    print("Getting funding from Binance")
    details = client.get_contract_details()
    if details is None or details.empty:
        print("No contract details found.")
        return
    symbol = details["symbol"].values
    for sym in symbol:
        funding_rates = client.get_funding(symbol=sym, limit=1000)
        if funding_rates:
            for rate in funding_rates:
                funding_rate = FundingRate(
                    timestamp=get_now_utc(),
                    exchange="Binance",
                    symbol=sym,  # Binance uses USDT for perpetuals
                    annual_funding_rate=round(float(rate["fundingRate"]) * 100, 4),
                )
                funding_batch = funding_rate.to_batch()
                if funding_batch:
                    pass
                    #db_client.batch_write(funding_batch)


def get_open_interest(client: BinanceDataCollector, db_client: QuestDBClient):
    print("Fetching open interest data from Binance...")
    details = client.get_contract_details()
    if details is None or details.empty:
        print("No contract details found.")
        return
    symbol = list(details["symbol"].values[:10])
    symbol.extend(['SOLUSDT','SUIUSDT','DOGEUSDT',"BNBUSDT"])
    for sym in symbol:
        print(f"Fetching open interest for {sym}")
        open_interest = client.get_open_interest(symbol=sym)
        if open_interest:
            open_interest = OpenInterest(
                timestamp=get_now_utc(),
                exchange="Binance",
                symbol=sym,
                open_interest=round(float(open_interest["openInterest"]), 2),
            )
            oi_batch = open_interest.to_batch()
            if oi_batch:
                db_client.batch_write(oi_batch)
        time.sleep(1)


if __name__ == "__main__":
    db_client = QuestDBClient(host=CLARENCE_QUEST_HOST, port=CLARENCE_QUEST_PORT)
    data_client = BinanceDataCollector()
    # Register the collector

    schedule.every(5).minutes.at(":00").do(lambda: get_open_interest(data_client, db_client))
    #schedule.every().hour.at(":00").do(lambda: get_funding(data_client, db_client))
    schedule.run_all()
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Error in BinanceSnapshotter: {e}")
        finally:
            schedule.run_pending()