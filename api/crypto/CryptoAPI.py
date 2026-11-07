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

"Cryptocurrency data retrieval from public providers."
from ..prep import crypto_adapter
from .parse._periods import historical
from .parse._intra import latest
from ..._http.connection import Connection


__all__ = ['engine']


class APIClient:
    def __init__(self, adapter):
        self.adapter = adapter

    def Latest(self, slug, baseCurrencySymbol=None, quoteCurrencySymbol=None, limit=100, exchangeType="all", cryptoExchange=None):
        "Fetches and returns the latest live cryptocurrency market data for a specified asset."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='live', slug=slug, baseCurrencySymbol=baseCurrencySymbol, quoteCurrencySymbol=quoteCurrencySymbol, limit=limit, exchangeType=exchangeType)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )         
        if content:
            obj = latest(content, cryptoExchange=cryptoExchange)
            data = obj.DATA()
            return data

    def Historical(self, slug, start, end):
        "Fetches and returns historical cryptocurrency data for a specified asset within a given date range."
        if all(x is None for x in [start, end]):
            raise ValueError("Start and end dates must be provided for historical data requests.")
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='historical', slug=slug, start=start, end=end)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )          
        if content:
            obj = historical(content)
            data = obj.DATA()
            return data
           
    def __dir__(self):
        return ['Historical','Latest'] 



engine = APIClient(crypto_adapter)

def __dir__():
    return __all__




