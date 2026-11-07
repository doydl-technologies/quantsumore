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

import re

from .market_utils import fxutil, equityquery, CoinQuery
from ..date_parser import dtparse
from ..exceptions import (
    TickerNotFoundError,
    CurrencyPairNotFoundError,
    InvalidCurrencyPairError,
    InvalidSlugTypeError,
    CoinSlugNotFoundError,
    CoinSlugIdMismatchError,
)
from ..strata_utils import IterDict

__all__ = [
    "_normalize_dates",
    "_INTERVAL_TO_MINUTES",
    "_RANGE_TO_DAYS",
    "_enforce_valid_combo",
    "_auto_adjust_interval",
    "_days_from_range",
    "_MAX_POINTS",
    "_validate",
    "_aliasmap",
]



class instrument_validation:
    """Validate ticker symbols, currency pairs and cryptocurrency slugs.

    Stock checks select a standard, Yahoo or Nasdaq mapping from the local
    registry. Currency checks normalize and validate codes against the selected
    currency set. Slug checks use the local cryptocurrency database.
    Successful checks store their result in validated_instrument; invalid
    identifiers raise the corresponding instrument exception.
    """
    def __init__(self): self.validated_instrument = None

    def stock_ticker(self, ticker, search_type="standard"):
        self.validated_instrument = None
        ticker = ticker.strip()
        if search_type == "standard":
            result = equityquery.search_symbol(ticker)
            if not result: raise TickerNotFoundError(f"Could not locate ticker symbol: {ticker}")
        elif search_type == "EquityProviderA":
            result = equityquery.search_yahoo_symbol(ticker)
            if not result: raise TickerNotFoundError(f"Could not locate ticker symbol: {ticker}")
        elif search_type == "EquityProviderD":
            result = equityquery.search_nasdaq_symbol(ticker)
            if not result: raise TickerNotFoundError(f"Could not locate ticker symbol: {ticker}")
        self.validated_instrument = ticker

    def fx_currency(self, ccy_pair, currency_dict_type="major"):
        self.validated_instrument = None
        tokens = fxutil.tokenize(ccy_pair)
        if not tokens: raise InvalidCurrencyPairError("Please enter a valid currency pair as a string or a list of strings.")
        validated = [fxutil.query(t, query_type=currency_dict_type, ret_type="code") for t in tokens if fxutil.query(t, query_type=currency_dict_type, ret_type="code")]
        if len(validated) == len(tokens): self.validated_instrument = validated
        if not (isinstance(self.validated_instrument, list) and all(isinstance(i, str) for i in self.validated_instrument)):
            raise InvalidCurrencyPairError("Invalid currency. Currently, the only currencies accepted are from: " + ", ".join(fxutil.which.major()) + ". Please enter a valid currency.")
        if not self.validated_instrument: raise CurrencyPairNotFoundError("Please enter a valid currency pair.")
        if self.validated_instrument is None: raise CurrencyPairNotFoundError(f"{ccy_pair} is not in the list of accepted currency pairs.")
        self.validated_instrument = fxutil._join_currency(self.validated_instrument)

    def crypto_slug_name(self, slug):
        self.validated_instrument = None
        if not isinstance(slug, str): raise InvalidSlugTypeError("Please enter a valid coin slug and NOT a symbol (must be a string).")
        slug = slug.lower()
        data = CoinQuery.Slug(slug)
        result = IterDict.search_keys_in(data, target_keys=["slug", "id"], value_only=False, first_only=False, return_all=False)
        if result and len(result) == 2:
            def _extract(data, key):
                return IterDict.search_keys(data, target_keys=key, value_only=True, first_only=True, return_all=False, include_key_in_results=False)
            SLUG = _extract(result, "slug")
            ID = _extract(result, "id")
            self.validated_instrument = (SLUG, ID)
        elif result:
            raise CoinSlugIdMismatchError("Id or slug name not found! Check the slug name you entered.")
        else:
            raise CoinSlugNotFoundError("Please enter a valid coin slug and NOT a symbol.")

    def __dir__(self): return ['stock_ticker', 'fx_currency', 'crypto_slug_name', 'validated_instrument']


class _normalizeDate:
    """Normalize date ranges to Unix seconds, UTC Unix seconds or strftime output.

    norm() supports optional start/end clipping.
    """
    def __init__(self): pass

    def norm(self, start_date, end_date=None, future_date_check=False, date_format="unix", clip=None):
        """
        Normalize start/end dates; formats: "unix", "utc_unix", or strftime. Optionally clip ("start"|"end").
        """
        end_date = dtparse.now(utc=True) if not end_date else (dtparse.parse(end_date) if isinstance(end_date, str) else end_date)
        start_date = dtparse.parse(start_date) if isinstance(start_date, str) else start_date
        if start_date > end_date: raise ValueError("Start date must be before or equal to end date.")
        if future_date_check:
            now = dtparse.now(utc=True)
            if start_date > now or end_date > now: raise ValueError("Data not available on requested date. Please try another date.")
        if date_format == "unix":
            start_date = dtparse.unix_timestamp(start_date)
            end_date = dtparse.unix_timestamp(end_date)
        elif date_format == "utc_unix":
            start_date = dtparse.unix_timestamp(start_date, utc=True)
            end_date = dtparse.unix_timestamp(end_date, utc=True)
        else:
            start_date, end_date = start_date.strftime(date_format), end_date.strftime(date_format)
        if clip == "start": return end_date
        if clip == "end": return start_date
        return start_date, end_date


# Equity URL routing.



# Coarsen the interval above this point count to bound response size.
_MAX_POINTS = 100_000

# Aliases for valid interval strings (maps variations to standardized code)
_VALID_INTERVAL_ALIASES = {
    '1m': [
        '1 minute', 'one minute', 'a minute', '1 min',
    ],
    '2m': [
        '2 minutes', 'two minutes', '2 min',
    ],
    '5m': [
        '5 minutes', 'five minutes', '5 min',
    ],
    '15m': [
        '15 minutes', 'fifteen minutes', '15 mins', 'quarter of an hour', '15 min',
    ],
    '30m': [
        '30 minutes', 'thirty minutes', 'half hour', '30 mins', '30 min',
    ],
    '1h': [
        '60 minutes', 'one hour', 'an hour', '1 hour', 'hour', '60 m',
    ],
    '90m': [
        '90 minutes', 'ninety minutes', '1.5 hours', 'an hour and a half',
    ],
    '1d': [
        '1 day', 'one day', 'a day', '24 hours', '24 h',
    ],
    '5d': [
        '5 days', 'five days',
    ],
    '1wk': [
        '1 week', 'one week', 'a week', '7 days', 'week', '7 d',
    ],
    '1mo': [
        '1 month', 'one month', 'a month', '30 days', 'month', '30 d',
    ],
    '3mo': [
        '3 months', 'three months', '90 days', '90 d',
    ]
}

# Aliases for valid range strings (maps variations to standardized code)
_VALID_RANGE_ALIASES = {
    '1d': [
        '24 hours', 'one day', 'a day', '1 day', '24 h', 'day',
    ],
    '5d': [
        '5 days', '120 hours', 'five days', '120 h',
    ],
    '1mo': [
        '1 month', '30 days', '720 hours', 'one month', 'a month', 'monthly',
        '30 d', '720 h',
    ],
    '3mo': [
        '3 months', '90 days', '2160 hours', 'three months', 'quarter',
        '90 d', '2160 h',
    ],
    '6mo': [
        '6 months', '180 days', '4320 hours', 'six months', 'half year', 'half-year',
        '180 d', '4320 h',
    ],
    '1y': [
        '1 year', '12 months', '365 days', '8760 hours', 'one year', 'a year', 'yearly',
        '365 d', '12 mo', '8760 h',
    ],
    '2y': [
        '2 years', '24 months', '730 days', '17520 hours', 'two years',
        '17520 h', '730 d', '24 mo',
    ],
    '5y': [
        '5 years', '60 months', '1825 days', '43800 hours', 'five years',
        '60 mo', '43800 h', '1825 d',
    ],
    '10y': [
        '10 years', '120 months', '3650 days', '87600 hours', 'ten years',
        'a decade', 'decade', '3650 d', '87600 h', '120 mo',
    ],
    'ytd': [
        'ytd', 'year to date', 'year-to-date', 'this year', 'current year',
        'since jan 1', 'jan 1', 'jan 01', 'jan1', 'cy',
    ],
    'max': [
        'max', 'maximum', 'all', 'all history', 'entire history',
        'since inception', 'lifetime', 'inception',
    ]
}

# Maps range name to an approximate number of days for that range
_RANGE_TO_DAYS = {
    "1d":    1,
    "5d":    5,
    "1mo":  30,
    "3mo":  90,
    "6mo": 180,
    "1y":  365,
    "2y":  365*2,
    "5y":  365*5,
    "10y": 365*10,
}

def _days_from_range(rng):
    """
    Return the number of days corresponding to a named range string.
    """
    if rng == "ytd":
        today = dtparse.now(utc=False, as_unix=False, format=None, date_only=True)
        start = dtparse.build(today.year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tz_offset_hours=None, as_date=True)
        return (today - start).days + 1  # Includes every trading day including today (if markets are open and data is up-to-the-minute)
    if rng == "max":
        return float("inf")
    try:
        return _RANGE_TO_DAYS[rng]
    except KeyError:
        raise ValueError(f"Unsupported range '{rng}'. Valid: {_RANGE_TO_DAYS.keys() | {'ytd','max'}}")

# Approximate duration of each interval, in minutes.
_INTERVAL_TO_MINUTES = {
    "1m":   1,
    "2m":   2,
    "5m":   5,
    "15m": 15,
    "30m": 30,
    # Use "1h" as the canonical spelling for a 60-minute interval.
    "90m": 90,
    "1h":   60,
    "1d": 1440,
    "5d": 5 * 1440,
    "1wk": 7 * 1440,
    "1mo": 30 * 1440,
    "3mo": 90 * 1440,
}

# Provider history limits for minute-level intervals.
_MAX_RANGE_FOR_INTERVAL_DAYS = {
    "1m": 7,  # One-minute intervals allow at most seven days of history.
    **{iv: 60 for iv in ["2m","5m","15m","30m","60m","90m","1h"]},  # These intervals allow at most 60 days of history.
}

# List of intervals in order of increasing coarseness (1m -> 3mo)
_ORDERED_INTERVALS = sorted(
    _INTERVAL_TO_MINUTES.items(),
    key=lambda kv: kv[1]
)

def _enforce_valid_combo(rng, iv):
    """
    Raise ValueError if the interval/range combo exceeds the API's allowed history.
    """
    days = _days_from_range(rng)
    cap = _MAX_RANGE_FOR_INTERVAL_DAYS.get(iv, float("inf"))
    if days > cap:
        raise ValueError(
            f"Interval '{iv}' only supports up to {cap} days of history "
            f"(you asked for {days} days)."
        )
        
# Sequence of interval codes, in order of increasing coarseness (e.g., ['1m', '2m', ...])
_INTERVAL_SEQUENCE = [iv for iv, _ in _ORDERED_INTERVALS]



def _auto_adjust_interval(rng, iv):
    """
    If the number of data points exceeds _MAX_POINTS, incrementally increase
    the interval (make it coarser) until the point count is below threshold.
    Raises ValueError if even the coarsest interval exceeds limit.
    """
    days = _days_from_range(rng)
    base_minutes = _INTERVAL_TO_MINUTES[iv]
    raw_points = float("inf") if days == float("inf") else days * 1440 / base_minutes

    if raw_points <= _MAX_POINTS:
        return iv

    idx = _INTERVAL_SEQUENCE.index(iv)
    for next_iv in _INTERVAL_SEQUENCE[idx + 1 :]:
        pts = days * 1440 / _INTERVAL_TO_MINUTES[next_iv]
        if pts <= _MAX_POINTS:
            return next_iv

    # A smaller range is required when even the coarsest interval exceeds the limit.
    max_days = int(_MAX_POINTS * base_minutes / 1440)
    raise ValueError(
        f"Even '{_INTERVAL_SEQUENCE[-1]}' yields more than {_MAX_POINTS:,} points. "
        f"Try a smaller range (≤ {max_days} days)."
    )
    

class AliasMapper:
    """
    Merge one or more named mappings of {canonical_key: synonym or [synonyms]}.
    lookup(s, mapping=None, invert=False, collapse_space=True) will:

      • find s as a key or synonym in the chosen mapping (default is the first one)
      • if collapse_space=True, try "joined ↔ spaced" retries for number+word inputs:
          - "1day" → "1 day"
          - "1 day" → "1day"
      • return the canonical key (default) or the list of synonyms (invert=True)
    """
    def __init__(self, **mapping_dicts):
        if not mapping_dicts:
            raise ValueError("Provide at least one mapping dict: e.g. intervals=..., ranges=...")
        self._maps = {}
        self._lower_maps = {}
        self._inverse_maps = {}
        for name, mapping in mapping_dicts.items():
            self._maps[name] = mapping

            lower_key = {key.lower(): key for key in mapping}
            self._lower_maps[name] = lower_key

            inv = {}
            for key, val in mapping.items():
                syns = val if isinstance(val, list) else [val]
                for syn in syns:
                    inv[syn.lower()] = key
            self._inverse_maps[name] = inv

        self._default = next(iter(mapping_dicts))

    def lookup(self, s, *, mapping=None, invert=False, collapse_space=True):
        """
        Retrieves the canonical key or its synonyms for a given input string, with optional mapping selection and space-collapsing behavior.

        This method standardizes or reverse-maps synonyms, abbreviations, or alternative forms of a term using predefined mappings.
        It can also handle minor formatting differences (e.g., "1day" vs "1 day") and invert lookups to retrieve all synonyms for a key.

        Parameters:
        ----------
        s : str
            The input string to look up—may be a key or a known synonym.
        mapping : str, optional
            The name of the mapping to use for lookup. If not specified, the default mapping (provided during initialization) is used.
        invert : bool, optional
            If True, returns a list of synonyms associated with the canonical key; otherwise, returns the canonical key itself. Default is False.
        collapse_space : bool, optional
            If True (default), attempts to resolve lookups by normalizing minor formatting differences (e.g., converting "1day" <-> "1 day").

        Returns:
        -------
        str or list[str] or None
            If `invert` is False, returns the canonical key as a string if found, otherwise None.
            If `invert` is True, returns a list of synonyms for the resolved key, or None if not found.

        Raises:
        ------
        KeyError
            If the specified mapping does not exist.
        """
        name = mapping or self._default
        if name not in self._maps:
            raise KeyError(f"Unknown mapping '{name}'. Available: {list(self._maps)}")

        lower_key_map = self._lower_maps[name]
        inverse_map   = self._inverse_maps[name]
        original_map  = self._maps[name]

        token = s.strip().lower()
        key = None

        if token in lower_key_map:
            key = lower_key_map[token]

        elif token in inverse_map:
            key = inverse_map[token]

        elif collapse_space:
            m = re.match(r'^(\d+)([a-z]+)$', token)
            if m:
                spaced = f"{m.group(1)} {m.group(2)}"
                return self.lookup(spaced, mapping=name, invert=invert, collapse_space=False)

            m = re.match(r'^(\d+)\s+([a-z]+)$', token)
            if m:
                joined = f"{m.group(1)}{m.group(2)}"
                return self.lookup(joined, mapping=name, invert=invert, collapse_space=False)

        if key is None:
            return None

        if not invert:
            return key

        val = original_map[key]
        return val[:] if isinstance(val, list) else [val]


_validate        = instrument_validation()

_normalize_dates = _normalizeDate()

_aliasmap       = AliasMapper(
    intervals=_VALID_INTERVAL_ALIASES,
    ranges=_VALID_RANGE_ALIASES
)

def __dir__():
    return __all__


