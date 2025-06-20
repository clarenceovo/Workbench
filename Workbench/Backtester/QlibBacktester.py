import os
import pandas as pd
import numpy as np
import gym
from gym import spaces
from stable_baselines3 import PPO
# Qlib model zoo imports
from qlib.contrib.model.gbdt import LGBModel
from qlib.contrib.model.xgboost import XGBoostModel
from qlib.contrib.model.linear import LinearModel
from qlib.contrib.model.tsdnn import TSDNNModel
from qlib.contrib.model.tft import TFTModel
from qlib.contrib.model.sfm import SFMModel
from qlib.contrib.model.tcn import TCNModel
from qlib.contrib.model.alstm import ALSTMModel
from qlib.contrib.model.gru import GRUModel
from qlib.contrib.model.lstm import LSTMModel
from qlib.contrib.model.gat import GATModel
from qlib.contrib.model.gcn import GCNModel
from qlib.contrib.model.transformer import TransformerModel
from qlib.contrib.model.tabnet import TabNetModel
from qlib.contrib.model.nbeats import NBeatsModel
from qlib.contrib.model.nhits import NHitsModel
from qlib.contrib.model.nrt import NRTModel
from qlib.contrib.model.san import SANModel
from qlib.contrib.model.dlinear import DLinearModel
from qlib.contrib.model.autoformer import AutoformerModel
from qlib.contrib.model.informer import InformerModel
from qlib.contrib.model.patchtst import PatchTSTModel
from qlib.contrib.model.tide import TiDEModel

class QlibFundingEnv(gym.Env):
    """
    Custom RL environment for trading based on multivariate data (OHLCV + alt data).
    Actions: 0 = very long, 1 = long, 2 = neutral, 3 = short, 4 = very short
    """
    def __init__(self, df, initial_balance=10000):
        super().__init__()
        self.data = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0  # -2 (very short), -1 (short), 0 (neutral), 1 (long), 2 (very long)
        self.action_space = spaces.Discrete(5)  # 0: very long, 1: long, 2: neutral, 3: short, 4: very short
        # Observation: all columns except datetime, symbol, and target columns
        obs_cols = [col for col in self.data.columns if col not in ['datetime', 'symbol', 'target', 'position']]
        self.obs_cols = obs_cols
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(len(obs_cols) + 1,), dtype=np.float32)

    def reset(self):
        self.data = self.data.sample(frac=1).reset_index(drop=True)
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        return self._get_obs()

    def _get_obs(self):
        row = self.data.iloc[self.current_step]
        obs = [row[col] for col in self.obs_cols]
        obs.append(self.position)
        return np.array(obs, dtype=np.float32)

    def step(self, action):
        done = False
        reward = 0
        row = self.data.iloc[self.current_step]
        # Map action to position
        action_to_position = {0: 2, 1: 1, 2: 0, 3: -1, 4: -2}
        prev_position = self.position
        self.position = action_to_position[action]
        position_change_penalty = -abs(self.position - prev_position) * 0.1
        reward = self.position * row.get('funding_rate', 0) * row.get('mark_price', 1) + position_change_penalty
        self.balance += reward
        self.current_step += 1
        if self.current_step >= len(self.data):
            done = True
        return self._get_obs(), reward, done, {}

    def render(self, mode='human'):
        print(f'Step: {self.current_step}, Balance: {self.balance}, Position: {self.position}')

def train_rl_agent_from_df(df, model_path='ppo_funding.zip', timesteps=10000):
    env = QlibFundingEnv(df)
    model = PPO('MlpPolicy', env, verbose=1, seed=42)
    model.learn(total_timesteps=timesteps)
    model.save(model_path)
    return model

def backtest_rl_agent_from_df(df, model_path='ppo_funding.zip'):
    env = QlibFundingEnv(df)
    model = PPO.load(model_path)
    obs = env.reset()
    done = False
    total_reward = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _ = env.step(action)
        total_reward += reward
    print(f'Backtest completed. Final balance: {env.balance}, Total reward: {total_reward}')
    return env.balance, total_reward

def backtest_rl_agent_by_bar(df, model_path='ppo_funding.zip'):
    """
    Backtest RL agent bar-by-bar, updating PnL and position at each step. Returns a DataFrame with bar-level results.
    """
    env = QlibFundingEnv(df)
    model = PPO.load(model_path)
    obs = env.reset()
    done = False
    results = []
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        prev_balance = env.balance
        prev_position = env.position
        obs, reward, done, _ = env.step(action)
        row = env.data.iloc[env.current_step - 1]
        results.append({
            'datetime': row['datetime'] if 'datetime' in row else env.current_step,
            'action': action,
            'position': env.position,
            'reward': reward,
            'balance': env.balance,
            'prev_balance': prev_balance,
            'prev_position': prev_position,
            'mark_price': row.get('mark_price', None),
            'funding_rate': row.get('funding_rate', None)
        })
    results_df = pd.DataFrame(results)
    print(f'Backtest by bar completed. Final balance: {env.balance}')
    return results_df
