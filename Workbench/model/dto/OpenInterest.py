from dataclasses import dataclass
from datetime import datetime
from Workbench.transport.QuestClient import QuestBatch


@dataclass
class OpenInterest:
    timestamp: datetime
    exchange: str
    symbol: str
    open_interest: float

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "exchange": self.exchange,
            "symbol": self.symbol,
            "open_interest": self.open_interest
        }

    def to_json(self):
        import json
        return json.dumps(self.to_dict())

    def to_batch(self):
        try:
            return QuestBatch(
                topic="open_interest",
                symbol={"symbol": self.symbol, "exchange": self.exchange},
                columns={
                    "open_interest": self.open_interest
                },
                timestamp=self.timestamp,
            )
        except Exception as e:
            print(f"Error converting FundingRate to batch: {e}")
            return None