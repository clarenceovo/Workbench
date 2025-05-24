import requests
import pandas as pd
from .BaseHandler import BaseHandler
class FinApiHandler(BaseHandler):
    def __init__(self) -> None:
        super().__init__('FinApiHandler')
        self.url = 'http://18.180.162.113:9888/crypto'

    def get_hist_data(self, symbol, start=None, end=None):
        HIST_ENDPOINT = self.url + '/getHistData'
        self.logger.info(f'Fetching historical data for {symbol}')
        payload = {
            'ticker': symbol,
            'start': start,
            'end': end
        }
        ret = requests.get(HIST_ENDPOINT, params=payload)
        if ret.status_code != 200:
            raise Exception(f'Failed to get data.{ret.text}')
        ret = ret.json()
        if ret:
            df = pd.DataFrame(ret['data'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        else:
            #return empty dataframe
            return pd.DataFrame()
