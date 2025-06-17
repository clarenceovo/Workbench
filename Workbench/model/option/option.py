from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import math

from scipy.interpolate import griddata
from scipy.interpolate import interp1d
from scipy.stats import norm
import numpy as np

@dataclass
class Option:
    contractSymbol: str
    strike: float
    lastPrice: float
    bid: float
    ask: float
    change: float
    percentChange: float
    openInterest: int
    impliedVolatility: float
    inTheMoney: bool
    lastTradeDate: datetime
    expiration: datetime
    currency:str
    volume: int = 0

    def __post_init__(self):
        #time zone set to be EST for now

        pass

    def to_dict(self):
        return {
            'contractSymbol': self.contractSymbol,
            'strike': self.strike,
            'lastPrice': self.lastPrice if math.isfinite(self.lastPrice) else None,
            'bid': self.bid if math.isfinite(self.bid) else None,
            'ask': self.ask if math.isfinite(self.ask) else None,
            'volume': self.volume if math.isfinite(self.volume) else None,
            'change': self.change if math.isfinite(self.change) else None,
            'percentChange': self.percentChange if math.isfinite(self.percentChange) else None,
            'openInterest': self.openInterest if math.isfinite(self.openInterest) else None,
            'impliedVolatility': str(self.impliedVolatility) if math.isfinite(self.impliedVolatility) else None,
            'inTheMoney': self.inTheMoney,
            'lastTradeDate': self.lastTradeDate.strftime('%Y-%m-%d'),
            'expiration': self.expiration.strftime('%Y-%m-%d'),
            'currency': self.currency.name
        }




@dataclass
class OptionChain:
    expirationDate: datetime
    calls:List[Option]
    puts:List[Option]
    markPrice: Optional[float] = None

    @property
    def call_strikes(self):
        return [call.strike for call in self.calls]

    @property
    def put_strikes(self):
        return [put.strike for put in self.puts]

    @property
    def oi_profile(self):
        oi_dict = {}
        for call in self.calls:
            if call.strike not in oi_dict:
                oi_dict[call.strike] = {'call_oi': 0, 'put_oi': 0}
            oi_dict[call.strike]['call_oi'] += call.openInterest

        for put in self.puts:
            if put.strike not in oi_dict:
                oi_dict[put.strike] = {'call_oi': 0, 'put_oi': 0}
            oi_dict[put.strike]['put_oi'] += put.openInterest

        return oi_dict

    @property
    def total_oi(self):
        oi_dict = self.oi_profile
        # Combine call and put open interest
        total_oi_dict = {strike: data['call_oi'] + data['put_oi'] for strike, data in oi_dict.items()}
        return total_oi_dict

    @property
    def chain_max_pain(self):
        total_pain = {}
        usd_notional = {}
        call_pain = {}
        put_pain = {}

        for strike in self.call_strikes + self.put_strikes:
            total_pain[strike] = 0
            usd_notional[strike] = 0
            call_pain[strike] = 0
            put_pain[strike] = 0

            for call in self.calls:
                call_pain[strike] += call.openInterest * max(0, strike - self.markPrice)
                usd_notional[strike] += call.openInterest * strike

            for put in self.puts:
                put_pain[strike] += put.openInterest * max(0, self.markPrice - strike)
                usd_notional[strike] += put.openInterest * strike

            total_pain[strike] = call_pain[strike] + put_pain[strike]

        max_pain_strike_call = min(call_pain, key=call_pain.get)
        max_pain_strike_put = min(put_pain, key=put_pain.get)

        # Decide which side to choose
        if call_pain[max_pain_strike_call] > put_pain[max_pain_strike_put]:
            max_pain_strike = max_pain_strike_call
        else:
            max_pain_strike = max_pain_strike_put

        return max_pain_strike, usd_notional[max_pain_strike], call_pain[max_pain_strike], put_pain[max_pain_strike]

    def to_dict(self):
        return {
            'expirationDate':self.expirationDate.strftime('%Y-%m-%d'),
            'calls': [call.to_dict() for call in self.calls],
            'puts': [put.to_dict() for put in self.puts],
            'markPrice':self.markPrice
        }

    @property
    def oi_ratio(self):
        return [call.openInterest / put.openInterest for call,put in zip(self.calls,self.puts)]

    def extract_risk_neutral_density(self, risk_free_rate=0.05,observation_period=252.0):
        strikes = np.array([option.strike for option in self.calls + self.puts])
        implied_vols = np.array([option.impliedVolatility for option in self.calls + self.puts])
        expirations = (self.expirationDate - datetime.now()).days / observation_period

        # Remove duplicates
        unique_strikes, unique_indices = np.unique(strikes, return_index=True)
        strikes = strikes[unique_indices]
        implied_vols = implied_vols[unique_indices]

        # Calculate the forward price
        forward_price = self.markPrice * np.exp(risk_free_rate * expirations)

        # Interpolate implied volatilities
        #vol_interp = interp1d(strikes, implied_vols, kind='cubic', fill_value="extrapolate")


        # Calculate the second derivative of the call price with respect to strike price
        d2_call_prices = []
        for strike in strikes:
            d1 = (np.log(forward_price / strike) + (implied_vols[0] ** 2 / 2) * expirations) / (
                        implied_vols[0] * np.sqrt(expirations))
            d2 = d1 - implied_vols[0] * np.sqrt(expirations)
            call_price = forward_price * norm.cdf(d1) - strike * np.exp(-risk_free_rate * expirations) * norm.cdf(d2)
            d2_call_prices.append(call_price)

        d2_call_prices = np.gradient(np.gradient(d2_call_prices, strikes), strikes)

        # Calculate the risk-neutral density
        risk_neutral_density = np.exp(risk_free_rate * expirations) * d2_call_prices

        return strikes, risk_neutral_density

    def calculate_expected_price_range(self, risk_free_rate=0.01,observation_period=252.0):
        strikes, rnd = self.extract_risk_neutral_density(risk_free_rate,observation_period)

        # Calculate the expected price
        expected_price = np.trapz(strikes * rnd, strikes)

        # Calculate the standard deviation of the price
        variance = np.trapz((strikes - expected_price) ** 2 * rnd, strikes)
        std_dev = np.sqrt(variance)

        return expected_price, expected_price - std_dev, expected_price + std_dev

@dataclass
class OptionChains:
    symbol: str
    markPrice:float
    chains:List[OptionChain]


    def get_chain_by_date(self,date:datetime)->OptionChain:
        for chain in self.chains:
            if chain.expirationDate == date:
                return chain
        return None

    def calculate_volatility_skew(self, date: datetime):
        chain = self.get_chain_by_date(date)
        if chain is None:
            return None

        strikes = []
        implied_vols = []

        for option in chain.calls + chain.puts:
            strikes.append(option.strike)
            implied_vols.append(option.impliedVolatility)

        if not strikes or not implied_vols:
            return None

        # Calculate the skew as the difference between the highest and lowest implied volatilities
        skew = max(implied_vols) - min(implied_vols)
        return round(skew,4)

    def calculate_volatility_surface(self):
        strikes = []
        expirations = []
        implied_vols = []

        for chain in self.chains:
            for option in chain.calls + chain.puts:
                strikes.append(option.strike)
                expirations.append((chain.expirationDate - datetime.now()).days)
                implied_vols.append(option.impliedVolatility)

        if not strikes or not implied_vols:
            return None

        # Create a grid for strikes and expirations
        strike_grid = np.linspace(min(strikes), max(strikes), 100)
        expiration_grid = np.linspace(min(expirations), max(expirations), 100)
        strike_grid, expiration_grid = np.meshgrid(strike_grid, expiration_grid)

        # Interpolate the implied volatilities over the grid
        vol_surface = griddata((strikes, expirations), implied_vols, (strike_grid, expiration_grid), method='cubic')

        return strike_grid, expiration_grid, vol_surface





