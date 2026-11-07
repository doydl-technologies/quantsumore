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


from ....markup import idextract
from ...market_utils import ExchangeQuery
from ...shape_tools import normalize_time, is_valid_dataframe
from ....strata_utils import IterDict
from ....proxy import Proxy
from ....exceptions import (
    CryptoLiveQuoteNoDataError, 
    CryptoLiveQuoteUnavailableError,
)


__all__ = ['latest']



# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Cryptocurrency Market Pairs API Response

This class expects, as input, the parsed JSON response from a cryptocurrency markets API,
providing information on all available trading pairs, prices, and associated metadata for a given asset.

Example Input Structure:
[
  {
    "<string-key>": {   # Usually a URL-encoded string or endpoint signature, e.g. "...+bitcoin&start=1&limit=100..."
      "response": {
        "data": {
          "id": int,            # Asset ID, e.g. 1 for Bitcoin
          "name": str,          # Asset name, e.g. "Bitcoin"
          "symbol": str,        # Asset symbol, e.g. "BTC"
          "numMarketPairs": int,# Total number of market pairs for this asset
          "marketPairs": [      # List of market pair objects (each an exchange pair/trading venue)
            {
              "rank": int,                     # Ranking among market pairs
              "exchangeId": int,               # Unique exchange ID
              "exchangeName": str,             # Name of the exchange, e.g. "Kraken"
              "exchangeSlug": str or float,    # Exchange slug or sometimes a float (API inconsistency)
              "marketPair": str,               # Market pair symbol, e.g. "XBT/EUR"
              "category": str,                 # "spot", "derivative", etc.
              "marketUrl": str,                # Direct URL to the exchange/market
              "price": float,                  # Latest price for this market pair
              "volumeUsd": float,              # 24h trading volume in USD
              "effectiveLiquidity": float,     # Estimated available liquidity
              "lastUpdated": str,              # ISO 8601 timestamp, e.g. "2025-08-04T06:51:07.000Z"
              "quote": float,                  # Quoted price (may be in quote asset)
              "volumeBase": float,             # Volume in base asset
              "volumeQuote": float,            # Volume in quote asset
              "feeType": str,                  # "percentage" or "flat", etc.
              "depthUsdNegativeTwo": float,    # Order book depth at -2% from mid price
              "depthUsdPositiveTwo": float,    # Order book depth at +2% from mid price
              "reservesAvailable": int,        # 1 if exchange has published PoR, else 0
              "porAuditStatus": int,           # Proof-of-Reserves audit status flag
              "volumePercent": float,          # Market share percentage
              "indexPrice": float,             # Index price, if provided
              "isVerified": int,               # 1 if market is verified, else 0
              "quotes": [                      # List of additional quote objects
                {
                  "id": str,                   # Quote asset ID as string
                  "price": float,              # Quote price
                  "volume24h": float,          # 24h volume for this quote
                  "indexPrice": float          # Index price for this quote
                }
                # ...more quote objects...
              ],
              "type": str,                     # Market type, e.g. "cex"
              "centerType": str,               # Center type, e.g. "cex"
              "hideStarsMarket": int,          # UI/display flag
              # ...other market pair fields, such as outlier flags, marketScore, etc.
            }
            # ...more market pairs...
          ],
          "sort": str,                 # Sorting method used, e.g. "cmc_rank_advanced"
          "direction": str,            # "asc" or "desc"
          "sponsoredExchange": [       # (Optional) Sponsored exchanges for UI display/ads
            {
              "eventId": int,
              "customName": str,
              "customLogo": str,            # URL to logo image
              "subInfos": [                 # Country-specific ad links/info
                {
                  "url": str,
                  "showMsg": str,
                  "supportCountries": [str],
                  "excludeCountries": [str],
                  "customOptions": str      # Serialized options, e.g. "{}"
                }
                # ...more subInfos...
              ],
              "customOptions": str
            }
            # ...more sponsored exchanges...
          ]
        },
        "status": {
          "timestamp": str,         # ISO 8601, e.g. "2025-08-04T06:54:22.954Z"
          "error_code": str or int, # "0" on success
          "error_message": str,     # "SUCCESS" on success
          "elapsed": str or int,    # Elapsed request time in ms or s
          "credit_count": int       # API credits consumed
        }
      }
    }
  }
  # ...more items for additional queries (if batched)...
]

Notes:
	• The top-level list contains one or more objects, each keyed by a string unique to the request (often URL or endpoint+params).
	• Field types may vary due to API quirks (e.g., exchangeSlug can be str or float).
	• "marketPairs" is a list of dicts, one for each trading venue/pair.
	• "sponsoredExchange" is for ad/marketing display; may be missing.
	• "quotes" is a nested list per market pair, providing additional price/volume for other quote currencies.

Handle missing or extra fields defensively: this API sometimes adds or omits fields without notice.
"""
class latest:
    def __init__(self, json_content=None, cryptoExchange=None):
        self.crypto_exchange=cryptoExchange; self.crypto_exchange_ids=None; self.data=None; self.error_messages=[]; self.error=True
        if json_content: self.json_content = IterDict.isNested(json_content)
        if self.crypto_exchange and not isinstance(self.crypto_exchange, list): self.crypto_exchange = [self.crypto_exchange]
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
                    if error_message != "SUCCESS": validation_list.append((url, False))
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
                    for sub_key, sub_value in value.items():
                        process_entry(f"{key} - {sub_key}", sub_value)
                else: messages.append(f"{key}: {value}")
            extracted_data = extract_message_fields(data)
            for key, value in extracted_data.items(): process_entry(key, value)
            if verbose: [print(message) for message in messages]
            else: return clean(messages)
        validate_crypto_content = validate_api_responses(json_content); error_messages_list = []
        for url, check in validate_crypto_content:
            if not check:
                slug_name = idextract.extract(url, idextract.CRYPTO_SLUG)
                data = IterDict.find(json_content, target_key=url)
                n_message = process_messages(data)
                message = n_message[0] if n_message else None
                error_messages_list.append((slug_name, message))
            self.error_messages = error_messages_list
            valid_urls = [url for url, is_valid in validate_crypto_content if is_valid]
            self.json_content = [entry for entry in json_content if any(url in entry for url in valid_urls)]
            if valid_urls: self.error = False
    def clean_exchanges(self):
        if self.crypto_exchange:
            exchanges = self.crypto_exchange
            unique_exchanges = list(set(exchanges))
            exchange_ids = [ExchangeQuery.FindID(ex) for ex in unique_exchanges]
            self.crypto_exchange_ids = [item for item in exchange_ids if item is not None]
    def process_json(self, data):
        market_pairs_data = data['data']['marketPairs']; rows = []
        for market_pair in market_pairs_data:
            row = {
                'coinSymbol':data['data']["symbol"],'coinName':data['data']["name"],'exchangeId':market_pair.get('exchangeId',pd.NA),'exchangeName':market_pair.get('exchangeName',pd.NA),
                'exchangeSlug':market_pair.get('exchangeSlug',pd.NA),'marketPair':market_pair.get('marketPair',pd.NA),'category':market_pair.get('category',pd.NA),'baseSymbol':market_pair.get('baseSymbol',pd.NA),
                'baseCurrencyId':market_pair.get('baseCurrencyId',pd.NA),'quoteSymbol':market_pair.get('quoteSymbol',pd.NA),'quoteCurrencyId':market_pair.get('quoteCurrencyId',pd.NA),'price':market_pair.get('price',pd.NA),
                'volumeUsd':market_pair.get('volumeUsd',pd.NA),'effectiveLiquidity':market_pair.get('effectiveLiquidity',pd.NA),'lastUpdated':market_pair.get('lastUpdated',pd.NA),'quote':market_pair.get('quote',pd.NA),
                'volumeBase':market_pair.get('volumeBase',pd.NA),'volumeQuote':market_pair.get('volumeQuote',pd.NA),'feeType':market_pair.get('feeType',pd.NA),'depthUsdNegativeTwo':market_pair.get('depthUsdNegativeTwo',pd.NA),
                'depthUsdPositiveTwo':market_pair.get('depthUsdPositiveTwo',pd.NA),'volumePercent':market_pair.get('volumePercent',pd.NA),'exchangeType':market_pair.get('type',pd.NA),'timeQueried':data['status']["timestamp"],
            }
            rows.append(row)
        if self.crypto_exchange_ids: rows = [pair for pair in rows if pair["exchangeId"] in self.crypto_exchange_ids]
        rows = [{key:value for key,value in row.items() if key not in ['exchangeId','baseCurrencyId','quoteCurrencyId','exchangeSlug']} for row in rows]
        return rows
    def iterate(self):
        rows = []; dataset = IterDict.find(self.json_content, False, 'response')
        for data in dataset:
            result = self.process_json(data)
            if result: rows.append(result)
        row_data = rows; flattened_data = [item for sublist in row_data for item in sublist]
        df = pd.DataFrame(flattened_data)
        df['timeQueried'] = pd.to_datetime(df['timeQueried']); df['lastUpdated'] = pd.to_datetime(df['lastUpdated'])
        df = normalize_time(df, 'lastUpdated')
        self.data = df
    def parse(self):
        self.clean_exchanges(); self.iterate()
    def DATA(self):
        if not is_valid_dataframe(self.data):
            if self.error_messages: raise CryptoLiveQuoteNoDataError(self.error_messages)
            raise CryptoLiveQuoteUnavailableError()
        return self.data
    def __dir__(self): return ['DATA']


def __dir__():
    return __all__
