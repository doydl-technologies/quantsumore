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

__all__ = ['AroonIndicator']


        

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class AroonIndicator:
    def __init__(self, parent, period=25):
        self.parent = parent
        self.df = self.parent.df
        self.period = period

        self.parent.verify_period_sufficiency(self.period + 1)

        self._calculate_aroon()
        self._detect_trends()
        
    def _calculate_aroon(self):
        """Calculate the Aroon Up and Aroon Down indicators and store them in the DataFrame."""
        self.df['Aroon_Up'] = self.df['High'].rolling(window=self.period + 1).apply(
            lambda x: ((self.period - x[::-1].argmax()) / self.period) * 100, raw=True
        )

        self.df['Aroon_Down'] = self.df['Low'].rolling(window=self.period + 1).apply(
            lambda x: ((self.period - x[::-1].argmin()) / self.period) * 100, raw=True
        )

    def _detect_trends(self):
        """Detect trends and consolidations based on Aroon Up and Aroon Down interactions."""
        self.df['Trend_Signal'] = 'None'

        # Detect Aroon-Up crossing above Aroon-Down (Potential Uptrend Start)
        self.df['Trend_Signal'] = np.where(
            (self.df['Aroon_Up'] > self.df['Aroon_Down']) & (self.df['Aroon_Up'].shift(1) <= self.df['Aroon_Down'].shift(1)),
            'Uptrend Start',
            self.df['Trend_Signal']
        )

        # Detect Aroon-Down crossing above Aroon-Up (Potential Downtrend Start)
        self.df['Trend_Signal'] = np.where(
            (self.df['Aroon_Down'] > self.df['Aroon_Up']) & (self.df['Aroon_Down'].shift(1) <= self.df['Aroon_Up'].shift(1)),
            'Downtrend Start',
            self.df['Trend_Signal']
        )

        # Strong Uptrend: Aroon-Up between 70 and 100, Aroon-Down between 0 and 30
        self.df['Trend_Signal'] = np.where(
            (self.df['Aroon_Up'] >= 70) & (self.df['Aroon_Up'] <= 100) &
            (self.df['Aroon_Down'] >= 0) & (self.df['Aroon_Down'] <= 30),
            'Strong Uptrend',
            self.df['Trend_Signal']
        )

        # Strong Downtrend: Aroon-Down between 70 and 100, Aroon-Up between 0 and 30
        self.df['Trend_Signal'] = np.where(
            (self.df['Aroon_Down'] >= 70) & (self.df['Aroon_Down'] <= 100) &
            (self.df['Aroon_Up'] >= 0) & (self.df['Aroon_Up'] <= 30),
            'Strong Downtrend',
            self.df['Trend_Signal']
        )

        # Range Trading/Consolidation: Aroon-Up and Aroon-Down moving in parallel
        self.df['Trend_Signal'] = np.where(
            abs(self.df['Aroon_Up'] - self.df['Aroon_Down']) <= 10, # Consolidation tolerance in Aroon percentage points.
            'Range Trading/Consolidation',
            self.df['Trend_Signal']
        )

    def get_aroon(self):
        """Return the DataFrame with the Aroon Up, Aroon Down, and Trend Signal columns."""
        return self.df[['Date', 'Close', 'Aroon_Up', 'Aroon_Down', 'Trend_Signal']]

    def plot_aroon(self):
        """Plot the Aroon Up and Aroon Down indicators, highlighting trend signals."""
        plt.figure(figsize=(14, 8))
        plt.plot(self.df['Date'], self.df['Aroon_Up'], label='Aroon Up', color='green')
        plt.plot(self.df['Date'], self.df['Aroon_Down'], label='Aroon Down', color='red')
        plt.axhline(50, color='gray', linestyle='--', label='50 level')

        trend_signal_dates = self.df[self.df['Trend_Signal'] != 'None']['Date']
        for trend in ['Uptrend Start', 'Downtrend Start', 'Strong Uptrend', 'Strong Downtrend', 'Range Trading/Consolidation']:
            plt.scatter(self.df[self.df['Trend_Signal'] == trend]['Date'], 
                        self.df[self.df['Trend_Signal'] == trend]['Aroon_Up'],
                        label=trend, s=50, alpha=0.7)

        plt.title('Aroon Indicator with Trend Signals')
        plt.xlabel('Date')
        plt.ylabel('Aroon Value')
        plt.legend(loc='upper right')
        plt.grid(True)
        plt.show()
        
def __dir__():
    return __all__
