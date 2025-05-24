from enum import Enum

class Sentiment(Enum):
    BULLISH = 1
    BEARISH = -1
    NEUTRAL = 0

class Direction(Enum):
    BUY = 1
    SELL = -1
    HOLD = 0


