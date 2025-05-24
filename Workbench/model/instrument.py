import pandas as pd
import numpy as np
from Workbench.model.crypto_ticker import TickerSeries
import logging
class Instrument:
    def __init__(self, name: str, price_df: pd.DataFrame, import_freq: TickerSeries):
        """
        Initializes the Instrument with a base DataFrame and its frequency.

        Parameters:
        - name (str): Name of the instrument.
        - price_df (pd.DataFrame): Base DataFrame containing price data with at least a 'close' column.
        - import_freq (TickerSeries): Frequency of the base DataFrame.
        """
        self.name = name
        self.base_df = price_df.copy()
        self.base_freq = import_freq
        # Perform initial setup
        self.__post_init()

    def __post_init(self):
        """
        Post-initialization to aggregate data and calculate historical metrics.
        """
        # Define a mapping from TickerSeries to Pandas frequency strings
        frequency_mapping = {
            TickerSeries.DAILY.name: '1D',
            TickerSeries.H1.name: '1h',
            TickerSeries.H4.name: '4h',
            TickerSeries.H8.name: '8h',
            TickerSeries.M1.name: '1min',
            TickerSeries.M5.name: '5min',
            TickerSeries.M15.name: '15min',
            TickerSeries.M30.name: '30min',
        }

        # Define the order in which to process frequencies to handle dependencies
        # Start from the lowest frequency to the highest
        aggregation_order = [
            TickerSeries.M1,
            TickerSeries.M5,
            TickerSeries.M15,
            TickerSeries.M30,
            TickerSeries.H1,
            TickerSeries.H4,
            TickerSeries.H8,
            TickerSeries.DAILY,
        ]

        # Iterate through each frequency and process accordingly
        for freq in aggregation_order:
            if self.base_freq.name == freq.name:
                # Assign the base DataFrame to its corresponding frequency attribute
                setattr(self, f'price_df_{freq.name.lower()}', self.base_df)
                logging.debug(f"Assigned base DataFrame to frequency {freq.name}")

                # Calculate historical volatility and drift
                try:
                    processed_df = self.calc_hist_vol(getattr(self, f'price_df_{freq.name.lower()}'), freq)
                    setattr(self, f'price_df_{freq.name.lower()}', processed_df)
                    logging.debug(f"Calculated histosrical volatiltiy and drift for {freq.name}")
                except Exception as e:
                    logging.error(f"Error calculating historical volatility for {freq.name}: {e}")
            else:
                try:
                    aggregated_df = self.aggregate(self.base_df, frequency_mapping[freq.name])
                    setattr(self, f'price_df_{freq.name.lower()}', aggregated_df)
                    logging.debug(f"Aggregated base DataFrame to frequency {freq.name}")

                    # Calculate historical volatility and drift
                    processed_df = self.calc_hist_vol(aggregated_df, freq)
                    setattr(self, f'price_df_{freq.name.lower()}', processed_df)
                    logging.debug(f"Calculated historical volatiltiy and drift for {freq.name}")
                except Exception as e:
                    logging.error(f"Failed to process frequency {freq.name}: {e}")

    @staticmethod
    def aggregate(df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """
        Aggregates the DataFrame to the specified frequency.

        Parameters:
        - df (pd.DataFrame): DataFrame to be aggregated.
        - freq (str): Pandas frequency string (e.g., '1H', '4H', '1D').

        Returns:
        - pd.DataFrame: Resampled DataFrame.
        """
        try:
            logging.debug(f"**Aggregating DataFrame to frequency {freq}**")
            agg_df = df.resample(freq).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'volume_usd': 'sum'
            }).dropna()
            return agg_df
        except Exception as e:
            logging.error(f"Aggregation error for frequency {freq}: {e}")
            raise

    @staticmethod
    def calc_hist_vol(df: pd.DataFrame, obs_freq: TickerSeries) -> pd.DataFrame:
        """
        Calculates historical volatility and drift for different time horizons based on observation frequency.

        Parameters:
        - df (pd.DataFrame): DataFrame containing at least a 'close' column with price data.
        - obs_freq (TickerSeries): Observation frequency as defined in the TickerSeries Enum.

        Returns:
        - pd.DataFrame: Original DataFrame augmented with volatility and drift columns.
        """
        # Define observation and lookback periods
        freq_settings = {
            TickerSeries.DAILY.name: {'observations': 365, 'lookbacks': {'1m': 30, '3m': 92, '6m': 183, '1y': 365}},
            TickerSeries.H1.name: {'observations': 365 * 24,
                              'lookbacks': {'1m': 30 * 24, '3m': 92 * 24, '6m': 183 * 24, '1y': 365 * 24}},
            TickerSeries.H4.name: {'observations': 365 * 6,
                              'lookbacks': {'1m': 30 * 6, '3m': 92 * 6, '6m': 183 * 6, '1y': 365 * 6}},
            TickerSeries.H8.name: {'observations': 365 * 3,
                              'lookbacks': {'1m': 30 * 3, '3m': 92 * 3, '6m': 183 * 3, '1y': 365 * 3}},
            TickerSeries.M5.name: {'observations': 365 * 24 * 12,
                              'lookbacks': {'1m': 30 * 24 * 12, '3m': 92 * 24 * 12, '6m': 183 * 24 * 12,
                                            '1y': 365 * 24 * 12}},
            TickerSeries.M15.name: {'observations': 365 * 24 * 4,
                               'lookbacks': {'1m': 30 * 24 * 4, '3m': 92 * 24 * 4, '6m': 183 * 24 * 4,
                                             '1y': 365 * 24 * 4}},
            TickerSeries.M30.name: {'observations': 365 * 24 * 2,
                               'lookbacks': {'1m': 30 * 24 * 2, '3m': 92 * 24 * 2, '6m': 183 * 24 * 2,
                                             '1y': 365 * 24 * 2}},
            TickerSeries.M1.name: {'observations': 365 * 24 * 60,
                              'lookbacks': {'1m': 30 * 24 * 60, '3m': 92 * 24 * 60, '6m': 183 * 24 * 60,
                                            '1y': 365 * 24 * 60}},
        }

        settings = freq_settings.get(obs_freq.name)
        if not settings:
            raise ValueError(f"Observation frequency '{obs_freq}' not supported")

        observations = settings['observations']
        lookbacks = settings['lookbacks']

        # Calculate logarithmic returns
        df['ret'] = np.log(df['close'] / df['close'].shift(1))

        # Calculate rolling volatility and drift
        for period, window in lookbacks.items():
            vol_col = f'vol_{period}'
            drift_col = f'drift_{period}'
            df[vol_col] = df['ret'].rolling(window=window).std() * np.sqrt(observations)
            df[drift_col] = df['ret'].rolling(window=window).mean() * observations

        return df