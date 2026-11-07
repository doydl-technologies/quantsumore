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


from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from tests.runtime import prepare_runtime


class FinancialAnalysisTests(unittest.TestCase):
    def setUp(self):
        from quantsumore.analysis.fundamental import fAnalyze
        columns = ["2025-12-31", "2024-12-31"]
        income = pd.DataFrame([[500, 400], [10, 8], [100, 80]],
                              index=["Total Revenue", "Research and Development", "Net Income"],
                              columns=columns)
        balance = pd.DataFrame([[100, 250], [50, 100], [500, 600], [10, 15]],
                               index=["Total Current Assets", "Total Current Liabilities",
                                      "Total Assets", "Goodwill"], columns=columns)
        cash = pd.DataFrame([[100, 80], [10, 8], [150, 100], [50, 20]],
                            index=["Net Income", "Depreciation", "Net Cash Flow-Operating",
                                   "Capital Expenditures"], columns=columns)
        class Engine:
            calls = 0
            def Process(self, ticker, period):
                self.calls += 1
                return {"financial_statements": [(income, balance, cash)], "dividend": []}
        self.engine = Engine()
        self.analyze = fAnalyze(self.engine)
        self.analyze("FIXTURE", "Annual")

    def test_ratio_cache_and_statement_copy(self):
        self.assertEqual(self.analyze.current_ratio().tolist(), [2.0, 2.5])
        external = self.analyze.balance_sheet
        external.iloc[0, 0] = -1
        self.assertEqual(self.analyze.current_ratio().tolist(), [2.0, 2.5])
        self.analyze("FIXTURE", "Annual")
        self.assertEqual(self.engine.calls, 1)

    def test_method_discovery_without_dividends(self):
        for data, report in ((None, None), (pd.DataFrame({"amount": [1]}), None),
                             (None, pd.DataFrame({"yield": [0.02]}))):
            with self.subTest(data_missing=data is None, report_missing=report is None):
                self.analyze.dividend_data = data
                self.analyze.dividend_report = report
                names = dir(self.analyze)
                self.assertIn("current_ratio", names)
                self.assertIn("CommonSize", names)
                self.assertNotIn("dividend_yield", names)
                self.assertEqual(self.analyze.current_ratio().tolist(), [2.0, 2.5])

    def test_method_discovery_with_dividends(self):
        self.analyze.dividend_data = pd.DataFrame({"amount": [1]})
        self.analyze.dividend_report = pd.DataFrame({"yield": [0.02]})
        names = dir(self.analyze)
        self.assertIn("current_ratio", names)
        for name in ("dividend_data", "dividend_report", "dividend_yield",
                     "ex_dividend_date", "annual_dividend"):
            self.assertIn(name, names)

    def test_method_discovery_before_statements_are_loaded(self):
        from quantsumore.analysis.fundamental import fAnalyze
        self.assertEqual(dir(fAnalyze(self.engine)), [])

    def test_common_size_and_vertical_analysis_for_all_statements(self):
        cases = (
            ("I", "Total Revenue", "Total Revenue"),
            ("B", "Total Assets", "Total Assets"),
            ("C", "Net Income", "Net Cash Flow-Operating"),
        )
        for alias, common_base, vertical_base in cases:
            with self.subTest(statement=alias):
                common = self.analyze.CommonSize(alias)
                vertical = self.analyze.VerticalAnalysis(alias)
                for date in ("2025-12-31", "2024-12-31"):
                    self.assertEqual(common.loc[common_base, date + " (%)"], 100.0)
                    self.assertEqual(vertical.loc[vertical_base, date], "100.00%")

    def test_missing_markers_survive_elementwise_formatting(self):
        income = self.analyze.income_statement.astype(object)
        income.loc["Research and Development", "2025-12-31"] = "--"
        self.analyze.income_statement = income
        self.assertEqual(self.analyze.CommonSize("I").loc["Research and Development", "2025-12-31 (%)"], "--")
        self.assertEqual(self.analyze.VerticalAnalysis("I").loc["Research and Development", "2025-12-31"], "--")

    def test_excel_export_for_standard_and_common_size_statements(self):
        from openpyxl import load_workbook
        with TemporaryDirectory() as directory:
            for common_size in (False, True):
                with self.subTest(common_size=common_size):
                    path = Path(directory) / ("common.xlsx" if common_size else "standard.xlsx")
                    self.analyze.writeStatement(str(path), include_common_size=common_size)
                    workbook = load_workbook(path)
                    try:
                        self.assertEqual(set(workbook.sheetnames), {"Income Statement", "Balance Sheet", "Cash Flow Statement"})
                        rows = list(workbook["Income Statement"].values)
                        revenue = next(row for row in rows if "Total Revenue" in row)
                        self.assertIn(500, revenue)
                    finally:
                        workbook.close()
