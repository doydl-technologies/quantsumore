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

__all__ = ['RelativeStrengthIndex']


        

# Defer dependency imports until first use.
pd = Proxy("pandas")
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


from ._averages import seeded_average


class RelativeStrengthIndex:
    def __init__(self, parent, period=14):
        self.parent = parent
        self.df = self.parent.df
        self.period = period

        self.parent.verify_period_sufficiency(self.period + 1)

        self._calculate_rsi()
        self._detect_overbought_oversold()
        self._detect_divergence()
        self._detect_support_resistance()

    def _calculate_rsi(self):
        """Calculate the RSI based on the specified period."""
        delta = self.df['Close'].diff()
        gain = seeded_average(delta.clip(lower=0), self.period, start=self.period, alpha=1 / self.period)
        loss = seeded_average(-delta.clip(upper=0), self.period, start=self.period, alpha=1 / self.period)
        total = gain + loss
        self.df['RSI'] = (100 * gain / total).where(total != 0, 0)

    def _detect_overbought_oversold(self):
        """Detect overbought and oversold conditions."""
        self.df['Overbought'] = np.where(self.df['RSI'] > 70, 'Overbought', 'None')
        self.df['Oversold'] = np.where(self.df['RSI'] < 30, 'Oversold', 'None')

        # Signal conditions distinguish threshold crossings from sustained extremes.
        self.df['Sell_Signal'] = np.where((self.df['RSI'] > 70) & (self.df['RSI'].shift(1) <= 70), 'Sell Signal', 'None')
        self.df['Buy_Signal'] = np.where((self.df['RSI'] < 30) & (self.df['RSI'].shift(1) >= 30), 'Buy Signal', 'None')

    def _detect_divergence(self):
        """Detect divergence between RSI and price."""
        self.df['Price_Trend'] = np.where(self.df['Close'] > self.df['Close'].shift(1), 'up',
                                          np.where(self.df['Close'] < self.df['Close'].shift(1), 'down', 'flat'))
        self.df['RSI_Trend'] = np.where(self.df['RSI'] > self.df['RSI'].shift(1), 'up',
                                        np.where(self.df['RSI'] < self.df['RSI'].shift(1), 'down', 'flat'))

        # Label opposite one-period price and RSI changes as divergence.
        self.df['Divergence'] = np.where((self.df['Price_Trend'] == 'up') & (self.df['RSI_Trend'] == 'down'), 'Bearish Divergence',
                                         np.where((self.df['Price_Trend'] == 'down') & (self.df['RSI_Trend'] == 'up'), 'Bullish Divergence', 'None'))

    def _detect_support_resistance(self):
        """Label crossings of RSI thresholds 70 and 30 as heuristic resistance/support signals."""
        self.df['Support_Resistance'] = 'None'

        # Label crossings of 70 and 30; these are heuristic resistance/support signals.
        self.df['Support_Resistance'] = np.where((self.df['RSI'] >= 70) & (self.df['RSI'].shift(1) < 70), 'Resistance',
                                                 self.df['Support_Resistance'])
        self.df['Support_Resistance'] = np.where((self.df['RSI'] <= 30) & (self.df['RSI'].shift(1) > 30), 'Support',
                                                 self.df['Support_Resistance'])

    def get_rsi(self):
        """Return the DataFrame with the RSI and detected signals."""
        return self.df[['Date', 'Close', 'RSI', 'Overbought', 'Oversold', 'Sell_Signal', 'Buy_Signal', 'Divergence', 'Support_Resistance']]

    def plot_rsi(self):
        """Plot the RSI with overbought/oversold levels, divergence, and support/resistance levels."""
        plt.figure(figsize=(14, 8))

        plt.plot(self.df['Date'], self.df['RSI'], label='RSI', color='blue')
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')

        plt.scatter(self.df[self.df['Overbought'] == 'Overbought']['Date'],
                    self.df[self.df['Overbought'] == 'Overbought']['RSI'], color='red', label='Overbought Signal', marker='v')
        plt.scatter(self.df[self.df['Oversold'] == 'Oversold']['Date'],
                    self.df[self.df['Oversold'] == 'Oversold']['RSI'], color='green', label='Oversold Signal', marker='^')

        for div_type in ['Bearish Divergence', 'Bullish Divergence']:
            plt.scatter(self.df[self.df['Divergence'] == div_type]['Date'],
                        self.df[self.df['Divergence'] == div_type]['RSI'], label=div_type, marker='o', alpha=0.7)

        plt.title('Relative Strength Index (RSI)')
        plt.xlabel('Date')
        plt.ylabel('RSI Value')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

def __dir__():
    return __all__
