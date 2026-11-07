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

"Retrieve and categorize company financial statements and dividends."
import re

from ..api.equity.parse._financials import statements
from ..api.equity.parse._shareholders import dividend
from ..api.prep import equity_adapter
from .._http.connection import Connection
from ..strata_utils import IterDict
from ..exceptions import (
    DividendHistoryNoDataError,
    DividendHistoryUnavailableError,
    FinancialStatementUnavailableError,
    FinancialDataNotLoadedError,
    APIRequestError,    
)

__all__ = [
    'get_process'
    ]    


def _normalize_base_url(u):
    if isinstance(u, (list, tuple)) and u:
        u = u[0]
    if isinstance(u, (bytes, bytearray)):
        u = u.decode()
    return str(u).rstrip('/')
   
def fetch_financials_dividends_pair(pairs, timeout=20):
    """Fetch both financial statements and dividends directly from their providers."""
    if len(pairs) != 2:
        raise ValueError("Provide exactly two (base, endpoint) tuples")
    return [item for pair in pairs for item in Connection.Request(pair, timeout=timeout)]
       
class APIClient:
    """Fetch and parse company financial statements and dividend data."""
    def __init__(self, adapter):
        """Store an asset adapter providing make() for endpoint URL construction."""
        self.adapter = adapter

    def _make_request(self, url):
        "Dispatch outbound API requests for the specified URL(s)."
        base = url[0].decode() if isinstance(url[0], bytes) else url[0]
        endpoint = url[1]
        content = Connection.Request(
            url=(base, endpoint),
            params=None,
            return_url=True
        )      
        return content
    
    def _make_pair(self, pairs):
        return fetch_financials_dividends_pair(pairs)
       
    def _urls(self, ticker, period):
        """
        Construct all required endpoint URLs for both financials and dividends.

        Parameters:
        ----------
        ticker : str
            The stock ticker symbol to query.
        period : str
            Reporting period (e.g., "Q", "Quarterly", "A", "Annual").

        Returns
        -------
        urls : list of str
            List of endpoint URLs needed to fetch all relevant data.

        Raises
        ------
        ValueError
            If an unsupported reporting period is provided.
        """    	
        valid_periods = {'Quarterly': ['Q', 'Quarter', 'Qtr'], 'Annually': ['A', 'Annual']} 
        period = IterDict.key_from_mapping(period, valid_periods, invert=False)
        if not period: raise ValueError("Invalid period.")
        urls = []; make = getattr(self.adapter, 'make')
        f = make(query='financials', ticker=ticker, period=period)
        f_base = f[0].decode() if isinstance(f[0], bytes) else f[0]
        f_ep = f[1]
        d = make(query='dividend_history', ticker=ticker)
        d_base = d[0].decode() if isinstance(d[0], bytes) else d[0]
        d_ep = d[1]
        urls.append((f_base, f_ep)); urls.append((d_base, d_ep))
        return urls

    def _categorize_content(self, content):     
        """
        Group fetched response content into financial statement and dividend categories.

        Parameters:
        ----------
        content : list of dict
            Raw response payload(s) returned from API requests.

        Returns
        -------
        categorized_content : dict
            Dictionary with two keys:
                - 'financial_statements': list of statement payloads
                - 'dividend': list of dividend payloads

        Notes
        -----
        Categorization is based on URL patterns; endpoints containing 'dividend' are
        grouped separately from those containing 'financials'.
        """    	
        categorized = {'dividend': [], 'financial_statements': []}
                    
        # Flatten: accept list[dict] or list[list[dict]]
        flat = []
        for entry in content:
            if isinstance(entry, dict):
                flat.append(entry)
            elif isinstance(entry, list):
                flat.extend(d for d in entry if isinstance(d, dict))

        for entry in flat:
            for url, data in entry.items():
                if isinstance(url, str) and url.startswith(('https://', 'http://')):
                    u = url.lower()
                    if "dividend" in u:                   
                        categorized['dividend'].append({url: data})
                    elif "financials" in u:
                        categorized['financial_statements'].append({url: data})
        return categorized     

    def Process(self, ticker, period="Q"):
        "Fetch and parse all available financial statement and dividend data for a specified ticker and period."
        urls = self._urls(ticker=ticker, period=period)
        try:
            responses = fetch_financials_dividends_pair(urls)
        except APIRequestError as e:
            return {"error": "REQUEST_FAILED", "detail": str(e)}        
        categorized = self._categorize_content(responses)
        
        results = {'financial_statements': [], 'dividend': []}
        fin_content = categorized.get('financial_statements', [])
        if fin_content:
            try:
                fs_obj = statements(json_content=fin_content)
                results['financial_statements'] = [(fs_obj.IncomeStatement, fs_obj.BalanceSheet, fs_obj.CashFlowStatement)]
            except (FinancialDataNotLoadedError, FinancialStatementUnavailableError): pass
        div_content = categorized.get('dividend', [])
        if div_content:
            try:
                dv_obj = dividend(json_content=div_content)
                results['dividend'] = [(dv_obj.DividendReport, dv_obj.DividendData)]
            except (DividendHistoryNoDataError, DividendHistoryUnavailableError): pass
        return results


def get_process():
    from quantsumore.api.prep import equity_adapter
    return APIClient(equity_adapter)

def __dir__():
    return __all__
