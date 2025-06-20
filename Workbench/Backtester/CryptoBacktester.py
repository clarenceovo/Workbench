import pandas as pd
import numpy as np
import vectorbt as vbt

class CryptoBacktester:
    def __init__(self, stop_loss_pct=0.1, initial_balance=10000):
        self.stop_loss_pct = stop_loss_pct
        self.initial_balance = initial_balance

    def run_backtest(self, data: pd.DataFrame, signal_fn):
        """
        Run backtest using vectorbt.
        signal_fn: function accepting data and returning entries, exits, and size arrays
        """
        entries, exits, size = signal_fn(data)
        price = data['close']

        self.portfolio = vbt.Portfolio.from_signals(
            close=price,
            entries=entries,
            exits=exits,
            size=size,
            init_cash=self.initial_balance,
            fees=0.001,
            sl_stop=self.stop_loss_pct
        )

    def calculate_metrics(self):
        if hasattr(self, 'portfolio'):
            stats = self.portfolio.stats()
            return {
                "Final Balance": self.portfolio.value().iloc[-1],
                "Sharpe Ratio": stats['Sharpe Ratio'],
                "Sortino Ratio": stats['Sortino Ratio']
            }
        return {}

    def export_results(self, filename="backtest_results.csv"):
        if hasattr(self, 'portfolio'):
            self.portfolio.value().to_csv(filename)