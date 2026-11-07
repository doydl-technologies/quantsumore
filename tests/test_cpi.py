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

import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import requests

from tests.runtime import prepare_runtime


class CPIRetrievalTests(unittest.TestCase):
    def fetch(self, text, **kwargs):
        from quantsumore.api.cpi.parse._inflation import CUUR0000AA0
        response = Mock(text=text)
        with patch('requests.get', return_value=response) as request:
            data = CUUR0000AA0.Data(**kwargs).all_items_index()
        return data, request, response

    def test_direct_csv_request_is_bounded_and_does_not_need_html(self):
        from quantsumore.api.cpi.ConsumerPriceIndexAPI import APIClient
        adapter = Mock()
        response = Mock(text='observation_date,CPIAUCNS\n2024-01-01,100\n2024-10-01,120\n')
        with patch('requests.get', return_value=response) as request:
            data = APIClient(adapter)._all_urban()
        request.assert_called_once()
        adapter.make.assert_not_called()
        self.assertEqual(request.call_args.kwargs['timeout'], (3.05, 10))
        query = parse_qs(urlparse(request.call_args.args[0]).query)
        self.assertEqual(query, {'id': ['CPIAUCNS'], 'cosd': ['1913-01-01']})
        self.assertEqual(data.attrs['latest_observation'], '2024-10-01')
        self.assertEqual(data.attrs['source_series_id'], 'CPIAUCNS')
        self.assertEqual(list(data.columns), ['series_id', 'year', 'period', 'value'])
        self.assertEqual(data.loc[data['period'] == 'Average', 'value'].item(), 110.0)
        response.raise_for_status.assert_called_once()

    def test_legacy_date_column_missing_values_and_requested_series(self):
        text = 'DATE,CPIAUCSL\n2024-01-01,100\n2024-02-01,.\n2024-03-01,120\n'
        data, request, _ = self.fetch(text, series_id='cpiaucsl')
        self.assertEqual(data['period'].tolist(), ['January', 'March', 'Average'])
        self.assertEqual(data['value'].tolist(), [100.0, 120.0, 110.0])
        self.assertEqual(data.attrs['source_series_id'], 'CPIAUCSL')
        self.assertIn('id=CPIAUCSL', request.call_args.args[0])

    def test_date_bounds_apply_to_observations_and_annual_average(self):
        data, request, _ = self.fetch(
            'DATE,CPIAUCNS\n2023-12-01,80\n2024-01-01,100\n2024-02-01,120\n2024-03-01,140\n',
            start_date='2024-01-01', end_date='2024-02-01'
        )
        self.assertEqual(data['period'].tolist(), ['January', 'February', 'Average'])
        self.assertEqual(data['value'].tolist(), [100.0, 120.0, 110.0])
        self.assertEqual(parse_qs(urlparse(request.call_args.args[0]).query)['coed'], ['2024-02-01'])

    def test_timeout_and_http_failures_keep_their_cause(self):
        from quantsumore.api.cpi.ConsumerPriceIndexAPI import engine
        from quantsumore.exceptions import CPIDataUnavailableError
        timeout = requests.Timeout('provider stalled')
        with patch('requests.get', side_effect=timeout):
            with self.assertRaisesRegex(CPIDataUnavailableError, 'provider stalled') as caught:
                engine._all_urban()
        self.assertIs(caught.exception.__cause__, timeout)
        error = requests.HTTPError('503 Service Unavailable')
        response = Mock()
        response.raise_for_status.side_effect = error
        with patch('requests.get', return_value=response):
            with self.assertRaisesRegex(CPIDataUnavailableError, '503') as caught:
                engine._all_urban()
        self.assertIs(caught.exception.__cause__, error)

    def test_invalid_payloads_raise_clear_errors_instead_of_empty_data(self):
        from quantsumore.exceptions import CPIDataUnavailableError
        payloads = (
            '', '<html>Access denied</html>', 'DATE,OTHER\n2024-01-01,100\n',
            'DATE,CPIAUCNS\n2024-01-01,.\n', 'DATE,CPIAUCNS\ninvalid,100\n',
            'DATE,CPIAUCNS\n2024-01-01,0\n', 'DATE,CPIAUCNS\n2024-01-01,-1\n',
            'DATE,CPIAUCNS\n2024-01-01,inf\n',
            'DATE,CPIAUCNS\n2024-01-01,100\n2024-01-02,101\n',
        )
        for text in payloads:
            with self.subTest(payload=text):
                with self.assertRaises(CPIDataUnavailableError) as caught:
                    self.fetch(text)
                self.assertIsNotNone(caught.exception.__cause__)

    def test_latest_month_uses_calendar_order_and_latest_published_data(self):
        from quantsumore.api.cpi.ConsumerPriceIndexAPI import _InflationAdjustment
        data, _, _ = self.fetch(
            'DATE,CPIAUCNS\n2023-09-01,100\n2023-10-01,125\n'
            '2024-09-01,200\n2024-10-01,250\n'
        )
        calculator = _InflationAdjustment(data)
        self.assertEqual(calculator.current_month, 'October')
        self.assertEqual(calculator.select(100, 2023, 2024, calculator.current_month), 200.0)
        data, _, _ = self.fetch('DATE,CPIAUCNS\n2024-12-01,300\n2024-09-01,200\n')
        self.assertEqual(_InflationAdjustment(data).current_month, 'December')

    def test_year_by_year_uses_latest_calendar_month(self):
        from quantsumore.api.cpi.ConsumerPriceIndexAPI import _InflationAdjustment
        data, _, _ = self.fetch(
            'DATE,CPIAUCNS\n2023-09-01,90\n2023-10-01,100\n'
            '2024-09-01,200\n2024-10-01,250\n'
        )
        result = _InflationAdjustment(data).year_by_year(100, 1)
        self.assertEqual(result[2023], 250.0)

    def test_default_exception_message_remains_available(self):
        from quantsumore.exceptions import CPIDataUnavailableError
        self.assertIn('CPI data is currently unavailable', str(CPIDataUnavailableError()))
