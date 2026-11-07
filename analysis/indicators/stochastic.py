# -*- coding: utf-8 -*-
#
## ╭─────────────────────────────────────────────────────────────────────────────────────────────╮
## │  Library         : doydl's Finance API Client — quantsumore                                 │
## │                                                                                             │
## │  Project Status  : Retired on July 27, 2025. Deprecated and unsupported.                    │
## │                    Preserved for historical reference only. No ongoing development,         │
## │                    compatibility fixes, endpoint repairs, support, or security updates      │
## │                    are planned. Corrective archival releases do not resume maintenance.     │
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
## ╰─────────────────────────────────────────────────────────────────────────────────────────────╯
#

from ...proxy import Proxy

__all__ = ['FastStochasticOscillator']



# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class FastStochasticOscillator:
    def __init__(self, parent, k_period=14, d_period=3):
        self.parent = parent
        self.df = self.parent.df
        self.k_period = k_period
        self.d_period = d_period

        max_period = self.k_period + self.d_period - 1
        self.parent.verify_period_sufficiency(max_period)

        self._calculate_stochastic()
        self._detect_overbought_oversold()
        self._detect_crosses()
        self._detect_divergence()

    def _calculate_stochastic(self):
        """Calculate the %K and %D lines of the Stochastic Oscillator."""
        self.df['Lowest_Low'] = self.df['Low'].rolling(window=self.k_period).min()
        self.df['Highest_High'] = self.df['High'].rolling(window=self.k_period).max()

        span = self.df['Highest_High'] - self.df['Lowest_Low']
        self.df['%K'] = (100 * (self.df['Close'] - self.df['Lowest_Low']) / span).where(span != 0, 0)

        self.df['%D'] = self.df['%K'].rolling(window=self.d_period).mean()
        self.df['%K'] = self.df['%K'].where(self.df['%D'].notna())

    def _detect_overbought_oversold(self):
        """Detect overbought and oversold conditions."""
        self.df['Overbought'] = np.where(self.df['%K'] > 80, 'Overbought', 'None')
        self.df['Oversold'] = np.where(self.df['%K'] < 20, 'Oversold', 'None')

    def _detect_crosses(self):
        """Detect intersections of %K and %D lines, signaling potential momentum shifts."""
        self.df['Cross'] = 'None'

        # Detect when %K crosses above %D (Bullish Signal)
        self.df['Cross'] = np.where(
            (self.df['%K'] > self.df['%D']) & (self.df['%K'].shift(1) <= self.df['%D'].shift(1)),
            'Bullish Cross',
            self.df['Cross']
        )

        # Detect when %K crosses below %D (Bearish Signal)
        self.df['Cross'] = np.where(
            (self.df['%K'] < self.df['%D']) & (self.df['%K'].shift(1) >= self.df['%D'].shift(1)),
            'Bearish Cross',
            self.df['Cross']
        )

    def _detect_divergence(self):
        """Detect divergence between the Stochastic Oscillator and price."""
        self.df['Price_Trend'] = np.where(self.df['Close'] > self.df['Close'].shift(1), 'up',
                                          np.where(self.df['Close'] < self.df['Close'].shift(1), 'down', 'flat'))
        self.df['Stoch_Trend'] = np.where(self.df['%K'] > self.df['%K'].shift(1), 'up',
                                          np.where(self.df['%K'] < self.df['%K'].shift(1), 'down', 'flat'))

        # Label opposite one-period price and stochastic changes as heuristic divergence.
        self.df['Divergence'] = np.where((self.df['Price_Trend'] == 'up') & (self.df['Stoch_Trend'] == 'down'), 'Bearish Divergence',
                                         np.where((self.df['Price_Trend'] == 'down') & (self.df['Stoch_Trend'] == 'up'), 'Bullish Divergence', 'None'))

    def get_stochastic(self):
        """Return the DataFrame with the Stochastic Oscillator %K, %D lines, and detected signals."""
        return self.df[['Date', 'Close', '%K', '%D', 'Overbought', 'Oversold', 'Cross', 'Divergence']]

    def plot_stochastic(self):
        """Plot the Stochastic Oscillator %K and %D lines, highlighting overbought/oversold conditions, crosses, and divergence."""
        plt.figure(figsize=(14, 8))

        plt.plot(self.df['Date'], self.df['%K'], label='%K Line', color='blue')
        plt.plot(self.df['Date'], self.df['%D'], label='%D Line', color='red')

        plt.axhline(80, color='red', linestyle='--', label='Overbought (80)')
        plt.axhline(20, color='green', linestyle='--', label='Oversold (20)')

        plt.scatter(self.df[self.df['Overbought'] == 'Overbought']['Date'],
                    self.df[self.df['Overbought'] == 'Overbought']['%K'], color='red', label='Overbought Signal', marker='v')
        plt.scatter(self.df[self.df['Oversold'] == 'Oversold']['Date'],
                    self.df[self.df['Oversold'] == 'Oversold']['%K'], color='green', label='Oversold Signal', marker='^')

        plt.scatter(self.df[self.df['Cross'] == 'Bullish Cross']['Date'],
                    self.df[self.df['Cross'] == 'Bullish Cross']['%K'], color='green', label='Bullish Cross', marker='o')
        plt.scatter(self.df[self.df['Cross'] == 'Bearish Cross']['Date'],
                    self.df[self.df['Cross'] == 'Bearish Cross']['%K'], color='red', label='Bearish Cross', marker='o')

        for div_type in ['Bearish Divergence', 'Bullish Divergence']:
            plt.scatter(self.df[self.df['Divergence'] == div_type]['Date'],
                        self.df[self.df['Divergence'] == div_type]['%K'], label=div_type, marker='x', alpha=0.7)

        plt.title('Stochastic Oscillator with Overbought/Oversold, Crosses, and Divergence')
        plt.xlabel('Date')
        plt.ylabel('Stochastic Value')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

def __dir__():
    return __all__
