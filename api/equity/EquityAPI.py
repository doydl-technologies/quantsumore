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

"Equity data retrieval from public providers."
from ..prep import equity_adapter
from .parse._info import profile
from .parse._metric import quote_statistics
from .parse._intra import latest
from .parse._trailing import last
from .parse._periods import historical
from .parse._listing import ipo
from .parse._shareholders import dividend
from .parse._financials import statements
from ..._http.connection import Connection
from ...strata_utils import IterDict


__all__ = ['engine']



class ProfileClient:
    def __init__(self, adapter):
        self._adapter = adapter

    def _fetch(self, ticker):
        make = getattr(self._adapter, 'make')
        url = make(query='profile', ticker=ticker)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        ) 
        if content:
            obj = profile(content)
            return obj.DATA()

    def bio(self, ticker):
        "Provides an overview or summary of a company's information based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('company_description')

    def executives(self, ticker):
        "Provides information about a company's executives based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('executives')

    def info(self, ticker):
        "Retrieves the basic information of a company based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('basic_info')

    def industry(self, ticker):
        "Retrieves the industry and sector classification for a company based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('industry_sector')

    def contact(self, ticker):
        "Retrieves contact information for a company based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('contact_details')

    def security(self, ticker):
        "Retrieves security-related information for a company based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('security_details')

    def filings(self, ticker):
        "Retrieves a company's regulatory filings based on its ticker symbol."
        data = self._fetch(ticker)
        return data and data.get('company_filings')

    def full(self, ticker):
        "Retrieves the complete company profile as a processed dictionary."
        return self._fetch(ticker)

    def __dir__(self):
        return [
            'bio',
            'executives',
            'info',
            'industry',
            'contact',
            'security',
            'filings',            
            'full',
        ]
        



class APIClient:
    def __init__(self, adapter):
        self.adapter = adapter
        self.Profile = ProfileClient(adapter)

    def Stats(self, ticker):
        "Provides various statistical information and financial metrics about a company based on its ticker symbol."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='stats', ticker=ticker)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )            
        if content:
            obj = quote_statistics(content)
            return obj.DATA()        

    def Historical(self, ticker, start, end):
        "Retrieves historical stock price data for a company based on its ticker symbol and a specified date range."
        if all(x is None for x in [start, end]):
            raise ValueError("Start and end dates must be provided for historical data requests.")
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='price', ticker=ticker, start=start, end=end)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )            
        if content:
            obj = historical(content)
            return obj.DATA()

    # Quotes retain the provider's reported price and observation timestamp.
    def Latest(self, ticker):
        "Retrieves the latest stock price for a company based on its ticker symbol."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='latest', ticker=ticker)        
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )       
        if content:
            obj = latest(content)
            return obj.DATA()

    def Dividends(self, ticker):
        "Retrieves dividend data for the specified ticker symbol."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='dividend_history', ticker=ticker)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )         
        if content:
            obj = dividend(content)
            return (obj.DividendReport, obj.DividendData)

    def Lastn(self, ticker,  range="1d", interval="1m"):
        "Retrieve the latest stock price data for a given ticker symbol, with flexible time range and granularity."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='last', ticker=ticker, range=range, interval=interval)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )         
        if content:
            obj = last(content)
            return obj.DATA()

    def Financials(self, ticker, period="Quarterly"):
        "Retrieves financial statement data for the specified ticker symbol."
        valid_periods = {'Quarterly': ['Q', 'Quarter', 'Qtr'], 'Annually': ['A', 'Annual']}
        period = IterDict.key_from_mapping(period, valid_periods, invert=False)
        if not period:
            raise ValueError("Invalid period.")
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='financials', ticker=ticker, period=period)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )      
        if content:
            obj = statements(json_content=content)
            return (obj.IncomeStatement, obj.BalanceSheet, obj.CashFlowStatement)

    def IPO(self, date=None):
        "Retrieves IPO data for the specified date or date range."
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='ipo', period=date)
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )     
        if content:
            obj = ipo(content)
            return obj.DATA()

    def __dir__(self):
        return [
            'Profile',        
            'Stats',               
            'Financials',
            'Dividends',
            'Historical',
            'Lastn',
            'Latest',
            'IPO'
        ]

engine = APIClient(equity_adapter)

def __dir__():
    return __all__


