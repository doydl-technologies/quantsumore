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
    LastTradeNoDataError,
    LastTradeDataUnavailableError,
)


__all__ = ['last']






# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Latest Price & Historical Time-Series API Response ("spark" endpoint)

This class expects, as input, the parsed JSON response for the latest price and historical timeseries data
for a single financial instrument (e.g., stock, ETF, crypto). The input is a list containing one or more
objects, each keyed by a unique request string (often the full endpoint with params).

Example Input Structure:
[
  {
    "<string-key>": {   # Usually a URL-encoded string or endpoint signature (e.g. "...+NVDA&range=1y...")
      "response": {
        "spark": {
          "result": [
            {
              "symbol": str,     # e.g. "NVDA"
              "response": [
                {
                  "meta": {
                    "currency": str,                # e.g. "USD"
                    "symbol": str,                  # e.g. "NVDA"
                    "exchangeName": str,            # e.g. "NMS"
                    "fullExchangeName": str,        # e.g. "NasdaqGS"
                    "instrumentType": str,          # e.g. "EQUITY"
                    "firstTradeDate": int,          # Unix timestamp
                    "regularMarketTime": int,       # Unix timestamp
                    "hasPrePostMarketData": bool,
                    "gmtoffset": int,               # Offset from GMT (in seconds)
                    "timezone": str,                # e.g. "EDT"
                    "exchangeTimezoneName": str,    # e.g. "America/New_York"
                    "regularMarketPrice": float,    # Latest available price
                    "fiftyTwoWeekHigh": float,
                    "fiftyTwoWeekLow": float,
                    "regularMarketDayHigh": float,
                    "regularMarketDayLow": float,
                    "regularMarketVolume": int,
                    "longName": str,                # e.g. "NVIDIA Corporation"
                    "shortName": str,               # e.g. "NVIDIA Corporation"
                    "chartPreviousClose": float,
                    "priceHint": int,
                    "currentTradingPeriod": {
                      "pre": {
                        "timezone": str,
                        "end": int,
                        "start": int,
                        "gmtoffset": int
                      },
                      "regular": {
                        "timezone": str,
                        "end": int,
                        "start": int,
                        "gmtoffset": int
                      },
                      "post": {
                        "timezone": str,
                        "end": int,
                        "start": int,
                        "gmtoffset": int
                      }
                    },
                    "dataGranularity": str,         # e.g. "1d"
                    "range": str,                   # e.g. "1y"
                    "validRanges": [str],           # e.g. ["1d", "5d", ...]
                  },
                  "timestamp": [int],               # List of UNIX timestamps, one per bar
                  "indicators": {
                    "quote": [
                      {
                        "close": [float],           # Closing prices, aligned by index to "timestamp"
                        # Optionally: "open", "high", "low", "volume" arrays
                      }
                    ]
                  }
                  # ...possibly other time-series data, e.g. "adjclose", "volume"
                }
                # ...possibly more response objects
              ]
              # ...possibly other fields (e.g. "error" for failure cases)
            }
            # ...more symbol results if batched
          ],
          "error": None or {}  # Error info if present, else None
        }
      }
    }
  }
  # ...more entries if batched
]

Notes:
	• The outer list allows for batch queries (multiple instruments in one request).
	• "<string-key>" is typically the request signature (endpoint + params).
	• The `"result"` list contains a dict per symbol/instrument. Each symbol may have one or more `"response"` entries (usually one).
	• Timestamps and indicator arrays (like `"close"`, `"open"`, etc.) are aligned by index (i.e., `close[i]` is the close for `timestamp[i]`).
	• Some fields (e.g., `"open"`, `"high"`, `"low"`, `"volume"`) may be omitted depending on request granularity or permissions.
	• `"error"` is present if the request fails for a symbol; otherwise it's `None`.

Always check for missing or `None` fields defensively.
"""
class last:
    __slots__ = ("_raw", "_record", "symbol", "longName", "shortName", "meta", "timestamps", "close_prices", "data")
    def __init__(self, json_content=None):
        self._raw = None; self._record = None; self.symbol = None; self.longName = None; self.shortName = None; self.meta = {}; self.timestamps = []; self.close_prices = []; self.data = None
        if json_content is None: raise LastTradeDataUnavailableError("No JSON content provided")
        self._raw = deepcopy(json_content)
        self._record = self._response_status(self._raw)
        self._populate()
        self._create_dataframe()
    @staticmethod
    def _response_status(json_content):
        payload = deepcopy(json_content)
        if isinstance(payload, list):
            if not payload: raise LastTradeDataUnavailableError("Empty list at top level")
            node = payload[0]
        elif isinstance(payload, dict): node = payload
        else: raise LastTradeDataUnavailableError(f"Unsupported JSON type: {type(payload)}")
        if isinstance(node, dict) and len(node) == 1:
            key = next(iter(node))
            if isinstance(key, str) and key.startswith(('https://', 'http://')): node = node[key]
        try: node = node["response"]["spark"]["result"]
        except Exception: raise LastTradeDataUnavailableError("Missing one of: 'response', 'spark', or 'result'")
        if not isinstance(node, list) or not node: raise LastTradeNoDataError("No 'result' data present")
        return node[0]
    def _populate(self):
        rec = self._record
        self.symbol = rec.get("symbol")
        responses = rec.get("response")
        if not isinstance(responses, list) or not responses: raise LastTradeNoDataError("No 'response' sub-array found")
        resp0 = responses[0]
        self.meta = resp0.get("meta", {})
        self.longName = self.meta.get("longName")
        self.shortName = self.meta.get("shortName")
        ts = resp0.get("timestamp")
        if not isinstance(ts, list): raise LastTradeNoDataError("Missing or invalid 'timestamp'")
        self.timestamps = ts
        quote_list = resp0.get("indicators", {}).get("quote", [])
        self.close_prices = quote_list[0].get("close", []) if quote_list and isinstance(quote_list, list) else []
        if len(self.timestamps) != len(self.close_prices):
            raise LastTradeDataUnavailableError(f"Timestamp ({len(self.timestamps)}) vs close ({len(self.close_prices)}) length mismatch")
    def _create_dataframe(self):
        company = self.longName or self.shortName or self.meta.get("shortName") or ""
        df = pd.DataFrame({
            "Symbol": [self.symbol]*len(self.timestamps), "Timestamp": self.timestamps, "Close Price": self.close_prices,
            "Market Price": [self.meta.get("regularMarketPrice")]*len(self.timestamps),
            "Day High": [self.meta.get("regularMarketDayHigh")]*len(self.timestamps),
            "Day Low": [self.meta.get("regularMarketDayLow")]*len(self.timestamps),
            "Volume": [self.meta.get("regularMarketVolume")]*len(self.timestamps),
            "Company Name": [company]*len(self.timestamps),
        })
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s")
        df = df[["Timestamp", "Symbol", "Company Name", "Close Price", "Market Price", "Day High", "Day Low", "Volume"]]
        self.data = df
    def DATA(self):
        if self.data is None or self.data.empty: raise LastTradeDataUnavailableError("No data available to return")
        return self.data
    def __repr__(self):
        cnt = len(self.timestamps) if self.timestamps else 0
        return f"<latest(symbol={self.symbol!r}, points={cnt})>"
    def __dir__(self): return ["DATA"]

def __dir__():
    return __all__
