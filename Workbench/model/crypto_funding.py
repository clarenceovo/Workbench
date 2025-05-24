from dataclasses import dataclass
from datetime import datetime

@dataclass
class CryptoFunding:
    tickerId: int
    fundingTime: datetime
    funding_rate: float
    mark_price: float

    def to_tuple(self):
        return (str(self.tickerId),self.fundingTime.strftime('%Y-%m-%d %H:%M:%S'),self.funding_rate,self.mark_price)