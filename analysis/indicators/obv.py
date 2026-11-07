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

__all__ = ['OnBalanceVolume']


     

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class OnBalanceVolume:
    def __init__(self, parent):
        self.parent = parent
        self.df = self.parent.df

        self._calculate_obv()

    def _calculate_obv(self):
        """Calculate the On-Balance Volume (OBV) and store it in the DataFrame."""
        self.df['OBV'] = 0
        
        change = np.sign(self.df['Close'].diff()).fillna(0)
        self.df['OBV'] = (change * self.df['Volume']).cumsum() + self.df['Volume'].iloc[0]

    def get_obv(self):
        """Return the DataFrame with the OBV column."""
        return self.df[['Date', 'Close', 'Volume', 'OBV']]

    def detect_divergence(self):
        """Return rows labeled by opposite one-period price and OBV changes.

        These divergence labels are legacy heuristics, not independently verified
        predictions of price direction.
        """
        self.df['Price_Trend'] = np.where(self.df['Close'] > self.df['Close'].shift(1), 'up', 
                                          np.where(self.df['Close'] < self.df['Close'].shift(1), 'down', 'flat'))
        self.df['OBV_Trend'] = np.where(self.df['OBV'] > self.df['OBV'].shift(1), 'up', 
                                        np.where(self.df['OBV'] < self.df['OBV'].shift(1), 'down', 'flat'))
        
        # Label opposite one-period price and OBV changes as divergence.
        self.df['Divergence'] = np.where((self.df['Price_Trend'] == 'up') & (self.df['OBV_Trend'] == 'down'), 'bearish',
                                         np.where((self.df['Price_Trend'] == 'down') & (self.df['OBV_Trend'] == 'up'), 'bullish', 'none'))
        
        divergence_df = self.df[self.df['Divergence'] != 'none'][['Date', 'Close', 'OBV', 'Divergence']]
        
        if divergence_df.empty:
            print("No divergence detected between OBV and price.")      
        return divergence_df

    def plot_obv_with_divergence(self):
        """Plot OBV and closing price with highlighted divergence points."""
        fig, ax1 = plt.subplots(figsize=(14, 8))

        ax1.set_xlabel('Date')
        ax1.set_ylabel('Close Price', color='tab:blue')
        ax1.plot(self.df['Date'], self.df['Close'], color='tab:blue', label='Close Price')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('On-Balance Volume (OBV)', color='tab:orange')
        ax2.plot(self.df['Date'], self.df['OBV'], color='tab:orange', label='OBV')
        ax2.tick_params(axis='y', labelcolor='tab:orange')

        divergence_points = self.df[self.df['Divergence'] != 'none']
        ax1.scatter(divergence_points['Date'], divergence_points['Close'], color='red', label='Divergence', zorder=5)

        fig.tight_layout()
        plt.title('On-Balance Volume (OBV) and Close Price with Divergence')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

def __dir__():
    return __all__
