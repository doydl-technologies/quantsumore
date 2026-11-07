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

from ....date_parser import dtparse
from ....proxy import Proxy
from ....exceptions import (
    TreasuryDataValidationError,
    TreasuryNoDataError,
    TreasuryDataUnavailableError,
)


__all__ = ['riskfreerate']




# Defer dependency imports until first use.
pd = Proxy("pandas", None)


"""
riskfreerate: Comprehensive Risk-Free Rate Extraction and Processing


This class is designed to efficiently process, validate, and standardize U.S. Treasury rate data
for use as risk-free rates in quantitative finance, analytics, and reporting. It supports both
T-bill rates and full Treasury yield curve data, enabling users to extract the latest rates or
generate a cleaned historical table.

Key Features:
  • Accepts a pandas DataFrame containing raw Treasury rate data (T-bills or yield curve).
  • Automatically detects and validates the type of data ("tbill" for Treasury bills or "tyield" for yield curve).
  • Cleans and prepares the input data, including date parsing, column normalization, and sorting.
  • Handles missing, malformed, or non-standard data gracefully, returning NaN or None where appropriate.

Data Processing:
  • Dates: Parses date strings into standardized datetime objects and sorts records chronologically.
  • Rates: Converts all rates to decimal form (e.g., 0.045 for 4.5%), rounding to four decimal places.
  • Columns: Remaps column names to user-friendly labels for both T-bill and yield curve data,
    supporting both extraction of latest rates and historical tables.

Internal Implementation:
  • Static and internal helper methods manage date parsing, rate formatting, and DataFrame cleaning.
  • Configurable column mappings support flexible extraction of both T-bill and yield curve maturities.
  • Encapsulates all processing logic, ensuring that downstream consumers receive ready-to-use,
    reliable, and standardized risk-free rate data.
"""
class riskfreerate:
    @staticmethod
    def _format_date(date_str):
        try:
            return dtparse.parse(date_str)
        except Exception:
            return pd.NaT

    @staticmethod
    def _format_rates(rates: dict) -> dict:
        out = {}
        for k, v in rates.items():
            if v is None:
                out[k] = None
            elif 0 <= v <= 1:
                out[k] = round(v, 4)
            else:                       # convert % → decimal
                out[k] = round(v / 100, 4)
        return out

    def __init__(self, df: pd.DataFrame, kind: str, *, full: bool = False):
        self.kind = kind.lower()
        if self.kind not in {"tbill", "tyield"}:
            raise TreasuryDataValidationError("kind must be 'tbill' or 'tyield'")
        self.full_requested = full

        self.df = self._clean_and_prepare(df)
        if self.df.empty:
            raise TreasuryNoDataError("Input DataFrame is empty or invalid for treasury scan.")
        elif self.full_requested:
            self.result = (self._full_tbill_table(self.df) if self.kind == "tbill"
                            else self._full_yield_table(self.df))
        else:
            latest = (self._extract_latest_tbills(self.df) if self.kind == "tbill"
                      else self._extract_latest_yield(self.df))
            self.result = self._format_rates(latest)

    def _clean_and_prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = df.columns.str.title()
        if "Date" in df.columns:
            df["Date"] = df["Date"].apply(self._format_date)
            df = df.sort_values("Date")
        return df.reset_index(drop=True)

    # T-Bill helpers
    _tbill_column_map = {
        "1-Month T-Bill":  "4 Weeks Coupon Equivalent",
        "2-Month T-Bill":  "8 Weeks Coupon Equivalent",
        "3-Month T-Bill":  "13 Weeks Coupon Equivalent",
        "4-Month T-Bill":  "17 Weeks Coupon Equivalent",
        "6-Month T-Bill":  "26 Weeks Coupon Equivalent",
        "12-Month T-Bill": "52 Weeks Coupon Equivalent",
    }

    def _extract_latest_tbills(self, df):
        last = df.loc[df["Date"] == df["Date"].max()]
        out = {}
        for display, col in self._tbill_column_map.items():
            try:
                out[display] = float(last.iloc[0][col])
            except Exception:
                out[display] = None
        return out
       
    def _full_tbill_table(self, df):
        keep = ["Date"] + [v for v in self._tbill_column_map.values() if v in df.columns]
        table = df[keep].rename(columns={v: k for k, v in self._tbill_column_map.items()})
        return table

    # Yield-Curve helpers
    _yield_column_map = {
        "1 Mo":  "1-Month Treasury Bill (T-Bill)",
        "2 Mo":  "2-Month Treasury Bill (T-Bill)",
        "3 Mo":  "3-Month Treasury Bill (T-Bill)",
        "4 Mo":  "4-Month Treasury Bill (T-Bill)",
        "6 Mo":  "6-Month Treasury Bill (T-Bill)",
        "1 Yr":  "1-Year Treasury Note",
        "2 Yr":  "2-Year Treasury Note",
        "3 Yr":  "3-Year Treasury Note",
        "5 Yr":  "5-Year Treasury Note",
        "7 Yr":  "7-Year Treasury Note",
        "10 Yr": "10-Year Treasury Note",
        "20 Yr": "20-Year Treasury Bond",
        "30 Yr": "30-Year Treasury Bond",
    }

    def _extract_latest_yield(self, df):
        last_row = df.loc[df['Date'] == df['Date'].max()]
        rates = {}
        for col, display in self._yield_column_map.items():
            if col in last_row.columns:
                value = last_row.iloc[0][col]
                try:
                    rates[display] = float(value)
                except Exception:
                    rates[display] = None
            else:
                rates[display] = None
        return rates

    def _full_yield_table(self, df):
        keep = ["Date"] + [c for c in self._yield_column_map if c in df.columns]
        table = df[keep].rename(columns=self._yield_column_map)
        return table
    
    def DATA(self):
        if self.result is None or (isinstance(self.result, dict) and not any(self.result.values())):
            raise TreasuryDataUnavailableError()
        return self.result

def __dir__():
    return __all__
