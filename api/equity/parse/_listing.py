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
    IPONoDataError,
    IPODataUnavailableError,
)


__all__ = ['ipo']




# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: IPO Calendar API Response

This class expects as input the parsed JSON response for an IPO (Initial Public Offering) calendar
API, summarizing priced, filed, upcoming, and withdrawn IPO deals for a given time period.

Example Input Structure:
[
  {
    "<string-key>": {   # Usually a URL-encoded query string or endpoint signature (e.g., "...+2025-06")
      "response": {
        "data": {
          "priced": {
            "asOf": null or str,
            "headers": {                # Mapping of data keys to column headers
              "proposedTickerSymbol": str,
              "companyName": str,
              "proposedExchange": str,
              "proposedSharePrice": str,
              "sharesOffered": str,
              "pricedDate": str,
              "dollarValueOfSharesOffered": str,
              "dealStatus": str
            },
            "rows": [
              {
                "dealID": str,
                "proposedTickerSymbol": str,
                "companyName": str,
                "proposedExchange": str,
                "proposedSharePrice": str,
                "sharesOffered": str,
                "pricedDate": str,                # Format: "M/D/YYYY"
                "dollarValueOfSharesOffered": str,
                "dealStatus": str                  # e.g., "Priced"
              },
              # ...more priced IPOs...
            ]
          },
          "upcoming": {
            "upcomingTable": {
              "asOf": null or str,
              "headers": null or dict,
              "rows": null or list
            },
            "lastUpdatedTime": str                # e.g., "LAST UPDATED: 07/31/2025* - Source: EDGAR® Online"
          },
          "filed": {
            "asOf": null or str,
            "headers": {                          # Mapping for filed IPOs
              "proposedTickerSymbol": str,
              "companyName": str,
              "filedDate": str,
              "dollarValueOfSharesOffered": str
            },
            "rows": [
              {
                "dealID": str,
                "proposedTickerSymbol": str or null,
                "companyName": str,
                "filedDate": str,                 # Format: "M/D/YYYY"
                "dollarValueOfSharesOffered": str
              },
              # ...more filed IPOs...
            ]
          },
          "withdrawn": {
            "asOf": null or str,
            "headers": {                          # Mapping for withdrawn IPOs
              "proposedTickerSymbol": str,
              "companyName": str,
              "proposedExchange": str,
              "sharesOffered": str,
              "filedDate": str,
              "dollarValueOfSharesOffered": str,
              "withdrawDate": str
            },
            "rows": [
              {
                "dealID": str,
                "proposedTickerSymbol": str or null,
                "companyName": str,
                "proposedExchange": str or null,
                "sharesOffered": str,
                "filedDate": str,
                "dollarValueOfSharesOffered": str,
                "withdrawDate": str
              },
              # ...more withdrawn IPOs...
            ]
          },
          "month": int,                           # Numeric month (e.g., 6)
          "year": int,                            # Numeric year (e.g., 2025)
          "totalResults": int                     # Total IPOs in the period (may only count one category)
        },
        "message": str or null,                   # Usually null
        "status": {
          "rCode": int,                           # e.g., 200 (success)
          "bCodeMessage": [
            {
              "code": int,
              "errorMessage": str                 # May indicate missing or partial data (e.g., "Upcoming:No record found.")
            },
            # ...more status messages...
          ],
          "developerMessage": str or null
        }
      }
    }
  }
  # ...more entries if batched
]

Notes:
	• The top-level list supports batch queries for multiple date ranges.
	• "<string-key>" is the endpoint+params signature, often includes the query month.
	• “priced”, “filed”, and “withdrawn” each have their own `headers` mapping and `rows` with actual IPO records.
	• Fields are always strings, and may be empty/null if not reported.
	• Defensive parsing is attempted; check for nulls and empty arrays.
"""
class ipo:
    __slots__ = ("_raw", "_payload", "_rows", "data")
    def __init__(self, json_content=None):
        self._raw = None; self._payload = {}; self._rows = []; self.data = None
        if json_content is None: raise IPODataUnavailableError("No JSON content provided")
        self._raw = deepcopy(json_content)
        resp = self._response_status(self._raw)
        data_section = resp.get("data", {})
        if data_section.get("totalResults", 0) < 1: raise IPONoDataError("No IPO records found")
        self._payload = data_section
        self._parse_rows()
        if not self._rows: raise IPONoDataError("No valid IPO rows to parse")
        self._create_dataframe()
    @staticmethod
    def _response_status(json_content):
        payload = deepcopy(json_content)
        if isinstance(payload, list):
            if not payload: raise IPODataUnavailableError("Empty list at top level")
            node = payload[0]
        elif isinstance(payload, dict): node = payload
        else: raise IPODataUnavailableError(f"Unsupported JSON type: {type(payload)}")
        if isinstance(node, dict) and len(node) == 1:
            key = next(iter(node))
            if key.startswith(('https://', 'http://')): node = node[key]
        resp = node.get("response")
        if not isinstance(resp, dict): raise IPODataUnavailableError("Missing or invalid 'response' field")
        return resp
    def _parse_rows(self):
        priced = self._payload.get("priced", {})
        for entry in priced.get("rows", []):
            self._rows.append({
                "Ticker_Symbol": entry.get("proposedTickerSymbol"),
                "Company_Name": entry.get("companyName"),
                "Exchange": entry.get("proposedExchange"),
                "IPO_Price": entry.get("proposedSharePrice"),
                "Shares_Offered": entry.get("sharesOffered"),
                "IPO_Date": entry.get("pricedDate"),
                "Total_Offer_Amount": entry.get("dollarValueOfSharesOffered"),
            })
    def _create_dataframe(self):
        df = pd.DataFrame(self._rows)
        df["Total_Offer_Amount"] = df["Total_Offer_Amount"].replace(r"[\$,]", "", regex=True).astype(float)
        df["IPO_Date"] = pd.to_datetime(df["IPO_Date"], format="%m/%d/%Y", errors="coerce")
        df = df[["Ticker_Symbol","Company_Name","Exchange","IPO_Price","Shares_Offered","IPO_Date","Total_Offer_Amount"]]
        self.data = df
    def DATA(self):
        if self.data is None or self.data.empty: raise IPONoDataError("IPO data unavailable or empty")
        return self.data
    def __repr__(self):
        count = len(self.data) if self.data is not None else 0
        return f"<ipo rows={count}>"
    def __dir__(self): return ['DATA']



def __dir__():
    return __all__
