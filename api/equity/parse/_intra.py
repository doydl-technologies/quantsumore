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

from ....date_parser import dtparse
from ....proxy import Proxy
from ....exceptions import (
    LatestNoDataError,
    LatestDataUnavailableError,
)


__all__ = ['latest']





# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Intraday "Latest" Price and Minute-Bar API Response ("spark" endpoint)

This class expects as input the parsed JSON response for the latest price and intraday minute-bar data
for a single financial instrument (e.g., stock, ETF, crypto). The input is a list containing one or more
objects, each keyed by a unique request string (often the full endpoint and parameters).

Example Input Structure:
[
  {
    "<string-key>": {   # Typically a URL-encoded string or endpoint signature
      "response": {
        "spark": {
          "result": [
            {
              "symbol": str,         # e.g., "NVDA"
              "response": [
                {
                  "meta": {
                    "currency": str,                # e.g., "USD"
                    "symbol": str,                  # e.g., "NVDA"
                    "exchangeName": str,            # e.g., "NMS"
                    "fullExchangeName": str,        # e.g., "NasdaqGS"
                    "instrumentType": str,          # e.g., "EQUITY"
                    "firstTradeDate": int,          # Unix timestamp
                    "regularMarketTime": int,       # Unix timestamp for latest tick
                    "hasPrePostMarketData": bool,
                    "gmtoffset": int,               # GMT offset in seconds
                    "timezone": str,                # e.g., "EDT"
                    "exchangeTimezoneName": str,    # e.g., "America/New_York"
                    "regularMarketPrice": float,    # Latest trade price
                    "fiftyTwoWeekHigh": float,
                    "fiftyTwoWeekLow": float,
                    "regularMarketDayHigh": float,
                    "regularMarketDayLow": float,
                    "regularMarketVolume": int,
                    "longName": str,                # e.g., "NVIDIA Corporation"
                    "shortName": str,               # e.g., "NVIDIA Corporation"
                    "chartPreviousClose": float,
                    "previousClose": float,
                    "scale": int,                   # Number of decimals for price display
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
                    "tradingPeriods": [
                      [
                        {
                          "timezone": str,
                          "end": int,
                          "start": int,
                          "gmtoffset": int
                        }
                        # ... possibly more trading period dicts ...
                      ]
                    ],
                    "dataGranularity": str,         # e.g., "1m"
                    "range": str,                   # e.g., "1d"
                    "validRanges": [str],           # Allowed ranges, e.g., ["1d", "5d", ...]
                  },
                  "timestamp": [int],               # List of UNIX timestamps for each minute bar
                  "indicators": {
                    "quote": [
                      {
                        "close": [float],           # List of close prices (aligned to timestamp)
                        # Optionally: "open", "high", "low", "volume"
                      }
                    ]
                  }
                  # ...possible additional keys, e.g., "adjclose"
                }
                # ...possibly more response objects
              ]
            }
            # ...more symbols if batch request
          ],
          "error": None or {}  # Error object on failure, else None
        }
      }
    }
  }
  # ...more result objects for batch queries...
]

Notes:
	• The top-level list supports batching (multiple symbols/queries).
	• The "<string-key>" is typically the unique request string or endpoint signature.
	• The "result" array contains a dict per symbol; each symbol has a "response" list (usually length 1).
	• Timestamps and indicator arrays (such as "close") are strictly aligned by index.
	• Not all indicator arrays ("open", "high", "low", "volume") may be present, depending on API permissions or symbol.
	• "error" is only populated on request failure.
	• Defensive parsing is attempted; field presence may vary by instrument, trading session, or API changes.
"""
class latest:
    __slots__ = ('_raw', '_record', 'symbol', 'meta', 'timestamps', 'close_prices', 'longName', 'shortName')
    def __init__(self, json_content=None):
        self._raw = None; self._record = None; self.symbol = None; self.longName = None; self.shortName = None; self.meta = {}; self.timestamps = []; self.close_prices = []
        if json_content is None: raise LatestDataUnavailableError("No JSON content provided")
        self._raw = deepcopy(json_content); self._record = self._response_status(self._raw); self._populate()
    @staticmethod
    def _response_status(json_content):
        payload = deepcopy(json_content)
        if isinstance(payload, list):
            if not payload: raise LatestDataUnavailableError("Empty list at top level")
            node = payload[0]
        elif isinstance(payload, dict): node = payload
        else: raise LatestDataUnavailableError(f"Unsupported JSON type: {type(payload)}")
        if isinstance(node, dict) and len(node) == 1:
            key = next(iter(node))
            if isinstance(key, str) and key.startswith(('https://', 'http://')): node = node[key]
        if isinstance(node, dict) and "response" in node: node = node["response"]
        else: raise LatestDataUnavailableError("Missing 'response' field")
        if isinstance(node, dict) and "spark" in node: node = node["spark"]
        else: raise LatestDataUnavailableError("Missing 'spark' field")
        result = node.get("result")
        if not isinstance(result, list) or not result: raise LatestNoDataError("No 'result' data present")
        return result[0]
    def _populate(self):
        rec = self._record
        self.symbol = rec.get("symbol")
        responses = rec.get("response")
        if not isinstance(responses, list) or not responses: raise LatestNoDataError("No 'response' sub‑array found")
        resp0 = responses[0]
        self.meta = resp0.get("meta", {})
        self.longName = "".join(self.meta.get("longName", None).split()) if self.meta.get("longName", None) else None
        self.shortName = "".join(self.meta.get("shortName", None).split()) if self.meta.get("shortName", None) else None
        ts = resp0.get("timestamp")
        if not isinstance(ts, list): raise LatestNoDataError("Missing or invalid 'timestamp'")
        self.timestamps = ts
        indicators = resp0.get("indicators", {}); quote_list = indicators.get("quote", [])
        self.close_prices = quote_list[0].get("close", []) if quote_list and isinstance(quote_list, list) else []
        if len(self.timestamps) != len(self.close_prices): raise LatestDataUnavailableError(f"Timestamp ({len(self.timestamps)}) vs close ({len(self.close_prices)}) length mismatch")
    @property
    def latest_price(self):
        if not self.close_prices: raise LatestDataUnavailableError("No price series available")
        return self.close_prices[-1]
    @property
    def latest_timestamp(self):
        if not self.timestamps: raise LatestDataUnavailableError("No timestamp series available")
        return self.timestamps[-1]
    def DATA(self):
        ts = self.latest_timestamp; price = self.latest_price; rm_tm = self.meta.get("regularMarketTime")
        result = {
            "Ticker": self.symbol, "Price": price, "Currency": self.meta.get("currency"),
            "quoteTimeUTC": dtparse.unix_timestamp(ts, format='%Y-%m-%dT%H:%M:%SZ', utc=True, to_unix=False),
            "lastPriceTime": dtparse.unix_timestamp(ts, format='%Y-%m-%d %I:%M %p', to_unix=False),
            "regularMarketTime": dtparse.unix_timestamp(rm_tm, format='%Y-%m-%d %I:%M %p', to_unix=False),
        }
        if self.longName and self.longName == self.shortName: result["Name"] = self.longName
        else:
            if self.longName: result["longName"] = self.longName
            if self.shortName: result["shortName"] = self.shortName
        if "Name" in result: order = ['Ticker', 'Name', 'Price', 'lastPriceTime', 'regularMarketTime']
        else: order = ['Ticker', 'longName', 'shortName', 'Price', 'lastPriceTime', 'regularMarketTime']
        order.extend(['Currency', 'quoteTimeUTC'])
        return {k: result[k] for k in order if k in result}
    def __repr__(self):
        count = len(self.timestamps) if self.timestamps else 0
        return f"<latest symbol={self.symbol!r}, points={count}>"
    def __dir__(self): return ["DATA"]


def __dir__():
    return __all__
