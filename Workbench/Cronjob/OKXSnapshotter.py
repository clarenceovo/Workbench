import time
from datetime import datetime

import schedule
from Workbench.CryptoDataConnector.OKXDataCollector import OKXDataCollector
from Workbench.model.dto.FundingRate import FundingRate
from Workbench.model.dto.OpenInterest import OpenInterest
from Workbench.transport.QuestClient import QuestDBClient
from Workbench.config.ConnectionConstant import QUEST_PORT, QUEST_HOST
from Workbench.util.TimeUtil import get_now_utc

def get_funding(client: OKXDataCollector, db_client: QuestDBClient):
    print("Getting funding from OKX")
    details = client.get_contract_details()
    if details is None or details.empty:
        print("No contract details found.")
        return
    symbols = details["instId"].unique()
    for sym in symbols:
        try:
            funding_data = client.get_funding(symbol=sym, limit=100)
            if funding_data:
                for entry in funding_data:
                    funding_rate = FundingRate(
                        timestamp=get_now_utc(),
                        exchange="OKX",
                        symbol=sym,
                        annual_funding_rate=round(float(entry["fundingRate"]) * 100, 4),
                    )
                    #batch = funding_rate.to_batch()
                    #if batch:
                    #   db_client.batch_write(batch)
            time.sleep(0.2)
        except Exception as e:
            print(f"Error fetching funding for {sym}: {e}")

def get_open_interest(client: OKXDataCollector, db_client: QuestDBClient):
    details = client.get_contract_details()
    details = details.query('ctType == "linear"') # Filter for SWAP contracts
    if details is None or details.empty:
        print("No contract details found.")
        return
    uly_symbols = details["uly"].dropna().unique()
    for uly in uly_symbols:
        try:
            open_interest_data = client.get_open_interest(uly)
            for item in open_interest_data:
                inst = item["instId"].replace('SWAP','').replace('-','')
                oi = OpenInterest(
                    timestamp=datetime.fromtimestamp(int(item['ts']) / 1000),
                    exchange="OKX",
                    symbol=inst,
                    open_interest=round(float(item["oiCcy"]), 2),
                )
                batch = oi.to_batch()
                if batch:
                    db_client.batch_write(batch)
            time.sleep(0.2)
        except Exception as e:
            print(f"Error fetching open interest for {uly}: {e}")
    print(f'Open interest data fetched successfully from OKX @{get_now_utc()}')

if __name__ == "__main__":
    db_client = QuestDBClient(host=QUEST_HOST, port=QUEST_PORT)
    data_client = OKXDataCollector()

    schedule.every(5).minutes.at(":00").do(lambda: get_open_interest(data_client, db_client))
    #schedule.every().hour.at(":00").do(lambda: get_funding(data_client, db_client))

    schedule.run_all()
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print(f"Error in OKXSnapshotter: {e}")