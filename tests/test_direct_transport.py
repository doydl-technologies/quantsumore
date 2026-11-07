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

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import inspect
import json
from pathlib import Path
import re
import threading
import unittest
from unittest.mock import patch

from tests.runtime import prepare_runtime


class Provider(BaseHTTPRequestHandler):
    requests = []

    def do_GET(self):
        self.requests.append((self.path, dict(self.headers)))
        status = 503 if self.path == '/failure' else 200
        text = self.path == '/text'
        body = b'provider text' if text else json.dumps({'value': 42}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain' if text else 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


class DirectTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from quantsumore._http.connection import Connection
        cls.connection = Connection
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.connection.close()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        Provider.requests.clear()

    def test_direct_request_preserves_parser_shape_without_auth_headers(self):
        target = self.base + '/quote?symbols=AAPL'
        result = self.connection.Request((self.base, '/quote?symbols=AAPL'), params={'range': '1d'})
        self.assertEqual(result, [{target: {'response': {'value': 42}}}])
        self.assertEqual(len(Provider.requests), 1)
        path, headers = Provider.requests[0]
        self.assertEqual(path, '/quote?symbols=AAPL&range=1d')
        self.assertNotIn('X-API-Key', headers)
        self.assertNotIn('Authorization', headers)

    def test_full_urls_and_text_responses(self):
        self.assertEqual(self.connection.Request(self.base + '/text', return_url=False), {'response': 'provider text'})

    def test_user_agent_tracks_package_version_for_new_sessions(self):
        from quantsumore import __version__
        from quantsumore._http import connection
        for package_version in (__version__, "9.8.7b6"):
            with self.subTest(package_version=package_version):
                self.connection.close()
                with patch.object(connection, "__version__", package_version, create=True):
                    try:
                        self.connection.Request(self.base + "/json", return_url=False)
                        self.assertEqual(Provider.requests[-1][1]["User-Agent"],
                                         f"quantsumore/{package_version}")
                    finally:
                        self.connection.close()

    def test_provider_errors_keep_their_http_status(self):
        from quantsumore.exceptions import APIRequestError
        with self.assertRaises(APIRequestError) as error:
            self.connection.Request(self.base + '/failure')
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(len(Provider.requests), 1)

    def test_credentials_are_not_loaded_from_netrc(self):
        self.connection.close()
        with patch('requests.sessions.get_netrc_auth', side_effect=AssertionError('Credential lookup attempted')):
            self.assertEqual(self.connection.Request(self.base + '/json', return_url=False), {'response': {'value': 42}})

    def test_public_clients_have_no_key_parameters_or_exports(self):
        import quantsumore.api as api
        import quantsumore.analysis as analysis
        from quantsumore._http import connection
        self.assertFalse(hasattr(api, 'APIKey'))
        self.assertFalse(hasattr(analysis, 'APIKey'))
        self.assertFalse(hasattr(connection, 'APIKey'))
        self.assertFalse(hasattr(self.connection, 'api_key'))
        self.assertFalse(hasattr(self.connection, '_anyquota'))
        methods = [api.equity.Latest, api.equity.Historical, api.equity.Profile.bio,
                   api.forex.Historical, api.forex.CurrencyConversion, api.forex.Interbank,
                   api.crypto.Latest, api.crypto.Historical,
                   analysis.fAnalysis.__call__, analysis.fAnalysis.get_financial_data]
        for method in methods:
            with self.subTest(method=method.__qualname__):
                self.assertNotIn('api_key', inspect.signature(method).parameters)

    def test_abandoned_service_and_key_storage_are_absent_from_source(self):
        import quantsumore
        source = Path(quantsumore.__file__).resolve().parent
        self.assertFalse((source / '__relaytable__.py').exists())
        tokens = re.compile(r'APIKey|api_key|X-API-Key|QUANTSUMORE_API_KEY|api\.doydl\.studio|_anyquota|__QUOTA_UPLINK__')
        for path in source.rglob('*.py'):
            if any(part in ('.git', 'build', '__pycache__') for part in path.parts):
                continue
            self.assertIsNone(tokens.search(path.read_text(encoding='utf-8')), str(path))

    def test_provider_routes_are_plain_urls_with_single_query_parameters(self):
        from urllib.parse import parse_qs, urlsplit
        from quantsumore.api.prep import equity_adapter, crypto_adapter, forex_adapter
        cases = [
            (equity_adapter.make('latest', ticker='AAPL'), 'query1.finance.yahoo.com', 'symbols'),
            (crypto_adapter.make('live', slug='bitcoin'), 'api.coinmarketcap.com', 'slug'),
            (forex_adapter.make('convert', currency_pair='EURUSD'), 'www.mtfxgroup.com', 'ratepair'),
        ]
        for (base, endpoint), host, parameter in cases:
            parsed = urlsplit(base + endpoint)
            self.assertEqual(parsed.hostname, host)
            self.assertEqual(len(parse_qs(parsed.query)[parameter]), 1)
            self.assertNotIn('gAAAA', base)

    def test_financial_pair_uses_two_direct_gets_and_native_urls(self):
        from quantsumore.analysis._fa import fetch_financials_dividends_pair, get_process
        result = fetch_financials_dividends_pair([(self.base, '/financials'), (self.base, '/dividends')])
        self.assertEqual([path for path, _ in Provider.requests], ['/financials', '/dividends'])
        categorized = get_process()._categorize_content(result)
        self.assertEqual(len(categorized['financial_statements']), 1)
        self.assertEqual(len(categorized['dividend']), 1)

    def test_native_fx_payload_uses_latest_observation_and_preserves_its_date(self):
        from quantsumore.api.forex.parse._rates import conversion
        payload = [{'https://www.mtfxgroup.com/api/rates/frequencyRateCustom/?ratepair=EURUSD': {
            'response': {'d': [
                {'RatePair': 'EURUSD', 'RatePairValue': 1.25, 'LastUpdate': 'Mon, 26 Oct 2026 00: 00:00'},
                {'RatePair': 'EURUSD', 'RatePairValue': 1.2, 'LastUpdate': 'Tue, 27 Oct 2026 00: 00:00'},
            ]}
        }}]
        result = conversion(payload, conversion_amount=100).DATA()
        self.assertEqual(result['conversion_rate_EUR_to_USD'], 1.2)
        self.assertEqual(result['amount_converted_from_EUR']['converted_amount_to_USD'], 120)
        self.assertEqual(result['last_updated'], 'Tue, 27 Oct 2026 00: 00:00')


if __name__ == '__main__':
    unittest.main(verbosity=2)
