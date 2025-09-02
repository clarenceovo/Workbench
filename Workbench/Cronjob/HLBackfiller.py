import time

from Workbench.CryptoDataConnector.HyperliquidDataCollector import HyperliquidDataCollector
from Workbench.config.ConnectionConstant import QUEST_HOST, QUEST_PORT, CLARENCE_QUEST_HOST
from Workbench.model.dto.FundingRate import FundingRate
from Workbench.transport.QuestClient import QuestDBClient
from datetime import datetime, timedelta

client = QuestDBClient(host=CLARENCE_QUEST_HOST,
                       port=9009,read_only=True)


write_client = QuestDBClient(host=QUEST_HOST,
                       port=QUEST_PORT)

time.sleep(5)
hl_client = HyperliquidDataCollector()

hist_funding = hl_client.get_historical_funding("ETH",start_time_ms=int((datetime.now()-timedelta(days=365)).timestamp()*1000),end_time_ms=int(datetime.now().timestamp()*1000))

symbol = client.execute_query("select distinct(symbol) from funding_rate where exchange = 'Hyperliquid'")
symbol_list = symbol['symbol'].tolist()

def get_historical_funding(symbol: str,start_time_ms: int = None, end_time_ms: int = None):
    """
    Get historical funding rates for a given symbol.
    """
    if start_time_ms is None:
        start_time_ms = int((datetime.now() - timedelta(days=365)).timestamp() * 1000)
    if end_time_ms is None:
        end_time_ms = int(datetime.now().timestamp() * 1000)
    hist_funding = hl_client.get_historical_funding(symbol,
                                                     start_time_ms=start_time_ms,
                                                     end_time_ms=end_time_ms)
    return hist_funding

if __name__ == '__main__':
    for symbol in symbol_list:
        first_row = client.execute_query(
            f"select * from funding_rate where symbol = '{symbol}' and exchange = 'Hyperliquid' order by timestamp asc limit 1")
        ts = first_row.index.tolist()[0]
        ts = int(ts.timestamp() * 1000) if ts else None

        payload = []
        end_of_page = False
        start_ts = int((datetime.now() - timedelta(days=180)).timestamp())
        end_ts = int(datetime(2025, 9, 1, 22, 0).timestamp() * 1000)
        while end_of_page  is False:
            try:
                hist_funding = hl_client.get_historical_funding(symbol,
                                                                 start_time_ms=start_ts,
                                                                 end_time_ms=end_ts)
                if not hist_funding:
                    end_of_page = True
                    continue

                payload.extend(hist_funding)

                for funding in hist_funding:
                    if funding['time'] > ts or len(hist_funding) == 1 :
                        end_of_page = True
                        break
                    else:
                        annual_rate = round(float(funding['fundingRate']) * 24 * 365 * 100, 4)
                        funding_rate = FundingRate(symbol=symbol,
                                                   annual_funding_rate=annual_rate,
                                                   timestamp=float(funding['time'] / 1000),
                                                   exchange="Hyperliquid")
                        batch = funding_rate.to_batch()
                        write_client.batch_write(batch)
                start_ts = hist_funding[-1]['time']
                print(f"Processed funding for {symbol} up to {datetime.fromtimestamp(start_ts/1000).strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(1)
            except Exception as e:
                print(f"Error fetching historical funding for {symbol}: {e}")
                break
