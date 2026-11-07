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

__all__ = ['AccumulationDistributionLine']


        

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class AccumulationDistributionLine:
    def __init__(self, parent):
        self.parent = parent
        self.df = self.parent.df

        self._calculate_ad_line()
        
    def _calculate_ad_line(self):
        """Calculate the Accumulation/Distribution (A/D) Line and store it in the DataFrame."""
        # Money Flow Multiplier (MFM).
        self.df['MFM'] = ((self.df['Close'] - self.df['Low']) - (self.df['High'] - self.df['Close'])) / (self.df['High'] - self.df['Low'])
        
        # A zero price range contributes no money flow.
        self.df['MFM'] = self.df['MFM'].fillna(0)
        
        self.df['MFV'] = self.df['MFM'] * self.df['Volume']
        
        self.df['AD_Line'] = self.df['MFV'].cumsum()

    def get_ad_line(self):
        """Return the DataFrame with the A/D Line column."""
        return self.df[['Date', 'Close', 'Volume', 'AD_Line']]

    def detect_divergence(self):
        """
        Detect divergence between the A/D Line and price.
        
        :return: DataFrame with detected divergence points.
        """
        self.df['Price_Trend'] = np.where(self.df['Close'] > self.df['Close'].shift(1), 'up', 
                                          np.where(self.df['Close'] < self.df['Close'].shift(1), 'down', 'flat'))
        self.df['AD_Trend'] = np.where(self.df['AD_Line'] > self.df['AD_Line'].shift(1), 'up', 
                                       np.where(self.df['AD_Line'] < self.df['AD_Line'].shift(1), 'down', 'flat'))
        
        # Label opposite one-period price and A/D changes as heuristic divergence.
        self.df['Divergence'] = np.where((self.df['Price_Trend'] == 'up') & (self.df['AD_Trend'] == 'down'), 'bearish',
                                         np.where((self.df['Price_Trend'] == 'down') & (self.df['AD_Trend'] == 'up'), 'bullish', 'none'))
        
        divergence_df = self.df[self.df['Divergence'] != 'none'][['Date', 'Close', 'AD_Line', 'Divergence']]
        
        if divergence_df.empty:
            print("No divergence detected between A/D Line and price.")                      
        return divergence_df

    def plot_ad_line_with_divergence(self):
        """Plot the A/D Line and closing price with highlighted divergence points."""
        fig, ax1 = plt.subplots(figsize=(14, 8))

        ax1.set_xlabel('Date')
        ax1.set_ylabel('Close Price', color='tab:blue')
        ax1.plot(self.df['Date'], self.df['Close'], color='tab:blue', label='Close Price')
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Accumulation/Distribution Line (A/D Line)', color='tab:green')
        ax2.plot(self.df['Date'], self.df['AD_Line'], color='tab:green', label='A/D Line')
        ax2.tick_params(axis='y', labelcolor='tab:green')

        divergence_points = self.df[self.df['Divergence'] != 'none']
        ax1.scatter(divergence_points['Date'], divergence_points['Close'], color='red', label='Divergence', zorder=5)

        fig.tight_layout()
        plt.title('Accumulation/Distribution Line (A/D Line) and Close Price with Divergence')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

def __dir__():
    return __all__
