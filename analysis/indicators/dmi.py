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

__all__ = ['DirectionalMovementIndex']


        

# Defer dependency imports until first use.
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class DirectionalMovementIndex:
    def __init__(self, parent, period=14, adx_threshold=25):
        self.parent = parent
        self.df = self.parent.df
        self.period = period
        self.adx_threshold = adx_threshold

        self.parent.verify_period_sufficiency(2 * self.period)
        self._calculate_indicators()
        self._calculate_signals()

    def _calculate_indicators(self):
        self.df['High-Low'] = self.df['High'] - self.df['Low']
        self.df['High-PrevClose'] = abs(self.df['High'] - self.df['Close'].shift(1))
        self.df['Low-PrevClose'] = abs(self.df['Low'] - self.df['Close'].shift(1))
        self.df['TR'] = self.df[['High-Low','High-PrevClose','Low-PrevClose']].max(axis=1)

        self.df['+DM'] = np.where(
            (self.df['High'] - self.df['High'].shift(1)) > (self.df['Low'].shift(1) - self.df['Low']),
            np.maximum(self.df['High'] - self.df['High'].shift(1), 0), 0
        )
        self.df['-DM'] = np.where(
            (self.df['Low'].shift(1) - self.df['Low']) > (self.df['High'] - self.df['High'].shift(1)),
            np.maximum(self.df['Low'].shift(1) - self.df['Low'], 0), 0
        )

        from ._averages import seeded_average

        size = len(self.df)
        plus, minus, ranges = (self.df[column].to_numpy(dtype=float) for column in ('+DM', '-DM', 'TR'))
        plus_sum, minus_sum, range_sum = (float(values[1:self.period].sum()) for values in (plus, minus, ranges))
        smooth = np.full((size, 3), np.nan)
        for position in range(self.period, size):
            plus_sum += plus[position] - plus_sum / self.period
            minus_sum += minus[position] - minus_sum / self.period
            range_sum += ranges[position] - range_sum / self.period
            smooth[position] = plus_sum, minus_sum, range_sum
        self.df['+DM_smooth'] = smooth[:, 0]
        self.df['-DM_smooth'] = smooth[:, 1]
        self.df['TR_smooth'] = smooth[:, 2]
        self.df['ATR'] = seeded_average(self.df['TR'], self.period, start=self.period, alpha=1 / self.period)
        self.df['+DI'] = (100 * self.df['+DM_smooth'] / self.df['TR_smooth']).where(self.df['TR_smooth'] != 0, 0)
        self.df['-DI'] = (100 * self.df['-DM_smooth'] / self.df['TR_smooth']).where(self.df['TR_smooth'] != 0, 0)
        denominator = self.df['+DI'] + self.df['-DI']
        self.df['DX'] = (100 * abs(self.df['+DI'] - self.df['-DI']) / denominator).where(denominator != 0, 0)
        self.df['ADX'] = seeded_average(self.df['DX'], self.period, start=2 * self.period - 1, alpha=1 / self.period)

    def _calculate_signals(self):
        self.df['Buy_Signal'] = np.where(
            (self.df['+DI'] > self.df['-DI']) & (self.df['+DI'].shift(1) <= self.df['-DI'].shift(1)), 1, 0
        )
        self.df['Sell_Signal'] = np.where(
            (self.df['-DI'] > self.df['+DI']) & (self.df['-DI'].shift(1) <= self.df['+DI'].shift(1)), 1, 0
        )
        self.df['Strong_Buy'] = np.where(
            (self.df['Buy_Signal'] == 1) & (self.df['ADX'] >= self.adx_threshold), 1, 0
        )
        self.df['Strong_Sell'] = np.where(
            (self.df['Sell_Signal'] == 1) & (self.df['ADX'] >= self.adx_threshold), 1, 0
        )

    def get_signals(self):
        return self.df[['Date', '+DI', '-DI', 'ADX', 'Buy_Signal', 'Sell_Signal', 'Strong_Buy', 'Strong_Sell']]

    def get_trend_strength(self):
        import numpy as _np
        conditions = [
            (self.df['ADX'] >= 25),
            (self.df['ADX'] < 25) & (self.df['ADX'] >= 20),
            (self.df['ADX'] < 20),
        ]
        choices = ['Strong Trend', 'Weak Trend', 'Trendless Market']
        self.df['Trend_Strength'] = _np.select(conditions, choices, default='Unknown')
        return self.df[['Date', 'ADX', 'Trend_Strength']]

    def plot_indicators(self):
        plt.figure(figsize=(14, 8))
        plt.plot(self.df['Date'], self.df['+DI'], label='+DI', color='green')
        plt.plot(self.df['Date'], self.df['-DI'], label='-DI', color='red')
        plt.plot(self.df['Date'], self.df['ADX'], label='ADX', color='blue')
        plt.fill_between(self.df['Date'], 0, self.df['ADX'], where=self.df['ADX'] >= 25, color='blue', alpha=0.1)
        plt.title('DMI and ADX Indicators'); plt.xlabel('Date'); plt.ylabel('Indicator Value')
        plt.legend(loc='upper right'); plt.grid(True); plt.show()

    def plot_trend_strength(self):
        trend_df = self.get_trend_strength()
        plt.figure(figsize=(14, 8))
        plt.plot(trend_df['Date'], trend_df['ADX'], label='ADX', color='blue')
        plt.fill_between(trend_df['Date'], 0, trend_df['ADX'],
                         where=trend_df['Trend_Strength'] == 'Strong Trend', color='blue', alpha=0.1, label='Strong Trend')
        plt.fill_between(trend_df['Date'], 0, trend_df['ADX'],
                         where=trend_df['Trend_Strength'] == 'Trendless Market', color='gray', alpha=0.1, label='Trendless Market')
        plt.title('ADX and Trend Strength'); plt.xlabel('Date'); plt.ylabel('ADX Value')
        plt.legend(loc='upper right'); plt.grid(True); plt.show()

def __dir__():
    return __all__
