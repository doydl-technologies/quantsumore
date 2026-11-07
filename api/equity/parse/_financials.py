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


from ....date_parser import dtparse
from ...shape_tools import is_valid_dataframe
from ....strata_utils import IterDict
from ....exceptions import (
    FinancialStatementUnavailableError,
)
from ....statement_types.types import (
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
)
from ....markup import idextract


__all__ = ['statements']





"""
Expected Input: Financial Statement API Response

The `statements` class expects as input the parsed JSON response from a financial statement endpoint,
returning the full suite of annual or quarterly financial data for a given security.

Example Input Structure:
[
  {
    "<string-key>": {  # Usually a URL-encoded path or endpoint signature, e.g. "...+NVDA/financials?frequency=1"
      "response": {
        "data": {
          "symbol": str,    # Security symbol, e.g. "NVDA"
          "tabs": {
            "incomeStatementTable": str,
            "balanceSheetTable": str,
            "cashFlowTable": str,
            "financialRatiosTable": str
          },
          "incomeStatementTable": {
            "asOf": str or null,
            "headers": dict,       # Period labels, e.g. {value1: "Period Ending:", value2: "1/26/2025", ...}
            "rows": list           # Each row is a dict of value1: row label, value2-valueN: period values (strings)
          },
          "balanceSheetTable": {
            "asOf": str or null,
            "headers": dict,       # Same structure as above
            "rows": list           # Each row is a dict of value1: row label, value2-valueN: period values (strings)
          },
          "cashFlowTable": {
            "asOf": str or null,
            "headers": dict,       # Same structure as above
            "rows": list           # Each row is a dict of value1: row label, value2-valueN: period values (strings)
          },
          "financialRatiosTable": {
            "asOf": str or null,
            "headers": dict,       # Same structure as above
            "rows": list           # Each row is a dict of value1: row label, value2-valueN: period values (strings)
          }
        },
        "message": str or null,    # May provide context or note missing data
        "status": {
          "rCode": int,            # e.g. 200 (success)
          "bCodeMessage": str or null,
          "developerMessage": str or null
        }
      }
    }
  }
]

Period/Frequency Handling:
• The API can return both **annual** and **quarterly** financials.
    • Annual Example: headers key "Period Ending:" with dates like "1/26/2025", "1/28/2024", etc.
    • Quarterly Example: headers key "Quarterly Ending:" with appropriate dates.
• The "frequency" query parameter controls this: `frequency=1` for annual, `frequency=2` for quarterly.
• Structure remains consistent between frequencies: only the header labels and dates change.

Table Structure & Notes:
• All four major financial tables are present:
    • **Income Statement**
    • **Balance Sheet**
    • **Cash Flow**
    • **Financial Ratios**
• Each table contains:
    • A headers dict for periods (always value1: row label, value2+: period dates)
    • A list of rows, where each row is a dict: value1 (metric label), value2-valueN (period values)
    • Data values are strings, sometimes with currency symbols, percent signs, "--" for missing values, or empty.
    • Some rows are purely categorical (e.g., "Operating Expenses") and will have empty values.

Batch/Multiple Instruments:
	• Top-level list supports batch results for multiple securities.
	• Each "<string-key>" is usually a unique request signature or URL, not just a ticker.

Defensive Parsing Recommendations:
	• Always check for missing or empty fields (e.g., "--", "", null).
	• Table structure is consistent, but some metrics or periods may be missing for certain securities or timeframes.
	• All numbers are returned as **strings**—parse/cast as needed for numerical operations.
	• Additional context or error info may be provided in the `message` or `status` fields.

Summary:
	• This structure provides the **complete set of financial statements and ratios** for a security, either annual or quarterly.
	• Always reference the headers dict to determine period dates and labels before processing rows.
	• Designed for robust tabular rendering, comparison, and analysis.
"""
class statements:
    # Map provider table keys to statement types and destination attributes.
    _TABLE_MAP = {
        "incomeStatementTable": (IncomeStatement, "income_statement"),
        "balanceSheetTable":  (BalanceSheet,  "balance_sheet"),
        "cashFlowTable":      (CashFlowStatement, "cash_flow_statement"),
    }

    def __init__(self, json_content):
        self.ticker = ""
        self.error_messages = []
        self.error = True
        self._raw = IterDict.isNested(json_content)

        for _, attr in self._TABLE_MAP.values():
            setattr(self, attr, None)

        self._validate_and_filter()
        self._report_errors()
        if not self.error:
            self._parse_all()

    def _validate_and_filter(self):
        """
        Check rCode, presence of tables, collect any error messages,
        and filter out failing entries from self._raw.
        """
        valid_entries = []
        for entry in self._raw:
            url, info = next(iter(entry.items()))
            status = info["response"]["status"]["rCode"]
            data   = info["response"].get("data", {})
            ok = (
                status == 200
                and any(data.get(tbl) for tbl in self._TABLE_MAP)
            )

            if not ok:
                ticker = idextract.extract(url, idextract.SYMBOL)
                msg = (
                    IterDict.find(info["response"], "message")
                    or IterDict.find(info["response"], "errorMessage")
                    or "Financial statement data could not be found."
                ).rstrip(".") + "."
                self.error_messages.append((ticker, msg))
            else:
                valid_entries.append(entry)

        self.error = len(valid_entries) == 0
        self._raw = valid_entries

    def _report_errors(self):
        for ticker, msg in self.error_messages:
            print(f"{ticker}: {msg}")

    def _parse_all(self):
        entry = self._raw[0]
        data  = next(iter(entry.values()))["response"]["data"]
        self.ticker = data.get("symbol", "") or self.ticker

        for key, (cls, attr) in self._TABLE_MAP.items():
            table = data.get(key)
            if table:
                df = self._parse_table(table["headers"], table["rows"], cls)
                setattr(self, attr, df)

    def _parse_table(self, headers, rows, df_class):
        """
        Build a FinancialStatement subclass from raw headers+rows.
        """
        valid_keys = {k: v for k, v in headers.items() if v}
        drop_keys  = set(headers) - set(valid_keys)
        for r in rows:
            for k in drop_keys:
                r.pop(k, None)

        df = pd.DataFrame.from_records(
            data=rows,
            columns=sorted(valid_keys),
        ).rename(columns=valid_keys)

        date_cols = list(df.columns[1:])
        parsed_strs = [
            dtparse.parse(date, to_format="%Y-%m-%d") for date in date_cols
        ]
        df.columns = [df.columns[0]] + parsed_strs
        sorted_dates = sorted(parsed_strs, reverse=True)
        df = df[[df.columns[0]] + sorted_dates]

        def _to_float(x):
            if isinstance(x, str) and x not in ("", "--"):
                return float(x.replace("$","").replace(",",""))
            return x

        for col in sorted_dates:
            df[col] = df[col].map(_to_float).fillna("")

        df = df.set_index(df.columns[0])
        df.__class__ = df_class
        return df

    @property
    def IncomeStatement(self):
        if not is_valid_dataframe(self.income_statement):
            raise FinancialStatementUnavailableError("Income Statement unavailable.")
        return self.income_statement

    @property
    def BalanceSheet(self):
        if not is_valid_dataframe(self.balance_sheet):
            raise FinancialStatementUnavailableError("Balance Sheet unavailable.")
        return self.balance_sheet

    @property
    def CashFlowStatement(self):
        if not is_valid_dataframe(self.cash_flow_statement):
            raise FinancialStatementUnavailableError("Cash Flow Statement unavailable.")
        return self.cash_flow_statement

    def __dir__(self):
        return ["IncomeStatement", "BalanceSheet", "CashFlowStatement"]

def __dir__():
    return __all__
