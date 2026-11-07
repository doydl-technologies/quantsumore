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

from datetime import date, timedelta
import json
import os
import subprocess
import sys
import unittest

from tests.runtime import prepare_runtime


CHECKS = {
    'equity_quote': 'from quantsumore.api import equity; r=equity.Latest(ticker="AAPL"); assert r["Price"] > 0 and r["Currency"] and r["quoteTimeUTC"]',
    'equity_profile': 'from quantsumore.api import equity; r=equity.Profile.bio(ticker="AAPL"); assert r is not None and len(r) > 0',
    'equity_history': 'from datetime import date,timedelta; from quantsumore.api import equity; r=equity.Historical(ticker="AAPL",start=str(date.today()-timedelta(days=60)),end=str(date.today())); assert r is not None and len(r) > 0 and "Close" in r.columns',
    'forex_daily': 'from quantsumore.api import forex; r=forex.CurrencyConversion(currency_pair="EURUSD",conversion_amount=100); assert r["conversion_rate_EUR_to_USD"] > 0 and r["last_updated"]',
    'crypto_markets': 'from quantsumore.api import crypto; r=crypto.Latest(slug="bitcoin",limit=1); assert r is not None and not r.empty and r["price"].iloc[0] > 0',
    'treasury_yield': 'from datetime import date; from quantsumore.api import treasury; r=treasury.Yield(period=date.today().year,full_table=True); assert r is not None and not r.empty',
    'treasury_bills': 'from datetime import date; from quantsumore.api import treasury; r=treasury.TBill(period=date.today().year,full_table=True); assert r is not None and not r.empty',
    'cpi_live': 'from quantsumore.api.cpi.ConsumerPriceIndexAPI import engine; c=engine.CPI_U.InflationAdjustment; assert c.min_year == 1913 and c.data.attrs["source"] == "FRED" and c.data.attrs["latest_observation"]; assert c.select(100, 2020, int(c.max_year), c.current_month) > 0',

}


def check_provider(name):
    program = CHECKS[name] + '; print("PROVIDER_CHECK_PASSED")'
    result = subprocess.run([sys.executable, '-I', '-c', program], capture_output=True,
                            text=True, timeout=35, env=os.environ.copy())
    if result.returncode or 'PROVIDER_CHECK_PASSED' not in result.stdout:
        raise AssertionError((result.stderr or result.stdout)[-2000:])


@unittest.skipUnless(os.environ.get('QUANTSUMORE_LIVE_TESTS') == '1', 'External provider checks are opt-in.')
class LiveProviderTests(unittest.TestCase):
    def test_current_providers(self):
        for name in CHECKS:
            with self.subTest(provider=name):
                check_provider(name)
