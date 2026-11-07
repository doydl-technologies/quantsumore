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

from copy import deepcopy

from ..strata_utils import IterDict


__all__ = ['Common_Size']




class Common_Size:
    def __init__(self, analyze_instance): self.parent = analyze_instance
    def __reshape_contents(self, financial_statement):
        df = deepcopy(financial_statement)
        def convert_to_float(value):
            if value == '--': return value
            try: return float(value)
            except ValueError: return value
        df = df.map(convert_to_float)
        return df.reset_index(drop=False)
    def _CommonSize(self, financial_statement):
        valid_statements = {
            "Income Statement": ["I","IS","Income","Income_Statement","Income Statement"],
            "Balance Sheet": ["Balance Sheet","B","BS","Balance_Sheet"],
            "Cash Flow Statement": ["Cash Flow Statement","Cash_Flow_Statement","C","CF","Cash Flow","Cash_Flow","Cash"],
        }
        financial_statement = IterDict.key_from_mapping(financial_statement, valid_statements, invert=False)
        if financial_statement == 'Income Statement':
            income_statement = deepcopy(self.parent.income_statement)
            if income_statement is not None and not income_statement.empty:
                df = self.__reshape_contents(income_statement)
                for col in list(df.columns[1:]):
                    total_revenue = df.loc[df[df.columns[0]] == 'Total Revenue', col].values[0]
                    if total_revenue == '--' or not isinstance(total_revenue, (int, float)): continue
                    df[col + ' (%)'] = df[col].apply(lambda x: (x/total_revenue)*100 if isinstance(x,(int,float)) else x)
                df.set_index(df.columns[0], inplace=True); return df.fillna('')
        if financial_statement == 'Balance Sheet':
            balance_sheet = deepcopy(self.parent.balance_sheet)
            if balance_sheet is not None and not balance_sheet.empty:
                df = self.__reshape_contents(balance_sheet)
                for col in list(df.columns[1:]):
                    total_assets = df.loc[df[df.columns[0]] == 'Total Assets', col].values[0]
                    if total_assets == '--' or not isinstance(total_assets, (int, float)): continue
                    df[col + ' (%)'] = df[col].apply(lambda x: (x/total_assets)*100 if isinstance(x,(int,float)) else x)
                df.set_index(df.columns[0], inplace=True); return df.fillna('')
        if financial_statement == 'Cash Flow Statement':
            cash_flow_statement = deepcopy(self.parent.cash_flow_statement)
            if cash_flow_statement is not None and not cash_flow_statement.empty:
                df = self.__reshape_contents(cash_flow_statement)
                for col in list(df.columns[1:]):
                    net_income = df.loc[df[df.columns[0]] == 'Net Income', col].values[0]
                    if net_income == '--' or not isinstance(net_income, (int, float)): continue
                    df[col + ' (%)'] = df[col].apply(lambda x: (x/net_income)*100 if isinstance(x,(int,float)) else x)
                df.set_index(df.columns[0], inplace=True); return df.fillna('')
               
def __dir__():
    return __all__
