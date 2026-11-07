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

import re
from copy import deepcopy

from ...shape_tools import is_valid_dataframe
from ....proxy import Proxy
from ....exceptions import (
    LiveBidAskNoDataError,
    LiveBidAskUnavailableError,
)


__all__ = ['latest']





# Defer dependency imports until first use.
pd = Proxy("pandas", None)


"""
Expected Input: Live Bid/Ask API Response

This class expects as input the parsed JSON response from a live currency bid/ask API call.
The structure includes summary statistics and metadata for a given forex symbol, as returned by the external service.

Example structure:
[
  {
    "<string-key>": {
      "response": {
        "data": {
          "symbol": str,           # e.g. "EURUSD"
          "summaryData": {
            "Bid": {
              "label": str,        # "Bid"
              "value": str         # e.g. "1.1572"
            },
            "Ask": {
              "label": str,        # "Ask"
              "value": str         # e.g. "1.1573"
            },
            "TodaysHigh": {
              "label": str,        # "Today's High"
              "value": str         # e.g. "1.1597"
            },
            "TodaysLow": {
              "label": str,        # "Today's Low"
              "value": str         # e.g. "1.1551"
            },
            "Open": {
              "label": str,        # "Open"
              "value": str         # e.g. "1.1586"
            },
            "NetChangePercent": {
              "label": str,        # "Net Change %"
              "value": str         # e.g. "-0.12%"
            },
            "pc": {
              "label": str,        # "Net Change"
              "value": str         # e.g. "-0.0014"
            },
            "Price": {
              "label": str,        # "Last Value"
              "value": str         # e.g. "1.1572"
            },
            "Time": {
              "label": str,        # "Time of Last Value"
              "value": str         # e.g. "08/04/2025 01:39:01"
            },
            "OneDayRange": {
              "label": str,        # "1 Day Range"
              "value": str         # e.g. "1.1551-1.1597"
            }
            # ...more fields possible...
          },
          "assetClass": str,        # e.g. "CURRENCIES"
          "additionalData": None,   # could also be more data
          "bidAsk": None            # could also be more data
        },
        "message": None,            # could also be a string message
        "status": {
          "rCode": int,             # HTTP-style code, e.g. 200
          "bCodeMessage": None,     # backend code message or None
          "developerMessage": None  # extra dev info or None
        }
      }
    }
  }
]
""" 
class latest:
    def __init__(self, json_content=None):
        self.cleaned_data = None; self.data = None; self.json_content = None
        if json_content: self.json_content = latest._response_status(json_content)
        if self.json_content:
            self.parse()
            if self.cleaned_data: self._create_dataframe()
    @staticmethod
    def _response_status(json_content):
        dataset = deepcopy(json_content)
        if isinstance(json_content, list):
            if not json_content: raise LiveBidAskError("Response is not a non-empty list")
            node = json_content[0]
        elif isinstance(json_content, dict): node = json_content
        else: raise LiveBidAskError(f"Unsupported response type: {type(json_content)}")
        if (isinstance(node, dict) and len(node)==1 and not any(k in node for k in ["response","error","data"])):
            node = next(iter(node.values()))
        if isinstance(node, dict) and "error" in node: raise LiveBidAskError(node["error"])
        data = node["response"] if isinstance(node, dict) and "response" in node else node
        if not isinstance(data, dict): raise LiveBidAskError("Unexpected structure for data payload")
        if "data" not in data: raise LiveBidAskNoDataError("No 'data' key found in response")
        data_dict = data["data"]
        summary = data_dict.get("summaryData")
        if not isinstance(summary, dict) or not summary: raise LiveBidAskNoDataError("No summary data available in response")
        return data_dict
    def _create_dataframe(self):
        df = pd.DataFrame(self.cleaned_data); self.data = df
    def parse(self):
        rows = []; content = deepcopy(self.json_content)
        entries = [content] if isinstance(content, dict) else content if isinstance(content, list) else []
        for entry in entries:
            row = {}; row['Symbol'] = entry.get('symbol'); row['Asset Class'] = entry.get('assetClass')
            summary_data = entry.get('summaryData', {})
            for val in summary_data.values():
                label = val.get('label'); value = val.get('value')
                if label is not None: row[label] = value
            rows.append(row)
        if rows: self.cleaned_data = rows
    def DATA(self):
        if not is_valid_dataframe(self.data): raise LiveBidAskUnavailableError()
        return self.data
    def __dir__(self): return ['DATA']

def __dir__():
    return __all__
