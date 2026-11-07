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

"""Retrieve U.S. Treasury bill rates and yield-curve data."""
from io import StringIO

from ..prep import treasury_adapter
from .parse._securities import riskfreerate
from ...date_parser import dtparse


__all__ = ['engine']




class APIClient:
    def __init__(self, adapter):
        self.adapter = adapter  

    def _exists(self, df):
        """Return whether df is non-None and its empty attribute is False."""
        import pandas as pd
        return df is not None and getattr(df, "empty", True) is False       

    def _request_csv(self, url, period):
        """
        Downloads and filters a Treasury CSV file from the specified URL as a pandas DataFrame.

        This method performs an HTTP GET request to download the CSV data, parses it into a DataFrame,
        and filters the result by the requested period (year or month).

        Parameters:
        ----------
        url : str
            The full download URL for the Treasury CSV resource.
        period : None, str, or int
            The period for which data should be returned:
                - None or "CY" (case-insensitive): Use the current calendar year.
                - 4-digit year (e.g., 2022): Filter for that entire year.
                - 6-digit year and month (e.g., 202204): Filter for that year and month.

        Returns:
        -------
        pandas.DataFrame
            The filtered DataFrame indexed by row, with 'Date' as a pandas datetime column.
            Returns an empty DataFrame if there are no matches.

        Raises:
        ------
        ValueError
            If the period is not one of the supported formats.
        """
        today = dtparse.nowCT()
        if period is None or str(period).lower() == 'cy':
            year, month = today.year, None
        else:
            ps = str(period)
            if len(ps) == 6 and ps.isdigit():
                year, month = int(ps[:4]), int(ps[4:])
            elif len(ps) == 4 and ps.isdigit():
                year, month = int(ps), None
            else:
                raise ValueError("`period` must be None, 'CY', YYYY, or YYYYMM")

        headers = {"User-Agent": "Mozilla/5.0"}
        
        import requests
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        
        import pandas as pd
        response = pd.read_csv(StringIO(resp.text))

        if 'Date' in response.columns:
            response['Date'] = pd.to_datetime(response['Date'], errors='coerce')
            mask = response['Date'].dt.year == year
            if month is not None:
                mask &= response['Date'].dt.month == month
            response = response.loc[mask]
            response = response.reset_index(drop=True)
        return response        

    def TBill(
        self,
        period=None,
        full_table=False,
    ):
        """
        Fetches and returns the most up-to-date daily Treasury bill rates.

        Downloads the latest Treasury bill rates from the U.S. Treasury (CSV API), filters
        the result to the requested period, and returns either summary rates or the full table.

        Parameters:
        ----------
        period : str, int, or None, optional
            The period for the data query:
                - 'CY' (str): Current year.
                - YYYY (int): Specific year (e.g., 2021).
                - YYYYMM (int): Specific month of a year (e.g., 202308).
                - None: Defaults to the current month of the current year.
        full_table : bool, default False
            If True, returns the full filtered DataFrame instead of summary rates.

        Returns:
        -------
        dict or pandas.DataFrame
            The latest daily Treasury bill rates as a dictionary (summary),
            or as a DataFrame if `full_table` is True.
        """
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='tbill', period=period)
        content = self._request_csv(url=url, period=period)
        if self._exists(content):
            obj = riskfreerate(content, kind="tbill", full=full_table)
            return obj.DATA()
           
    def Yield(
        self,
        period=None,
        full_table=False,
    ):
        """
        Fetches and returns the most up-to-date Daily Treasury Par Yield Curve Rates.

        Downloads the latest yield curve rates for U.S. Treasury notes and bonds (maturities: 1, 2, 3, 5, 7, 10, 20, 30 years)
        from the U.S. Treasury CSV endpoint, filters to the requested period, and returns either a summary dictionary
        or the full filtered table.

        Parameters:
        ----------
        period : str, int, or None, optional
            The time period for the data query:
                - 'CY' (str): Current year.
                - YYYY (int): Specific year (e.g., 2021).
                - YYYYMM (int): Specific month of a year (e.g., 202308).
                - None: Defaults to the current month of the current year.
        full_table : bool, default False
            If True, returns the full filtered DataFrame instead of summary rates.

        Returns:
        -------
        dict or pandas.DataFrame
            The latest Daily Treasury Par Yield Curve Rates as a dictionary (summary),
            or as a DataFrame if `full_table` is True.
        """
        make_method = getattr(self.adapter, 'make')
        url = make_method(query='tyield', period=period)
        content = self._request_csv(url=url, period=period)       
        if self._exists(content):
            obj = riskfreerate(content, kind="tyield", full=full_table)
            return obj.DATA()
           
    def YieldAll(
        self,
        period=None,
    ):
        """
        Fetches and returns the most up-to-date Treasury Yield Curve Rates for all available maturities.

        Retrieves the latest yield curve rates from the U.S. Treasury for a comprehensive set of maturities,
        including short-term bills and long-term notes and bonds.

        Parameters:
        ----------
        period : str, int, or None, optional
            The time period for the data query:
                - 'CY' (str): Current year.
                - YYYY (int): Specific year (e.g., 2021).
                - YYYYMM (int): Specific month and year (e.g., 202308).
                - None: Defaults to the current month of the current year.

        Returns:
        -------
        pandas.DataFrame
            The latest Treasury yield curve rates for all available maturities as a DataFrame.
        """
        return self.Yield(period=period, full_table=True)

    def __dir__(self):
        return [
            'TBill',
            'Yield',
            'YieldAll',
        ]       


engine = APIClient(treasury_adapter)

def __dir__():
    return __all__

