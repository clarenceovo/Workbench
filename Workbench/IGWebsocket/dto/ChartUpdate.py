import logging
from dataclasses import dataclass
from influxdb_client import Point
from datetime import datetime
@dataclass
class ChartUpdate:
    topic: str
    utm: int
    day_open_mid: float
    day_net_chg_mid: float
    day_perc_chg_mid: float
    day_high: float
    day_low: float
    ofr_open: float
    ofr_high: float
    ofr_low: float
    ofr_close: float
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    time :datetime = None
    current_mid:float = None
    bid_to_mid:float = None
    ask_to_mid:float = None


    @classmethod
    def from_ig_stream(cls,topic, update_obj):
        try:
            return cls(
                topic=topic,
                utm=int(update_obj.getValue('UTM')) if update_obj.getValue('UTM') != "" else None,
                day_open_mid=float(update_obj.getValue('DAY_OPEN_MID')) if update_obj.getValue(
                    'DAY_OPEN_MID') != "" else None,
                day_net_chg_mid=float(update_obj.getValue('DAY_NET_CHG_MID')) if update_obj.getValue(
                    'DAY_NET_CHG_MID') != "" else None,
                day_perc_chg_mid=float(update_obj.getValue('DAY_PERC_CHG_MID')) if update_obj.getValue(
                    'DAY_PERC_CHG_MID') != "" else None,
                day_high=float(update_obj.getValue('DAY_HIGH')) if update_obj.getValue('DAY_HIGH') != "" else None,
                day_low=float(update_obj.getValue('DAY_LOW')) if update_obj.getValue('DAY_LOW') != "" else None,
                ofr_open=float(update_obj.getValue('OFR_OPEN')) if update_obj.getValue('OFR_OPEN') != "" else None,
                ofr_high=float(update_obj.getValue('OFR_HIGH')) if update_obj.getValue('OFR_HIGH') != "" else None,
                ofr_low=float(update_obj.getValue('OFR_LOW')) if update_obj.getValue('OFR_LOW') != "" else None,
                ofr_close=float(update_obj.getValue('OFR_CLOSE')) if update_obj.getValue('OFR_CLOSE') != "" else None,
                bid_open=float(update_obj.getValue('BID_OPEN')) if update_obj.getValue('BID_OPEN') != "" else None,
                bid_high=float(update_obj.getValue('BID_HIGH')) if update_obj.getValue('BID_HIGH') != "" else None,
                bid_low=float(update_obj.getValue('BID_LOW')) if update_obj.getValue('BID_LOW') != "" else None,
                bid_close=float(update_obj.getValue('BID_CLOSE')) if update_obj.getValue('BID_CLOSE') != "" else None

            )
        except Exception as e:
            logging.error(e)
    def __post_init__(self):
        self.current_mid = self.day_open_mid + self.day_net_chg_mid if self.day_open_mid and self.day_net_chg_mid is not None else None
        self.bid_to_mid = self.current_mid - self.bid_close if self.current_mid and self.bid_close is not None else None
        self.ask_to_mid = self.ofr_close - self.current_mid if self.ofr_close and self.current_mid is not None else None
        self.time  = datetime.utcfromtimestamp(self.utm/1000)

    def get_product(self,topic):
        return topic.split(":")[1].split('.')[2]

    def to_influx_point(self):
        try:
            point = ((Point(f"spread_{self.get_product(self.topic)}").tag("topic",self.topic).
                     field("utm",self.utm).
                     field("day_open_mid",self.day_open_mid)
                     .field("day_net_chg_mid",self.day_net_chg_mid).
                     field("day_high",self.day_high).
                      field("day_low",self.day_low).
                     field("ofr_open",self.ofr_open).
                      field("ofr_high",self.ofr_high).
                     field("ofr_low",self.ofr_low).
                     field("ofr_close",self.ofr_close).
                     field("bid_open",self.bid_open).
                     field("bid_high",self.bid_high)
                     .field("bid_low",self.bid_low).
                     field("bid_close",self.bid_close).
                     field("current_mid",self.current_mid).
                     field("bid_to_mid",self.bid_to_mid).
                     field("ask_to_mid",self.ask_to_mid)).
                     time(self.time))
            return point
        except:
            return None
    def __str__(self):
        return f"Topic:{self.topic} bidSpd:{self.bid_to_mid} askSpd:{self.ask_to_mid} UTM: {self.utm}, DAY_OPEN_MID: {self.day_open_mid}, DAY_NET_CHG_MID: {self.day_net_chg_mid}, DAY_PERC_CHG_MID: {self.day_perc_chg_mid}, DAY_HIGH: {self.day_high}, DAY_LOW: {self.day_low}, OFR_OPEN: {self.ofr_open}, OFR_HIGH: {self.ofr_high}, OFR_LOW: {self.ofr_low}, OFR_CLOSE: {self.ofr_close}, BID_OPEN: {self.bid_open}, BID_HIGH: {self.bid_high}, BID_LOW: {self.bid_low}, BID_CLOSE: {self.bid_close}"