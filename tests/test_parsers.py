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

from datetime import datetime, timezone
import unittest
from unittest.mock import Mock, patch
from tests.runtime import prepare_runtime


class QuoteParserTests(unittest.TestCase):
    def test_statistics_requests_the_supplied_ticker(self):
        from quantsumore.api.equity.EquityAPI import APIClient
        for ticker in ("AAPL", "MSFT", "NVDA"):
            with self.subTest(ticker=ticker):
                adapter = Mock()
                adapter.make.return_value = (b"https://provider.example", f"/{ticker}/stats")
                parser = Mock()
                parser.DATA.return_value = {"ticker": ticker}
                with patch("quantsumore.api.equity.EquityAPI.Connection.Request", return_value={"payload": ticker}) as request, \
                     patch("quantsumore.api.equity.EquityAPI.quote_statistics", return_value=parser) as statistics:
                    self.assertEqual(APIClient(adapter).Stats(ticker), {"ticker": ticker})
                adapter.make.assert_called_once_with(query="stats", ticker=ticker)
                request.assert_called_once_with(url=("https://provider.example", f"/{ticker}/stats"),
                                                params=None, return_url=True)
                statistics.assert_called_once_with({"payload": ticker})

    def test_package_quote_exposes_provider_currency_and_utc_timestamp(self):
        from quantsumore.api.equity.parse._intra import latest
        timestamp = 1700000000
        payload = [{'https://provider.example/quote': {'response': {'spark': {'result': [
            {'symbol': 'AAPL', 'response': [{'meta': {'currency': 'USD', 'longName': 'Apple',
              'shortName': 'Apple', 'regularMarketTime': timestamp}, 'timestamp': [timestamp],
              'indicators': {'quote': [{'close': [125.5]}]}}]}
        ]}}}}]
        result = latest(payload).DATA()
        self.assertEqual(result['Currency'], 'USD')
        self.assertEqual(datetime.fromisoformat(result['quoteTimeUTC']), datetime.fromtimestamp(timestamp, timezone.utc))
        self.assertEqual(result['Price'], 125.5)
