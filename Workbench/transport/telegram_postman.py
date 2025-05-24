from requests import Session
import logging
from datetime import datetime
from Workbench.transport.BaseHandler import BaseHandler

TOKEN = '7341342883:AAHoNPZmp-7gBs0dOxWOjBg3s56UE5cEJYs'
TEST_CHANNEL = '-1002414297517'
class TelegramPostman(BaseHandler):

    def __init__(self) -> None:
        super().__init__('TelegramPostman')
        self.url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
        self.session = Session()
        self.logger = logging.getLogger("TelegramPostman")
        
    def send_message(self, chat_id=TEST_CHANNEL, text="",parse_mode=None,files=None):
        payload = {
            'chat_id': chat_id,
            'text': text
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        ret = self.session.post(self.url, data=payload,files=files)

        if ret.status_code != 200:
            raise Exception(f'Failed to send message.{ret.text}')
        else:
            self.logger.info(f'Message sent successfully @ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}')
    
    def send_image(self, chat_id=TEST_CHANNEL, text="",files=None):
        payload = {
            'chat_id': chat_id,
            "caption": text
        }
        files = {
            'photo': files
        }

        url = f'https://api.telegram.org/bot{TOKEN}/sendPhoto'
        ret = self.session.post(url, data=payload,files=files)
        if ret.status_code != 200:
            raise Exception(f'Failed to send image.{ret.text}')
        else:
            self.logger.info(f'Image sent successfully @ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}')

    def get_update(self):
        url = url = f'https://api.telegram.org/bot{TOKEN}/getUpdates'
        ret = self.session.get(url)
        if ret.status_code != 200:
            raise Exception('Failed to get updates')
        else:
            print("Updates fetched successfully")
            self.logger.info(f'Updates fetched successfully @ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}')
            return ret.json()
        
if __name__ == "__main__":
    POSTMAN = TelegramPostman()

    ret= POSTMAN.get_update()
    print(ret)