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

"Foreign-exchange data retrieval from public providers."
from ..prep import forex_adapter
from .parse._rates import interbank, conversion
from .parse._periods import historical
from .parse._intra import latest
from ..._http.connection import Connection


__all__ = ['engine']




class APIClient:
    def __init__(self, adapter):
        self.adapter = adapter  

    def Historical(self, currency_pair, start, end):
        "Retrieves historical exchange rates for one currency pair over a specified date range."
        if all(x is None for x in [start, end]): 
            raise ValueError("Start and end dates must be provided for historical data requests.")  
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='historical', currency_pair=currency_pair, start=start, end=end)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )     
        if content:
            obj = historical(content)
            historical_data = obj.DATA()
            return historical_data
           
    def Interbank(self, base_currency, filter_currencies=None, ignore_currencies=None):
        "Retrieves live interbank exchange rates for specified currencies."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='interbank', base_currency=base_currency, filter_currencies=filter_currencies, ignore_currencies=ignore_currencies)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )        
        if content:
            obj = interbank(content)
            interbank_data = obj.DATA()
            return interbank_data
       
    def BidAsk(self, currency_pair):
        "Retrieves current bid and ask prices, along with the spread, for a specified currency pair."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='bid_ask', currency_pair=currency_pair)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )     
        if content:
            obj = latest(content)
            bid_ask_data = obj.DATA()
            return bid_ask_data   

    def CurrencyConversion(self, currency_pair, conversion_amount=1):
        "Converts a specified amount from one currency to another using the latest available conversion rates."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='convert', currency_pair=currency_pair)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        ) 
        if content:
            obj = conversion(content, conversion_amount=conversion_amount)
            conversion_data = obj.DATA()
            return conversion_data
       
    def __dir__(self):
        return [
            'Historical',
            'Interbank',
            'BidAsk',
            'CurrencyConversion',
        ]

          
engine = APIClient(forex_adapter)


def __dir__():
    return __all__
