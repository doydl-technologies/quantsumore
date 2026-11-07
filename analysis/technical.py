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

"""Prepare historical OHLCV data and expose technical indicators and plots.

The analysis object normalizes column labels, identifies a single security and
checks available history before indicator calculations. Indicator objects
provide numeric results, legacy signal heuristics and plotting methods."""
import re
from copy import deepcopy

from ..date_parser import dtparse
from ..proxy import Proxy
from ..exceptions import DataInitializationError
from .indicators import (
    DirectionalMovementIndex as _DirectionalMovementIndex,
    AroonIndicator as _AroonIndicator,
    OnBalanceVolume as _OnBalanceVolume,
    AccumulationDistributionLine as _AccumulationDistributionLine,
    MACD as _MACD,
    RelativeStrengthIndex as _RelativeStrengthIndex,
    FastStochasticOscillator as _FastStochasticOscillator,
    MovingAveragesAndBollingerBands as _MovingAveragesAndBollingerBands,
    AverageTrueRange as _AverageTrueRange,
)

__all__ = ['tAnalyze']




# Defer dependency imports until first use.
pd = Proxy("pandas", None)
plt = Proxy("matplotlib.pyplot")
np = Proxy("numpy")


class tAnalyze:
    """Prepare one security's OHLCV data and construct indicator objects.

    Column names are mapped explicitly or inferred. If Symbol is absent, ticker
    can supply it. When multiple symbols are present, rows for the first symbol
    are selected. Dates are normalized to YYYY-MM-DD and prices/volume must
    convert to numeric values.

    Indicator methods return objects exposing calculated data and plots.
    Periods count observations, not calendar days. Numeric warm-up gaps and
    legacy heuristic signal labels are retained in the returned data.
    """
    def __init__(self, df, column_map=None, ticker=None, require_all=True):
        """Normalize historical prices for indicator calculations.

        Parameters
        ----------
        df : pandas.DataFrame
            Historical data with Symbol, Date, Open, High, Low, Close and Volume.
        column_map : dict, optional
            Source column names mapped to standard names. Unmapped names are inferred.
        ticker : str, optional
            Symbol to assign when the input has no Symbol column.
        require_all : bool, default True
            Retain only standard columns when True. All seven standard columns
            are still required after normalization when False.

        Raises
        ------
        DataInitializationError
            If preprocessing fails. Successful initialization prints the symbol.
        """
        self.dataframe = None
        self.df = None
        self.ticker = None
        try:
            self.dataframe = self.Dataframe(df, column_map=column_map, ticker=ticker, require_all=require_all)
            self.df = self.dataframe.df
            self.ticker = self.df['Symbol'].iloc[0]
            print(f"Historical prices successfully loaded for {self.ticker}.")
        except Exception as e:
            raise DataInitializationError(
                f"Historical prices could not be loaded for {self.ticker or 'ticker symbol'}. Error: {e}"
            )

    def __dir__(self):
        return [
            "DirectionalMovementIndex", "AroonIndicator", "OnBalanceVolume",
            "AccumulationDistributionLine", "MACD", "RelativeStrengthIndex",
            "FastStochasticOscillator", "MovingAveragesAndBollingerBands", "AverageTrueRange",
            "ticker", "df",
        ]

    class Dataframe:
        """Normalize column names, numeric values and dates, then select the first symbol."""
        def __init__(self, df: pd.DataFrame, column_map=None, ticker=None, require_all=True):
            if df.empty:
                raise ValueError("DataFrame is empty")
            self.df = deepcopy(df)
            self._user_map = column_map or {}
            self._ticker = ticker
            self._require_all = require_all

            self.rename_cols()
            self._maybe_add_symbol_from_ticker()
            self.convert_to_floats()
            self.filter_to_single_symbol()
            self.normalize_date()

            has_columns, missing = self.check_columns()
            if not has_columns:
                raise ValueError(f"Missing required columns: {missing}")

        def rename_cols(self):
            original_cols = list(self.df.columns)
            final_map = {}
            allowed_targets = {'Symbol','Date','High','Low','Open','Close','Volume'}
            bad_targets = [t for t in self._user_map.values() if t not in allowed_targets]
            if bad_targets:
                raise ValueError(f"Invalid target names in column_map: {bad_targets}. Allowed: {sorted(allowed_targets)}")
            missing_sources = [s for s in self._user_map if s not in original_cols]
            if missing_sources:
                raise ValueError(f"column_map refers to columns not in DataFrame: {missing_sources}")
            final_map.update(self._user_map)
            if 'Date' not in final_map.values() and 'Timestamp' in self.df.columns:
                final_map['Timestamp'] = 'Date'

            def find_best_matches(df):
                keyword_map = {
                    'Symbol': ['ticker', 'symbol'],
                    'Date':   ['date'],
                    'High':   ['high','h'],
                    'Low':    ['low','l'],
                    'Open':   ['open','o'],
                    'Close':  ['close','c','adjclose','adj_close','adjustedclose'],
                    'Volume': ['volume','vol','qty','quantity']
                }
                column_renames = {}
                for standard_name, keywords in keyword_map.items():
                    if standard_name in final_map.values():
                        continue
                    for keyword in keywords:
                        pattern = re.compile(r'^' + keyword + r'|' + keyword, re.IGNORECASE)
                        best = sorted([c for c in df.columns if pattern.search(c)],
                                      key=lambda x: not x.lower().startswith(keyword))
                        if best:
                            src = best[0]
                            if src not in final_map:
                                column_renames[src] = standard_name
                                break
                return column_renames

            auto_map = find_best_matches(self.df)
            for src, tgt in auto_map.items():
                if tgt not in self._user_map.values() and src not in final_map:
                    final_map[src] = tgt

            if not final_map:
                raise ValueError("Failed to match critical columns based on user mapping and keywords.")

            self.df = self.df.rename(columns=final_map, inplace=False)

            required = ['Symbol','Date','Open','High','Low','Close','Volume']
            present_required = [c for c in required if c in self.df.columns]
            if self._require_all:
                self.df = self.df[present_required]

        def _maybe_add_symbol_from_ticker(self):
            required = ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            if 'Symbol' not in self.df.columns:
                if self._ticker:
                    self.df['Symbol'] = str(self._ticker)
                elif self._require_all:
                    raise ValueError("Symbol column is missing and no `ticker` was provided to synthesize it.")
            if all(col in self.df.columns for col in required):
                self.df = self.df[required + [c for c in self.df.columns if c not in required]]

        def convert_to_floats(self):
            float_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_floats = [col for col in float_columns if col not in self.df.columns]
            if missing_floats:
                raise ValueError(f"Missing float columns: {missing_floats}")
            for col in float_columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                if self.df[col].isna().any():
                    raise ValueError(f"Conversion to float failed for column: {col}")

        def normalize_date(self):
            if 'Date' not in self.df.columns:
                raise ValueError("Date column is missing")
            try:
                self.df['Date'] = self.df['Date'].apply(lambda x: dtparse.parse(x, to_format='%Y-%m-%d'))
            except Exception as e:
                raise ValueError(f"Date conversion failed: {str(e)}")

        def check_columns(self):
            required_cols = ['Symbol', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_cols if col not in self.df.columns]
            return (not missing_columns, missing_columns)

        def filter_to_single_symbol(self):
            if 'Symbol' not in self.df.columns:
                raise ValueError("Symbol column is missing for filtering")
            first_symbol = self.df['Symbol'].iloc[0]
            self.df = self.df[self.df['Symbol'] == first_symbol]

    def verify_period_sufficiency(self, period):
        unique_dates = self.df['Date'].nunique()
        if unique_dates < period:
            raise ValueError(f"Insufficient data: The DataFrame contains only {unique_dates} unique dates, but at least {period} unique dates are required.")
      
    def DirectionalMovementIndex(self, period=14, adx_threshold=25):
        """Return a DMI/ADX indicator object.

        period controls Wilder smoothing (default 14); adx_threshold labels trend
        strength (default 25). The object exposes numeric results, heuristic signals
        and indicator/trend-strength plots.
        """
        return _DirectionalMovementIndex(self, period, adx_threshold)        
       
    def AroonIndicator(self, period=25):
        """Return an Aroon Up/Down indicator object.

        period counts elapsed observations (default 25, requiring 26 prices).
        The object exposes Aroon values, heuristic trend labels and a plot.
        """
        return _AroonIndicator(self, period)
       
    def OnBalanceVolume(self):
        """Return an On-Balance Volume indicator object.

        The object exposes OBV values, heuristic divergence labels and a plot.
        """
        return _OnBalanceVolume(self)

    def AccumulationDistributionLine(self):
        """Return an Accumulation/Distribution Line indicator object.

        The object exposes cumulative money flow, heuristic divergence labels and
        a plot.
        """
        return _AccumulationDistributionLine(self)

    def MACD(self, short_window=12, long_window=26, signal_window=9):
        """Return a MACD indicator object.

        short_window, long_window and signal_window count observations, with
        defaults 12, 26 and 9. The object exposes SMA-seeded EMA differences,
        signal/histogram values, heuristic crossover labels and a plot.
        """
        return _MACD(self, short_window, long_window, signal_window)

    def RelativeStrengthIndex(self, period=14):
        """Return a Wilder-smoothed RSI indicator object.

        period defaults to 14 observations. The object exposes RSI values,
        threshold-crossing and divergence heuristics, and a plot.
        """
        return _RelativeStrengthIndex(self, period)
       
    def FastStochasticOscillator(self, k_period=14, d_period=3):
        """Return a stochastic oscillator indicator object.

        k_period defaults to 14 observations; d_period defaults to 3 for smoothing
        %K into %D. The object exposes both lines, heuristic labels and a plot.
        """
        return _FastStochasticOscillator(self, k_period, d_period)

    def MovingAveragesAndBollingerBands(self, sma_period=20, ema_period=20, bb_period=20, bb_std=2):
        """Return a moving-average and Bollinger-band indicator object.

        sma_period, ema_period and bb_period default to 20 observations.
        bb_std defaults to 2 population standard deviations. The object exposes
        SMA, SMA-seeded EMA, bands, heuristic crossovers and a plot.
        """
        return _MovingAveragesAndBollingerBands(self, sma_period, ema_period, bb_period, bb_std)

    def AverageTrueRange(self, atr_period=14):
        """Return a Wilder-smoothed ATR indicator object.

        atr_period defaults to 14 observations. The object exposes ATR values,
        a plot and volatility-shift labels.
        """
        return _AverageTrueRange(self, atr_period)

def __dir__():
    return __all__
