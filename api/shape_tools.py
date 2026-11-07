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

from ..proxy import Proxy


__all__ = [
    'filter_dataframe_columns',
    'rename_dataframe_columns',
    'apply_conversion_to_columns',
    'is_valid_dataframe',
    'normalize_time',
]




# Defer dependency imports until first use.
pd = Proxy("pandas", None)


def filter_dataframe_columns(df, cols):
    """Filter DataFrame to only given columns that exist."""
    df2 = deepcopy(df)
    if isinstance(cols, str): cols = [cols]
    return df2[[c for c in cols if c in df2.columns]]

def rename_dataframe_columns(df, rename_dict):
    """Rename DataFrame columns using a valid mapping dict."""
    df2 = deepcopy(df)
    renames = {k:v for k,v in rename_dict.items() if k in df2.columns}
    return df2.rename(columns=renames)

def apply_conversion_to_columns(df, cols, fun):
    """Apply a function to given columns of DataFrame."""
    df2 = deepcopy(df)
    if isinstance(cols, str): cols = [cols]
    for col in cols:
        if col in df2.columns:
            df2[col] = [fun(x) if isinstance(x,(str,int,float)) else x for x in df2[col]]
    return df2

def is_valid_dataframe(df):
    """True if valid, non-empty DataFrame."""
    return isinstance(df, pd.DataFrame) and not df.empty

def normalize_time(df, cols):
    """Normalize datetime columns to midnight."""
    df2 = deepcopy(df)
    if isinstance(cols, str): cols = [cols]
    for c in cols:
        df2[c] = pd.to_datetime(df2[c]).dt.normalize()
    return df2

def __dir__():
    return __all__
