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

from copy import deepcopy

from ....proxy import Proxy
from ....exceptions import (
    HistoricalNoDataError,
    HistoricalDataUnavailableError,
)


__all__ = ['historical']




# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Historical Price Data API Response ("chart" endpoint)

This class expects as input the parsed JSON response for historical price data for a single security
(e.g., stock, ETF, or crypto). The structure is tailored to a "chart" API, delivering
daily or custom-interval time series data, including open, high, low, close, volume, and adjusted close prices.

Example Input Structure:
[
  {
    "<string-key>": {   # Typically a URL-encoded query string or endpoint signature
      "response": {
        "chart": {
          "result": [
            {
              "meta": {
                "currency": str,                # e.g., "USD"
                "symbol": str,                  # e.g., "NVDA"
                "exchangeName": str,            # e.g., "NMS"
                "fullExchangeName": str,        # e.g., "NasdaqGS"
                "instrumentType": str,          # e.g., "EQUITY"
                "firstTradeDate": int,          # Unix timestamp
                "regularMarketTime": int,       # Unix timestamp (latest tick)
                "hasPrePostMarketData": bool,
                "gmtoffset": int,               # GMT offset in seconds
                "timezone": str,                # e.g., "EDT"
                "exchangeTimezoneName": str,    # e.g., "America/New_York"
                "regularMarketPrice": float,    # Latest market price
                "fiftyTwoWeekHigh": float,
                "fiftyTwoWeekLow": float,
                "regularMarketDayHigh": float,
                "regularMarketDayLow": float,
                "regularMarketVolume": int,
                "longName": str,
                "shortName": str,
                "chartPreviousClose": float,
                "priceHint": int,
                "currentTradingPeriod": {
                  "pre": {
                    "timezone": str,
                    "start": int,
                    "end": int,
                    "gmtoffset": int
                  },
                  "regular": {
                    "timezone": str,
                    "start": int,
                    "end": int,
                    "gmtoffset": int
                  },
                  "post": {
                    "timezone": str,
                    "start": int,
                    "end": int,
                    "gmtoffset": int
                  }
                },
                "dataGranularity": str,         # e.g., "1d"
                "range": str,                   # (can be empty string)
                "validRanges": [str]            # Allowed ranges
              },
              "timestamp": [int],               # List of UNIX timestamps for each bar (aligned with OHLCV)
              "indicators": {
                "quote": [
                  {
                    "open": [float],            # Open prices per bar (aligned by index)
                    "high": [float],            # High prices per bar
                    "low": [float],             # Low prices per bar
                    "close": [float],           # Close prices per bar
                    "volume": [int]             # Volume per bar
                  }
                ],
                "adjclose": [
                  {
                    "adjclose": [float]         # Adjusted close prices per bar
                  }
                ]
              }
              # ...possibly more fields...
            }
            # ...more results for batch/overlay queries (rare)
          ],
          "error": None or {}                    # Error info if request fails, else None
        }
      }
    }
  }
  # ...more items if batch queries...
]

Notes:
	• The top-level list supports batch queries (multiple symbols/requests).
	• "<string-key>" is typically the request signature.
	• "result" is an array; for most use cases only the first entry is needed.
	• All time series arrays ("open", "high", "low", "close", "volume", "adjclose") are aligned by index to "timestamp".
	• Not all fields may be present for every symbol or interval (e.g., "adjclose" sometimes omitted).
	• Defensive parsing is attempted, as field presence and array lengths may vary.
	• Date/time fields are Unix timestamps (seconds since epoch).
"""
class historical:
    __slots__ = ("_raw", "_records", "_rows", "data")
    def __init__(self, json_content=None):
        self._raw = None; self._records = []; self._rows = []; self.data = None
        if json_content is None: raise HistoricalDataUnavailableError("No JSON content provided")
        self._raw = deepcopy(json_content)
        self._records = self._response_status(self._raw)
        if not self._records: raise HistoricalNoDataError("No historical result data present")
        self._parse_rows()
        if not self._rows: raise HistoricalNoDataError("No valid data points found after parsing")
        self._create_dataframe()
    @staticmethod
    def _response_status(json_content):
        payload = deepcopy(json_content); records = []
        if isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict): continue
                inner = next(iter(entry.values())); resp = inner.get("response", {}); chart = resp.get("chart", {})
                if chart.get("error"): continue
                result = chart.get("result", [])
                if isinstance(result, list): records.extend(result)
        elif isinstance(payload, dict):
            chart = payload.get("chart", {})
            if chart.get("error"): raise HistoricalDataUnavailableError(f"Chart error: {chart['error']}")
            result = chart.get("result", [])
            if isinstance(result, list): records.extend(result)
        else: raise HistoricalDataUnavailableError(f"Unsupported payload type: {type(payload)}")
        return records
    def _parse_rows(self):
        for rec in self._records:
            meta = rec.get("meta", {}); symbol = meta.get("symbol")
            company = meta.get("longName") or meta.get("shortName") or ""
            timestamps = rec.get("timestamp", [])
            quote_list = rec.get("indicators", {}).get("quote", []); adj_list = rec.get("indicators", {}).get("adjclose", [])
            quote = quote_list[0] if quote_list else {}; adj = adj_list[0] if adj_list else {}
            for i, ts in enumerate(timestamps):
                self._rows.append({
                    "Timestamp": ts, "Symbol": symbol, "Company Name": company,
                    "Open": quote.get("open", [None])[i], "High": quote.get("high", [None])[i],
                    "Low": quote.get("low", [None])[i], "Close": quote.get("close", [None])[i],
                    "Adj Close": adj.get("adjclose", [None])[i], "Volume": quote.get("volume", [None])[i],
                    "Currency": meta.get("currency"), "Exchange Name": meta.get("exchangeName"),
                    "Full Exchange Name": meta.get("fullExchangeName"), "Instrument Type": meta.get("instrumentType"),
                    "First Trade Date": meta.get("firstTradeDate"), "Regular Market Price": meta.get("regularMarketPrice"),
                    "52 Week High": meta.get("fiftyTwoWeekHigh"), "52 Week Low": meta.get("fiftyTwoWeekLow"),
                    "Day High": meta.get("regularMarketDayHigh"), "Day Low": meta.get("regularMarketDayLow"),
                    "Regular Market Volume": meta.get("regularMarketVolume"), "Market Time": meta.get("regularMarketTime"),
                })
    def _create_dataframe(self):
        df = pd.DataFrame(self._rows)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s")
        df["First Trade Date"] = pd.to_datetime(df["First Trade Date"], unit="s", errors="coerce")
        df["Market Time"] = pd.to_datetime(df["Market Time"], unit="s", errors="coerce")
        desired = ["Timestamp", "Symbol", "Company Name", "Open", "High", "Low", "Close", "Adj Close", "Volume",
                   "Currency", "Exchange Name", "Full Exchange Name", "Instrument Type", "First Trade Date",
                   "Regular Market Price", "52 Week High", "52 Week Low", "Day High", "Day Low", "Regular Market Volume", "Market Time"]
        df = df[[c for c in desired if c in df.columns]]
        self.data = df
    def DATA(self):
        if self.data is None or self.data.empty: raise HistoricalNoDataError("No historical data available")
        return self.data
    def __repr__(self):
        count = len(self.data) if self.data is not None else 0
        symbol = self.data["Symbol"].iat[0] if count > 0 else None
        return f"<historical symbol={symbol!r}, points={count}>"
    def __dir__(self): return ['DATA']

def __dir__():
    return __all__
