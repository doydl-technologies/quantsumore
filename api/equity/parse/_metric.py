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


from copy import deepcopy

from ....proxy import Proxy
from ....exceptions import (
    QuoteStatisticsError,
    QuoteStatisticsNoDataError,
)


__all__ = ['quote_statistics']






# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Quote Statistics API Response (Screener/Market Fundamentals Endpoint)

This class expects, as input, the parsed JSON response from a quote statistics or market screener API.
The data structure summarizes real-time and fundamental statistics for a given equity (by symbol).

Example Input Structure:
[
  {
    "<string-key>": {   # Usually a URL-encoded query string or endpoint signature
      "response": {
        "status": int,             # HTTP-like status code (e.g., 200 for success)
        "data": {
          "data": [
            {
              "s": str,            # Symbol (e.g., "$NVDA")
              "n": str,            # Company name (e.g., "NVIDIA Corporation")
              "marketCap": float,  # Market capitalization
              "price": float,      # Last trade price
              "volume": float,     # Trading volume
              "peRatio": float,    # Price/Earnings ratio
              "open": float,       # Opening price
              "close": float,      # Previous close
              "low": float,        # Session low
              "high": float,       # Session high
              "dividendYield": float,    # Dividend yield (%)
              "low52": float,            # 52-week low
              "high52": float,           # 52-week high
              "priceTarget": float,      # Analyst price target
              "exDivDate": str,          # Ex-dividend date (YYYY-MM-DD)
              "nextEarningsDate": str,   # Next earnings report date (YYYY-MM-DD)
              "averageVolume": float,    # Average volume (period depends on API)
              "eps": float,              # Earnings per share
              "beta": float              # Beta (volatility measure)
            }
            # ...more securities if requested in batch (usually length 1)
          ],
          "resultsCount": int           # Number of records in "data" array
        }
      }
    }
  }
  # ...more entries if batched...
]

Notes:
	• The top-level list supports batch queries.
	• "<string-key>" is typically the request signature or endpoint+params.
	• The "data" array contains one dict per equity/security (typically just one per request).
	• All fields may be missing/null if data is unavailable for the requested symbol.
	• Date fields are ISO date strings (YYYY-MM-DD).
"""
class quote_statistics:
    __slots__ = ("_raw","_payload","symbol","name","market_cap","price","volume","pe_ratio","open","close","low","high","dividend_yield","low52","high52","price_target","ex_div_date","next_earnings_date","average_volume","eps","beta")
    METRIC_KEY_MAP = {
        's':'Ticker','n':'Company Name','close':'Previous Close','open':'Open','low':'Day\'s Low','high':'Day\'s High','low52':'52W Low',
        'high52':'52W High','bid':'Bid','ask':'Ask','volume':'Volume','averageVolume':'Avg. Volume','marketCap':'Market Cap','beta':'Beta (5Y Monthly)','peRatio':'PE Ratio',
        'eps':'EPS','dividendYield':'Dividend Yield','exDivDate':'Ex-Dividend Date','nextEarningsDate':'Earnings Date','priceTarget':'Price Target',
    }
    def __init__(self, json_content=None):
        self._raw=None; self._payload=None
        self.symbol=None; self.name=None; self.market_cap=None; self.price=None; self.volume=None; self.pe_ratio=None; self.open=None; self.close=None; self.low=None; self.high=None; self.dividend_yield=None
        self.low52=None; self.high52=None; self.price_target=None; self.ex_div_date=None; self.next_earnings_date=None; self.average_volume=None; self.eps=None; self.beta=None
        if json_content is None: raise QuoteStatisticsNoDataError("No JSON content provided")
        self._raw = deepcopy(json_content); self._payload = self._response_status(json_content); self._populate_from_json(self._payload)
    @staticmethod
    def _response_status(json_content):
        payload = deepcopy(json_content)
        if isinstance(payload, list):
            if not payload: raise QuoteStatisticsError("Response not a non‐empty list")
            node = payload[0]
        elif isinstance(payload, dict): node = payload
        else: raise QuoteStatisticsError(f"Unsupported response type: {type(payload)}")
        if isinstance(node, dict) and len(node) == 1:
            key = next(iter(node))
            if isinstance(key, str) and key.startswith(('https://', 'http://')): node = node[key]
        if isinstance(node, dict) and "response" in node: node = node["response"]
        if not isinstance(node, dict) or "data" not in node or "status" not in node: raise QuoteStatisticsError("Unexpected structure after unwrapping URL/response")
        data_section = node.get("data")
        if (not isinstance(data_section, dict) or "data" not in data_section or not isinstance(data_section["data"], list) or len(data_section["data"]) == 0):
            raise QuoteStatisticsNoDataError("No valid data found in response")
        return node
    def _populate_from_json(self, payload):
        record = payload["data"]["data"][0]
        field_map = {
            "s":"symbol","n":"name","marketCap":"market_cap","price":"price","volume":"volume","peRatio":"pe_ratio","open":"open",
            "close":"close","low":"low","high":"high","dividendYield":"dividend_yield","low52":"low52","high52":"high52","priceTarget":"price_target",
            "exDivDate":"ex_div_date","nextEarningsDate":"next_earnings_date","averageVolume":"average_volume","eps":"eps","beta":"beta",
        }
        for json_key, attr in field_map.items(): setattr(self, attr, record.get(json_key))
    @staticmethod
    def _replace_none_with_na(obj, na_value="N/A"):
        if isinstance(obj, dict): return {k: quote_statistics._replace_none_with_na(v, na_value) for k,v in obj.items()}
        elif isinstance(obj, list): return [quote_statistics._replace_none_with_na(v, na_value) for v in obj]
        elif obj is None: return na_value
        else: return obj
    def _metrics(self):
        record = self._payload["data"]["data"][0]; out = {}
        for field_key, human in self.METRIC_KEY_MAP.items():
            value = record.get(field_key)
            if human=="Ticker" and isinstance(value, str): value = value.lstrip('$').strip()
            out[human] = value
        low, high = record.get('low'), record.get('high')
        out["Day's Range"] = f"{low} - {high}" if low is not None and high is not None else None
        low52, high52 = record.get('low52'), record.get('high52')
        out["52 Week Range"] = f"{low52} - {high52}" if low52 is not None and high52 is not None else None
        out.setdefault('Bid', None); out.setdefault('Ask', None)
        return out
    def DATA(self):
        raw_metrics = self._metrics()
        return self._replace_none_with_na(raw_metrics)
    def __dir__(self): return ["DATA"]

def __dir__():
    return __all__
