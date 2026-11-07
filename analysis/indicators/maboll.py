# -*- coding: utf-8 -*-
#
## ╭────────────────────────────────────────────────────────────────────────────────────────────╮
## │  Library         : doydl's Finance API Client — quantsumore                                 │
## │                                                                                             │
## │                                                                                             │
## │  Description     : `quantsumore` is a comprehensive Python library designed to streamline   │
## │                    the process of accessing and analyzing real-time financial data across   │
## │                    various markets. It provides specialized API clients to fetch data       │
## │                    from multiple financial instruments, including:                          │
## │                      - Cryptocurrencies                                                     │
## │                      - Equities and Stock Markets                                           │
## │                      - Foreign Exchange (Forex)                                             │
## │                      - Treasury Instruments                                                 │
## │                      - Consumer Price Index (CPI) Metrics                                   │
## │                                                                                             │
## │                    The library offers a unified interface for retrieving diverse financial  │
## │                    data, enabling users to perform in-depth financial and technical         │
## │                    analysis. Whether you're developing trading algorithms, conducting       │
## │                    market research, or building financial dashboards, `quantsumore` serves  │
## │                    as a reliable and efficient tool in your data pipeline.                  │
## │                                                                                             │
## │                                                                                             │
## │  Key Features    : - Real-time data retrieval from multiple financial markets               │
## │                    - Support for various financial instruments and metrics                  │
## │                    - Simplified API clients for ease of integration                         │
## │                    - Designed for both personal and non-commercial use                      │
## │                                                                                             │
## │                                                                                             │
## │  Legal Disclaimer: `quantsumore` is an independent Python library and is not affiliated     │
## │                    with any financial institutions or data providers. Likewise, doydl       │
## │                    technologies is not affiliated with, endorsed by, or sponsored by any    │
## │                    government, corporate, or financial institutions. Users should verify    │
## │                    the accuracy of the data obtained and consult professional advice        │
## │                    before making investment decisions.                                      │
## │                                                                                             │
## │                                                                                             │
## │  Copyright       : © 2023–2025 by doydl technologies. All rights reserved.                  │
## │                                                                                             │
## │                                                                                             │
## │  License         : Licensed under the Apache License, Version 2.0 (the "License");          │
## │                    you may not use this file except in compliance with the License.         │
## │                    You may obtain a copy of the License at:                                 │
## │                                                                                             │
## │                        http://www.apache.org/licenses/LICENSE-2.0                           │
## │                                                                                             │
## │                    Unless required by applicable law or agreed to in writing, software      │
## │                    distributed under the License is distributed on an "AS IS" BASIS,        │
## │                    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or          │
## │                    implied. See the License for the specific language governing             │
## │                    permissions and limitations under the License.                           │
## ╰────────────────────────────────────────────────────────────────────────────────────────────╯
#

from ...proxy import Proxy

__all__ = ['MovingAveragesAndBollingerBands']



        

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


from ._averages import seeded_average


class MovingAveragesAndBollingerBands:
    def __init__(self, parent, sma_period=20, ema_period=20, bb_period=20, bb_std=2):
        self.parent = parent
        self.df = self.parent.df
        self.sma_period = sma_period
        self.ema_period = ema_period
        self.bb_period = bb_period
        self.bb_std = bb_std

        max_period = max(self.sma_period, self.ema_period, self.bb_period)
        self.parent.verify_period_sufficiency(max_period)

        self._calculate_sma()
        self._calculate_ema()
        self._calculate_bollinger_bands()
        self._detect_crossovers()

    def _calculate_sma(self):
        self.df['SMA'] = self.df['Close'].rolling(window=self.sma_period).mean()

    def _calculate_ema(self):
        self.df['EMA'] = seeded_average(self.df['Close'], self.ema_period)

    def _calculate_bollinger_bands(self):
        self.df['BB_Middle'] = self.df['Close'].rolling(window=self.bb_period).mean()
        deviation = self.df['Close'].rolling(window=self.bb_period).std(ddof=0)
        self.df['BB_Upper'] = self.df['BB_Middle'] + self.bb_std * deviation
        self.df['BB_Lower'] = self.df['BB_Middle'] - self.bb_std * deviation

    def _detect_crossovers(self):
        self.df['Signal'] = 'None'

        # Detect when EMA crosses above SMA (Bullish Crossover)
        self.df['Signal'] = np.where((self.df['EMA'] > self.df['SMA']) & (self.df['EMA'].shift(1) <= self.df['SMA'].shift(1)),
                                     'Buy', self.df['Signal'])

        # Detect when EMA crosses below SMA (Bearish Crossover)
        self.df['Signal'] = np.where((self.df['EMA'] < self.df['SMA']) & (self.df['EMA'].shift(1) >= self.df['SMA'].shift(1)),
                                     'Sell', self.df['Signal'])

    def get_indicators(self):
        return self.df[['Date', 'Close', 'SMA', 'EMA', 'BB_Middle', 'BB_Upper', 'BB_Lower', 'Signal']]

    def plot_indicators(self):
        plt.figure(figsize=(14, 8))
        plt.plot(self.df['Date'], self.df['Close'], label='Close Price', color='black')
        plt.plot(self.df['Date'], self.df['SMA'], label=f'SMA {self.sma_period}', color='blue')
        plt.plot(self.df['Date'], self.df['EMA'], label=f'EMA {self.ema_period}', color='red')
        plt.plot(self.df['Date'], self.df['BB_Middle'], label='Bollinger Middle Band', color='green')
        plt.plot(self.df['Date'], self.df['BB_Upper'], label='Bollinger Upper Band', color='orange')
        plt.plot(self.df['Date'], self.df['BB_Lower'], label='Bollinger Lower Band', color='orange')
        plt.fill_between(self.df['Date'], self.df['BB_Upper'], self.df['BB_Lower'], color='orange', alpha=0.1)

        plt.scatter(self.df[self.df['Signal'] == 'Buy']['Date'],
                    self.df[self.df['Signal'] == 'Buy']['Close'], color='green', label='Buy Signal', marker='^')
        plt.scatter(self.df[self.df['Signal'] == 'Sell']['Date'],
                    self.df[self.df['Signal'] == 'Sell']['Close'], color='red', label='Sell Signal', marker='v')

        plt.title('SMA, EMA, Bollinger Bands, and Signals')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

def __dir__():
    return __all__
