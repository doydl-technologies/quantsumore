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

import threading
from urllib.parse import urlsplit

from .._version import __version__
from ..exceptions import APIRequestError

__all__ = ['Connection']


class _httpClient:
    _instance = None
    _lock = threading.Lock()
    _destroyed = False

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._destroyed:
                raise RuntimeError('The HTTP client has been closed.')
            if cls._instance is not None:
                raise RuntimeError('Use the exported Connection instance.')
            cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        self.base_url = None
        self.host = None
        self.code = None
        self.content_type = None
        self._session = None

    @classmethod
    def instance(cls):
        if cls._instance is None or cls._destroyed:
            raise RuntimeError('The HTTP client is unavailable.')
        return cls._instance

    def _get_session(self):
        if self._destroyed:
            raise RuntimeError('The HTTP client has been closed.')
        if self._session is None:
            import requests
            self._session = requests.Session()
            self._session.trust_env = False
            self._session.headers.update({
                'User-Agent': f'quantsumore/{__version__}',
                'Accept': 'application/json, text/plain, text/html;q=0.9, */*;q=0.8',
            })
        return self._session

    def update_base_url(self, url):
        if isinstance(url, (tuple, list)):
            if len(url) != 2:
                raise ValueError('Provide a URL or a (base, endpoint) pair.')
            base, endpoint = url
            if isinstance(base, bytes):
                base = base.decode('utf-8')
            if not isinstance(base, str) or not isinstance(endpoint, str):
                raise ValueError('The base URL and endpoint must be strings.')
            url = base + endpoint
        if not isinstance(url, str):
            raise ValueError('Provide a URL or a (base, endpoint) pair.')
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use a complete HTTP or HTTPS provider URL.')
        self.base_url = url
        self.host = parsed.hostname
        return url

    def Request(self, url, params=None, return_url=True, timeout=15):
        """Fetch a provider directly and retain the response shape used by the parsers."""
        import requests
        target = self.update_base_url(url)
        try:
            response = self._get_session().get(target, params=params, timeout=timeout)
            self.code = response.status_code
            self.content_type = response.headers.get('Content-Type', '')
            response.raise_for_status()
            body = response.json() if 'json' in self.content_type.lower() else response.text
            wrapped = {'response': body}
            return [{target: wrapped}] if return_url else wrapped
        except (requests.RequestException, ValueError) as error:
            raise APIRequestError(error) from error

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    @classmethod
    def destroy_instance(cls):
        if cls._instance is not None:
            cls._instance.close()
        cls._instance = None
        cls._destroyed = True


Connection = _httpClient()


def __dir__():
    return __all__
