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

from ...shape_tools import is_valid_dataframe
from ....date_parser import dtparse
from ....strata_utils import IterDict
from ....proxy import Proxy
from ....exceptions import (
    FXNoDataError,
    FXDataUnavailableError,
)
from ....markup import idextract


__all__ = ['historical']





# Defer dependency imports until first use.
pd = Proxy("pandas", None)


"""
Expected Input: Historical FX Rates API Response

This class expects as input the parsed JSON response for historical foreign exchange rates.
The input structure includes a list of daily exchange rates for a specified currency pair, 
each with its value and the date of the quote, as returned by the API.

Example structure:
[
  {
    "<string-key>": {
      "response": {
        "d": [
          {
            "RatePair": str,         # Currency pair, e.g. "EURUSD"
            "RatePairValue": float,  # Exchange rate value
            "LastUpdate": str,       # Date/time, e.g. "Sun, 01 Jan 2023 00:00:00"
            "CallCount": int         # API usage tracker (typically 0)
          }
          # ...more daily rate objects...
        ]
      }
    }
  }
]
"""
class historical:
    def __init__(self, json_content=None):
        self.cleaned_data=None; self.data=None; self.error=True
        if json_content: self.json_content = IterDict.isNested(json_content)
        if getattr(self, 'json_content', None):
            self.check_data(); self.display_error_messages()
            if not self.error:
                self.parse()
                if self.cleaned_data: self._create_dataframe()
    def display_error_messages(self):
        if getattr(self, 'error_messages', None):
            for message in self.error_messages: print(message)
    def check_data(self):
        json_content = self.json_content
        def validate_api_responses(api_responses):
            validation_list = []
            for index, response in enumerate(api_responses):
                for url, content in response.items():
                    quotes = content.get('response', {}).get('d', {})
                    if quotes == [] or quotes is None: validation_list.append((url, False))
                    else: validation_list.append((url, True))
            return validation_list
        validate_fx_content = validate_api_responses(json_content)
        error_messages_list = []
        for url, check in validate_fx_content:
            if not check:
                currency_pair = idextract.extract(url, idextract.CURRENCY_PAIR)
                data = IterDict.find(json_content, target_key=url)
                check_quote_values = IterDict.search_keys_in(data, "d")
                message = "No data exists for the specified time periods."
        self.error_messages = error_messages_list
        valid_urls = [url for url, is_valid in validate_fx_content if is_valid]
        self.json_content = [entry for entry in json_content if any(url in entry for url in valid_urls)]
        if valid_urls: self.error = False
    def _create_dataframe(self):
        df = pd.DataFrame(self.cleaned_data)
        df['InverseRate'] = round((1/df['RatePairValue']),6)
        df['LastUpdate'] = df['LastUpdate'].apply(dtparse.parse, to_format='%Y-%m-%d')
        df['BaseCurrency'] = df['RatePair'].str.slice(0,3)
        df['QuoteCurrency'] = df['RatePair'].str.slice(3,6)
        df.rename(columns={'LastUpdate':'Timestamp','RatePair':'CurrencyPair','RatePairValue':'Rate'},inplace=True)
        column_order=['Timestamp','CurrencyPair','BaseCurrency','QuoteCurrency','Rate','InverseRate']
        filtered_columns = [col for col in column_order if col in df.columns]
        self.data = df[filtered_columns]
    def parse(self):
        cleaned_content = IterDict.find(self.json_content, first_only=False, target_key="response", wrap=False)
        flattened_data = []
        for response in cleaned_content:
            for item in response['d']:
                new_item = {key:value for key,value in item.items() if key != 'CallCount'}
                flattened_data.append(new_item)
        if flattened_data: self.cleaned_data = flattened_data
    def DATA(self):
        if not is_valid_dataframe(self.data):
            if getattr(self, 'error_messages', None): raise FXNoDataError(self.error_messages)
            raise FXDataUnavailableError()
        return self.data
    def __dir__(self): return ['DATA']
    
def __dir__():
    return __all__
