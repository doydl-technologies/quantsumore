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

from ..strata_utils import IterDict


__all__ = ['Vertical_Analysis']




class Vertical_Analysis:
    def __init__(self, analyze_instance): self.parent = analyze_instance
    def _VerticalAnalysis(self, financial_statement):
        import pandas as pd
        valid_statements = {
            "Income Statement": ["I","IS","Income","Income_Statement","Income Statement"],
            "Balance Sheet": ["Balance Sheet","B","BS","Balance_Sheet"],
            "Cash Flow Statement": ["Cash Flow Statement","Cash_Flow_Statement","C","CF","Cash Flow","Cash_Flow","Cash"],
        }
        financial_statement = IterDict.key_from_mapping(financial_statement, valid_statements, invert=False)
        if financial_statement == 'Income Statement':
            statement = deepcopy(self.parent.income_statement)
            if statement is not None and not statement.empty:
                statement.replace(['--',''], pd.NA, inplace=True)
                statement = statement.apply(pd.to_numeric, errors='coerce')
                vertical = statement.div(statement.loc['Total Revenue'])
                v_fmt = vertical.map(lambda x: f"{x:.2%}" if pd.notna(x) else '')
                v_fmt = v_fmt.where(~self.parent.income_statement.isin(['--','']), self.parent.income_statement)
                return v_fmt
        if financial_statement == 'Balance Sheet':
            statement = deepcopy(self.parent.balance_sheet)
            if statement is not None and not statement.empty:
                statement.replace(['--',''], pd.NA, inplace=True)
                statement = statement.apply(pd.to_numeric, errors='coerce')
                vertical = statement.div(statement.loc['Total Assets'])
                v_fmt = vertical.map(lambda x: f"{x:.2%}" if pd.notna(x) else '')
                v_fmt = v_fmt.where(~self.parent.balance_sheet.isin(['--','']), self.parent.balance_sheet)
                return v_fmt
        if financial_statement == 'Cash Flow Statement':
            statement = deepcopy(self.parent.cash_flow_statement)
            if statement is not None and not statement.empty:
                statement.replace(['--',''], pd.NA, inplace=True)
                statement = statement.apply(pd.to_numeric, errors='coerce')
                vertical = statement.div(statement.loc['Net Cash Flow-Operating'])
                v_fmt = vertical.map(lambda x: f"{x:.2%}" if pd.notna(x) else '')
                v_fmt = v_fmt.where(~self.parent.cash_flow_statement.isin(['--','']), self.parent.cash_flow_statement)
                return v_fmt
               
def __dir__():
    return __all__
