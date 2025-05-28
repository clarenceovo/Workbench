from dataclasses import dataclass
import json


@dataclass
class SwapArbConfig:
    """
    Configuration for Swap Arbitrage.
    """
    exchange_a: str
    exchange_b: str
    exchange_a_market_list: list[str]
    exchange_b_market_list: list[str]
    long_leg_execution_mode: str  # "market" or "limit"
    short_leg_execution_mode: str  # "market" or "limit"
    upper_bound_entry_bp: float  # +20bp entry
    lower_bound_entry_bp: float  # -20bp entry
    exit_bp: float  # 20 (absolute) basis points exit
    max_trade_size_usd: float  # for check the USD value of the trade size , abort if larger than this value
    max_position: int  # 3 allow 3 swap positions
    is_depth_check: bool  # check the depth of the order book before placing orders

    def to_dict(self):
        return {
            "exchange_a": self.exchange_a,
            "exchange_b": self.exchange_b,
            "exchange_a_market_list": self.exchange_a_market_list,
            "exchange_b_market_list": self.exchange_b_market_list,
            "long_leg_execution_mode": self.long_leg_execution_mode,
            "short_leg_execution_mode": self.short_leg_execution_mode,
            "upper_bound_entry_bp": self.upper_bound_entry_bp,
            "lower_bound_entry_bp": self.lower_bound_entry_bp,
            "exit_bp": self.exit_bp,
            "max_trade_size_usd": self.max_trade_size_usd,
            "max_position": self.max_position,
            "is_depth_check": self.is_depth_check
        }

    def __str__(self):
        return json.dumps({
            "exchange_a": self.exchange_a,
            "exchange_b": self.exchange_b,
            "exchange_a_market_list": self.exchange_a_market_list,
            "exchange_b_market_list": self.exchange_b_market_list,
            "long_leg_execution_mode": self.long_leg_execution_mode,
            "short_leg_execution_mode": self.short_leg_execution_mode,
            "upper_bound_entry_bp": self.upper_bound_entry_bp,
            "lower_bound_entry_bp": self.lower_bound_entry_bp,
            "exit_bp": self.exit_bp,
            "max_trade_size_usd": self.max_trade_size_usd,
            "max_position": self.max_position,
            "is_depth_check": self.is_depth_check
        }, indent=4)
