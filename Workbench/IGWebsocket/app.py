import os
import sys
import lightstreamer.client
from lightstreamer.client import LightstreamerClient, Subscription , SubscriptionListener, ConsoleLoggerProvider , ConsoleLogLevel
from IGRestAPI.IGRestAPIHandler import IGRestAPIHandler
from IGWSHandler import ItemUpdate
import time
import sys, logging

logging.basicConfig(level=logging.DEBUG, format="%(message)s", stream=sys.stdout)
loggerProvider = ConsoleLoggerProvider(ConsoleLogLevel.DEBUG)
LightstreamerClient.setLoggerProvider(loggerProvider)

class IGWebsocketClient:
    def __init__(self,username:str,password:str,api_key:str,topic) -> None:
        self.last_ts = None
        self.is_active = True
        self.__username = username
        self.__password = password
        self.__api_key = api_key
        self.topic = topic
        self.api_client = IGRestAPIHandler(self.__username,self.__password,self.__api_key)
        self.cst, self.x_token = self.api_client.get_cst_token()
        logging.debug(f"Got CST {self.cst} and X-SECURITY-TOKEN {self.x_token}")
        self.endpoint = self.api_client.get_endpoint()
        logging.debug(f"Got endpoint {self.endpoint}")

        if self.cst is None or self.x_token is None:
            raise Exception("Failed to get CST and X-SECURITY-TOKEN")
        self.client = LightstreamerClient(self.endpoint,None)

    def connect(self):
        self.client.connectionDetails.setUser(self.__username)
        self.client.connectionDetails.setPassword(f"CST-{self.cst}|XST-{self.x_token}")
        self.client.connect()
        if self.client.getStatus() == "DISCONNECTED":
            raise Exception("Failed to connect to Lightstreamer")
        self.set_subscription()
        while self.is_active:
            time.sleep(1)

    def set_subscription(self):
        for t in self.topic:
            logging.info(f"Subscribing to {t}")
            subscription = Subscription(
                mode="MERGE",  # MERGE mode for real-time updates
                items=[t],  # Market ID for Bitcoin CFD
                fields=[
                    'UTM', "DAY_OPEN_MID", "DAY_NET_CHG_MID", "DAY_PERC_CHG_MID", "DAY_HIGH", "DAY_LOW", "OFR_OPEN",
                    "OFR_HIGH", "OFR_LOW", "OFR_CLOSE",
                    "BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE"
                ]
            )
            subscription.addListener(ItemUpdate())
            self.client.subscribe(subscription)

if __name__ == '__main__':
    client = IGWebsocketClient(os.getenv('IG_USER'),os.getenv('IG_PASSWORD'),os.getenv('IG_API_KEY'),["CHART:CS.D.BITCOIN.CFD.IP:SECOND"])
    client.connect()