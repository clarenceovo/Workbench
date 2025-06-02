from dataclasses import dataclass
from datetime import datetime
from Workbench.transport.QuestClient import QuestBatch

@dataclass
class FundingRate:
    timestamp: datetime
    exchange: str
    symbol: str
    annual_funding_rate: float

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "annual_funding_rate": self.annual_funding_rate
        }

    def to_json(self):
        import json
        return json.dumps(self.to_dict())

    def to_batch(self):
        try:
            return QuestBatch(
                topic="funding_rate",
                symbol={"symbol": self.symbol, "exchange": self.exchange},
                columns={
                    "annual_funding_rate": self.annual_funding_rate
                },
                timestamp=self.timestamp,
            )
        except Exception as e:
            print(f"Error converting FundingRate to batch: {e}")
            return None