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

__all__ = ['AverageTrueRange']



        

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


from ._averages import seeded_average


class AverageTrueRange:
    def __init__(self, parent, atr_period=14):
        self.parent = parent
        self.df = self.parent.df
        self.atr_period = atr_period

        self.parent.verify_period_sufficiency(self.atr_period + 1)

        self._calculate_atr()

    def _calculate_tr(self):
        """Calculate the True Range (TR) for each period."""
        self.df['High-Low'] = self.df['High'] - self.df['Low']
        self.df['High-PrevClose'] = abs(self.df['High'] - self.df['Close'].shift(1))
        self.df['Low-PrevClose'] = abs(self.df['Low'] - self.df['Close'].shift(1))
        self.df['TR'] = self.df[['High-Low', 'High-PrevClose', 'Low-PrevClose']].max(axis=1)

    def _calculate_atr(self):
        """Calculate the Average True Range (ATR) based on the True Range."""
        self._calculate_tr()
        self.df.loc[self.df.index[0], 'TR'] = float('nan')
        self.df['ATR'] = seeded_average(self.df['TR'], self.atr_period, start=self.atr_period, alpha=1 / self.atr_period)

    def get_atr(self):
        """Return the DataFrame with the ATR."""
        return self.df[['Date', 'Close', 'ATR']]

    def plot_atr(self):
        """Plot the ATR alongside the closing price."""
        plt.figure(figsize=(14, 8))

        plt.plot(self.df['Date'], self.df['Close'], label='Close Price', color='black')

        plt.plot(self.df['Date'], self.df['ATR'], label=f'ATR {self.atr_period}', color='blue')

        plt.title('Average True Range (ATR)')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.legend(loc='upper left')
        plt.grid(True)
        plt.show()

    def identify_volatility_shifts(self):
        """Identify and print periods of expanding or contracting volatility based on ATR changes."""
        self.df['ATR_Change'] = self.df['ATR'].diff()

        expanding_volatility = self.df[self.df['ATR_Change'] > 0]
        contracting_volatility = self.df[self.df['ATR_Change'] < 0]

        print("Expanding Volatility Periods:")
        print(expanding_volatility[['Date', 'Close', 'ATR', 'ATR_Change']].tail(10))

        print("\nContracting Volatility Periods:")
        print(contracting_volatility[['Date', 'Close', 'ATR', 'ATR_Change']].tail(10))

def __dir__():
    return __all__
