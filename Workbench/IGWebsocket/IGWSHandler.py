# Callback function to handle updates
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from CryptoTrader.IGWebsocket.dto.ChartUpdate import ChartUpdate
from lightstreamer.client import  SubscriptionListener
from CryptoTrader.transport.InfluxClient import InfluxClient
import logging
class ItemUpdate(SubscriptionListener):

    def __init__(self):
        self.influx_client = InfluxClient()

    def onItemUpdate(self, update):
        try:
            topic = update.getItemName()
            obj = ChartUpdate.from_ig_stream(topic,update)
            if obj:
                self.influx_client.write('ig_spread',obj.to_influx_point())

            #logging.info(f"Received update for {topic}")

        except Exception as e:
            print(f"Error: {e}")

    def onClearSnapshot(self, itemName, itemPos):
        pass

    def onCommandSecondLevelItemLostUpdates(self, lostUpdates, key):
        pass

    def onCommandSecondLevelSubscriptionError(self, code, message, key):
        pass

    def onEndOfSnapshot(self, itemName, itemPos):
        pass

    def onItemLostUpdates(self, itemName, itemPos, lostUpdates):
        pass

    def onListenEnd(self):
        pass

    def onListenStart(self):
        print("Listening for updates...")
        pass

    def onSubscription(self):
        print("Subscribed to updates")


    def onSubscriptionError(self, code, message):
        pass

    def onUnsubscription(self):
        pass

    def onRealMaxFrequency(self, frequency):
        pass
