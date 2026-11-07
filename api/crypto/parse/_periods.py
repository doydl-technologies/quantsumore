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


from ....markup import idextract
from ...market_utils import CoinQuery
from ...shape_tools import normalize_time, is_valid_dataframe
from ....strata_utils import IterDict
from ....proxy import Proxy
from ....exceptions import (
    CryptoHistoricalNoDataError, 
    CryptoHistoricalUnavailableError,
)


__all__ = ['historical']



# Defer dependency imports until first use.
pd = Proxy("pandas", None)

"""
Expected Input: Historical Cryptocurrency OHLCV API Response

This class expects as input the parsed JSON response for historical cryptocurrency OHLCV data.
The input should be a list containing one or more objects, each keyed by a string unique to the request (typically a URL or query signature).

Example Input Structure:
[
  {
    "<string-key>": {   # E.g., a URL-encoded query string or endpoint signature
      "response": {
        "data": {
          "id": int,             # Asset ID, e.g. 1 for Bitcoin
          "name": str,           # Asset name, e.g. "Bitcoin"
          "symbol": str,         # Asset symbol, e.g. "BTC"
          "timeEnd": str or int, # End time of the dataset as UNIX timestamp or string
          "quotes": [            # List of daily (or period) OHLCV records
            {
              "timeOpen": str,   # ISO 8601 datetime, start of period, e.g. "2023-01-02T00:00:00.000Z"
              "timeClose": str,  # ISO 8601 datetime, end of period
              "timeHigh": str,   # ISO 8601, time at which high occurred (optional)
              "timeLow": str,    # ISO 8601, time at which low occurred (optional)
              "quote": {
                "name": str,         # Asset or quote currency ID as string, e.g. "2781"
                "open": float,       # Open price for the period
                "high": float,       # High price for the period
                "low": float,        # Low price for the period
                "close": float,      # Close price for the period
                "volume": float,     # Trading volume over the period
                "marketCap": float,  # Market capitalization at close of period
                "timestamp": str     # ISO 8601 datetime, end of period
              }
            }
            # ...more daily or period records...
          ]
        },
        "status": {
          "timestamp": str,        # ISO 8601, API response timestamp
          "error_code": str or int,# "0" on success
          "error_message": str,    # "SUCCESS" on success
          "elapsed": str or int,   # Request duration (ms or s)
          "credit_count": int      # API credits consumed
        }
      }
    }
  }
  # ...more objects for additional requests if batched...
]

Notes:
	• The top-level list can contain multiple result objects for batched/multi-query requests.
	• The outermost key (string-key) is typically the full request signature, not just the asset.
	• The `"quotes"` array provides OHLCV data for each period (daily, hourly, etc., depending on API granularity).
	• `"timeHigh"` and `"timeLow"` indicate the exact times the daily high and low occurred, which is useful for more granular analysis.
	• Defensive parsing is recommended: some fields may be omitted or null depending on data quality or the API’s quirks.
"""
class historical:
    def __init__(self, json_content=None):
        self.data=None; self.error_messages=[]; self.error=True
        if json_content: self.json_content = IterDict.isNested(json_content)
        if getattr(self, "json_content", None):
            self.check_data(); self.display_error_messages()
            if not self.error: self.parse()
    def display_error_messages(self):
        if self.error_messages:
            for x, t in self.error_messages: print(f'{x}: {t}')
    def check_data(self):
        json_content = self.json_content
        def validate_api_responses(api_responses):
            validation_list = []
            for index, response in enumerate(api_responses):
                for url, content in response.items():
                    error_message = content.get('response', {}).get('status', {}).get('error_message', "")
                    quotes = content.get('response', {}).get('data', {}).get('quotes', None)
                    quotes_valid = False if quotes==[] or quotes is None else True
                    if error_message!="SUCCESS" or not quotes_valid: validation_list.append((url, False))
                    else: validation_list.append((url, True))
            return validation_list
        def process_messages(data, verbose=False):
            messages = []
            def clean(msgs):
                try: messages_list = [f for f in msgs if 'code:' not in f]; return [f.split("-")[-1].split(": ")[-1] for f in messages_list]
                except: return msgs
            def extract_message_fields(data):
                result = {}
                if isinstance(data, dict):
                    for key, value in data.items():
                        if 'error_message' in key.lower(): result[key] = value
                        elif isinstance(value, (dict, list)): result.update(extract_message_fields(value))
                elif isinstance(data, list):
                    for item in data: result.update(extract_message_fields(item))
                return result
            def process_entry(key, value):
                if value is None: return
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                if v is not None: messages.append(f"{key} - {k}: {v}")
                        else:
                            if item is not None: messages.append(f"{key}: {item}")
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items(): process_entry(f"{key} - {sub_key}", sub_value)
                else: messages.append(f"{key}: {value}")
            extracted_data = extract_message_fields(data)
            for key, value in extracted_data.items(): process_entry(key, value)
            if verbose: [print(message) for message in messages]
            else: return clean(messages)
        validate_crypto_content = validate_api_responses(json_content); error_messages_list = []
        for url, check in validate_crypto_content:
            if not check:
                crypto_id = idextract.extract(url, idextract.CRYPTO_ID)
                found_slug = CoinQuery.ID(crypto_id)
                slug_name = IterDict.search_keys_in(found_slug, "name")
                data = IterDict.find(json_content, target_key=url)
                check_quote_values = IterDict.search_keys_in(data, "quotes")
                if not check_quote_values: message = "No data exists for the specified time periods."
                else:
                    n_message = process_messages(data)
                    message = n_message[0] if n_message else None
                error_messages_list.append((slug_name, message))
            self.error_messages = error_messages_list
            valid_urls = [url for url, is_valid in validate_crypto_content if is_valid]
            self.json_content = [entry for entry in json_content if any(url in entry for url in valid_urls)]
            if valid_urls: self.error = False
    def process_json(self):
        rows = []; dataset = IterDict.find(self.json_content, False, 'response')
        for content in dataset:
            data = content.get('data', {}); status = content.get('status', {}); individual_data = []
            quotes = data.get('quotes', [])
            for quote in quotes:
                row = {
                    'symbol':data.get('symbol',pd.NA),'name':data.get('name',pd.NA),
                    'open':quote.get('quote',{}).get('open',pd.NA),'high':quote.get('quote',{}).get('high',pd.NA),'low':quote.get('quote',{}).get('low',pd.NA),
                    'close':quote.get('quote',{}).get('close',pd.NA),'volume':quote.get('quote',{}).get('volume',pd.NA),'marketCap':quote.get('quote',{}).get('marketCap',pd.NA),
                    'timestamp':quote.get('quote',{}).get('timestamp',pd.NA),'time_queried':status.get('timestamp',pd.NA),
                }
                individual_data.append(row)
            df = pd.DataFrame(individual_data); rows.append(df)
        data = pd.concat(rows, ignore_index=True) if rows else None
        column_order = ['timestamp','symbol','name','open','high','low','close','volume','marketCap','time_queried']
        data = data[column_order]; data.rename(columns={'timestamp':'date'}, inplace=True)
        data['date'] = pd.to_datetime(data['date']); data = normalize_time(data, 'date')
        data['time_queried'] = pd.to_datetime(data['time_queried']); self.data = data
    def parse(self): self.process_json()
    def DATA(self):
        if not is_valid_dataframe(self.data):
            if self.error_messages: raise CryptoHistoricalNoDataError(self.error_messages)
            raise CryptoHistoricalUnavailableError()
        return self.data
    def __dir__(self): return ['DATA']


def __dir__():
    return __all__
