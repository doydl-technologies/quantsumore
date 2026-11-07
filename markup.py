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

import html as std_html
import re
from urllib.parse import parse_qs, urlsplit



__all__ = [
    'url_encode_decode',
    'HTMLclean',
    'idextract',    
]




class HTMLCleaner:
    def __init__(self):
        self.html_comment_pattern = re.compile(r'<!--.*?-->', flags=re.DOTALL)
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U0001F1E0-\U0001F1FF"  # Flags
            "]+", flags=re.UNICODE
        )
        self.newline_tab_pattern = re.compile(r'\\[ntr]|[\n\t\r]')
        self.space_pattern = re.compile(r'\s+')

    def remove_comments(self, html):
        return self.html_comment_pattern.sub('', html)

    def remove_emojis(self, text):
        return self.emoji_pattern.sub('', text)

    def decode(self, html):
        text = self.newline_tab_pattern.sub('', html)
        text = self.space_pattern.sub(' ', text).strip()
        decoded_text = std_html.unescape(text)
        return decoded_text
       
    def __dir__(self):
        return ['remove_comments','remove_emojis', 'decode']


class URLEncoderDecoder:
    def __init__(self):
        self.encoding_dict = {
            "%20": " ",   "%21": "!",   "%22": "\"",  "%23": "#",   "%24": "$",
            "%25": "%",   "%26": "&",   "%27": "'",   "%28": "(",   "%29": ")",
            "%2A": "*",   "%2B": "+",   "%2C": ",",   "%2D": "-",   "%2E": ".",
            "%2F": "/",   "%3A": ":",   "%3B": ";",   "%3C": "<",   "%3D": "=",
            "%3E": ">",   "%3F": "?",   "%40": "@",   "%5B": "[",   "%5C": "\\",
            "%5D": "]",   "%5E": "^",   "%5F": "_",   "%60": "`",   "%7B": "{",
            "%7C": "|",   "%7D": "}",   "%7E": "~"
        }
        self.inverted_encoding_dict = {v: k for k, v in self.encoding_dict.items()}
        
    def is_valid_url(self, url):
        url_pattern = re.compile(
            r'^(https?|ftp):\/\/'  # protocol
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
            r'(?::\d+)?'  # port
            r'(?:\/?|[\/?]\S+)$', re.IGNORECASE) 
        return re.match(url_pattern, url) is not None

    def decode_url(self, encoded_url):
        decoded_url = encoded_url
        for encoded_char, decoded_char in self.encoding_dict.items():
            decoded_url = decoded_url.replace(encoded_char, decoded_char)
        return decoded_url

    def encode_url(self, url, chars_to_encode=None):
        match = re.match(r'^(https?://)', url)
        protocol = match.group(1) if match else ''
        url = url[len(protocol):] 
        encoded_url = protocol 
        for char in url:
            if chars_to_encode is not None and char not in chars_to_encode:
                encoded_url += char 
            elif char in self.inverted_encoding_dict:
                encoded_url += self.inverted_encoding_dict[char]
            else:
                encoded_url += char
        return encoded_url

    def encode_str(self, i, chars_to_encode=None, join_char=","):
        if not isinstance(i, list):
            i = [i]
        if chars_to_encode:
            if not isinstance(chars_to_encode, list):
                chars_to_encode = [chars_to_encode]
        encoded_list = []
        for item in i:
            encoded_item = ""
            for char in item:
                if chars_to_encode is not None and char not in chars_to_encode:
                    encoded_item += char
                elif char in self.inverted_encoding_dict:
                    encoded_item += self.inverted_encoding_dict[char]
                else:
                    encoded_item += char
            encoded_list.append(encoded_item)
        if join_char in self.inverted_encoding_dict and (chars_to_encode is None or join_char in chars_to_encode):
            encoded_join_char = self.inverted_encoding_dict[join_char]
        else:
            encoded_join_char = join_char
        return encoded_join_char.join(encoded_list)
       
       
# Instrument extractors.
class identifier:
    SYMBOL          = 'symbol'
    CURRENCY_PAIR   = 'currency_pair'
    CRYPTO_SLUG     = 'slug'
    CRYPTO_ID       = 'crypto_id'

    def __init__(self):
        self._extractors = {
            self.SYMBOL:        self._extract_symbol,
            self.CURRENCY_PAIR: self._extract_currency_pair,
            self.CRYPTO_SLUG:   self._extract_slug,
            self.CRYPTO_ID:     self._extract_crypto_id,
        }

    def extract(self, url, instrument):
        """
        Extract the code for the given instrument from the URL.

        instrument must be one of:
          - identifier.SYMBOL
          - identifier.CURRENCY_PAIR
          - identifier.CRYPTO_SLUG
          - identifier.CRYPTO_ID

        Returns the extracted string (or int for CRYPTO_ID) or None.
        """
        fn = self._extractors.get(instrument)
        if not fn:
            raise ValueError(f"No extractor for '{instrument}'")
        return fn(url)

    def _unwrap(self, url):
        if isinstance(url, list) and len(url) == 1 and isinstance(url[0], str):
            return url[0]
        return url

    def _extract_symbol(self, url):
        url = self._unwrap(url)
        source_url = url
        # 1) first segment before / ? or &
        seg = re.split(r'[/?&]', source_url, 1)[0]
        if re.fullmatch(r'[A-Z]{1,4}[-.^]?[A-Z]{0,4}', seg):
            return seg.upper()
        # 2) /stocks/FOO/...
        m = re.search(r'/stocks/([A-Z]{1,4}[-.^]?[A-Z]{0,4})(?=[/?&]|$)', source_url)
        if m: return m.group(1).upper()
        # 3) ?symbols=FOO or &symbols=FOO
        m = re.search(r'[?&]symbols=([A-Z]{1,4}[-.^]?[A-Z]{0,4})(?=[/?&]|$)', source_url)
        if m: return m.group(1).upper()
        # 4) screener f=s-is-%2524FOO
        m = re.search(r'f=s-is-%2524([A-Z]{1,4}[-.^]?[A-Z]{0,4})(?=[&]|$)', source_url)
        if m: return m.group(1).upper()
        # 5) generic catch‑all
        m = re.search(r'(?:/|[?&]|symbols=)([A-Z]{1,4}[-.^]?[A-Z]{0,4})(?=[/?&]|$)', source_url)
        return m.group(1).upper() if m else None

    def _extract_slug(self, url):
        url = self._unwrap(url)
        m = re.search(r'slug=([^&]+)', url)
        return m.group(1) if m else None

    def _extract_crypto_id(self, url):
        url = self._unwrap(url)
        m = re.search(r'id=(\d+)', url)
        return int(m.group(1)) if m else None

    def _extract_currency_pair(self, url):
        url = self._unwrap(url)
        source_url = url
        # 1) before any / or ?
        seg = re.split(r'[/?]', source_url, 1)[0]
        if re.fullmatch(r'[A-Za-z]{6}', seg):
            return seg.upper()
        # 2) ?ratepair=EURUSD
        qs = urlsplit(source_url).query or source_url.lstrip('?')
        params = parse_qs(qs)
        if 'ratepair' in params and params['ratepair']:
            pair = params['ratepair'][0]
            if re.fullmatch(r'[A-Za-z]{6}', pair):
                return pair.upper()
        # 3) /quotes/%5EFOO
        m = re.search(r'/(?:quotes/%5E|quote/)([A-Za-z]{6})(?=/|$)', source_url)
        return m.group(1).upper() if m else None

    def __dir__(self):
        return ['extract']       
       
url_encode_decode = URLEncoderDecoder()
HTMLclean = HTMLCleaner()
idextract = identifier()

def __dir__():
    return __all__
