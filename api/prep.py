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

import re

from .market_utils import fxutil, CurrencyQuery
from ..date_parser import dtparse
from ..markup import url_encode_decode
from ..exceptions import InvalidCurrencyPairError
from ._prep_utils import (
    _normalize_dates,
    _INTERVAL_TO_MINUTES,
    _RANGE_TO_DAYS,
    _enforce_valid_combo,
    _auto_adjust_interval,
    _days_from_range,
    _MAX_POINTS,
    _validate,
    _aliasmap,
)


__all__ = [
    'equity_adapter',
    'forex_adapter',
    'crypto_adapter',
    'cpi_adapter',
    'treasury_adapter',
]






# Equity URL routing.
class _Equity:
    """Build provider URLs for equity queries.

Normalize and validate tickers, resolve query-specific dates and intervals,
and batch symbols only for endpoints configured to accept multiple tickers.
Retrieval and parsing are handled by the data clients."""
    def __init__(self):
        self.base_url_v1 = 'https://stockanalysis.com/'
        self.base_url_v2 = 'https://query1.finance.yahoo.com/v8/finance/chart/'
        self.base_url_v3 = 'https://query1.finance.yahoo.com/v7/finance/spark?symbols='
        self.base_url_v4 = 'https://api.nasdaq.com/api/company/'
        self.base_url_v5 = 'https://api.nasdaq.com/api/quote/'
        self.base_url_v6 = 'https://api.nasdaq.com/api/ipo/calendar?date='

    def _normalize_tickers(self, tickers):
        if isinstance(tickers, str): tickers = [tickers]; [_validate.stock_ticker(t) for t in tickers]
        elif isinstance(tickers, list):
            if not all(isinstance(t, str) for t in tickers): raise ValueError("All elements in the ticker list must be strings.")
        else: raise ValueError("Input must be either a string or a list of strings.")
        norm = list(dict.fromkeys(t.upper() for t in tickers))
        [_validate.stock_ticker(t) for t in norm]
        return norm

    def _construct_url(self, id, period1=None, period2=None, f_rng=None, f_period=None, f_interval=None, Type=None):
        if period1 is None and period2 is None:
            if Type == "y_spark":
                t = url_encode_decode.encode_str(i=id, chars_to_encode=",", join_char=",")
                return (self.base_url_v3, f"{t}&range={f_rng}&interval={f_interval}&indicators=close&includeTimestamps=true&includePrePost=false&corsDomain=finance.yahoo.com&.tsrc=finance") # Used by: "latest" and "last" queries in make()
            if Type == "exchange_company":
                sel = 'Quarterly' if f_period == 'Quarterly' or f_period is None else 'Annually' # Used by: "financials" query in make()
                period = "2" if sel == 'Quarterly' else "1"
                return (self.base_url_v4, f"{id}/financials?frequency={period}")
            if Type == "div_payout":
                return (self.base_url_v5, f"{id}/dividends?assetclass=stocks") # Used by: "dividend_history" query in make()
            if Type == "stats":
                return (self.base_url_v1, f"api/screener/m/f?m=s&s=symbol&c=s,n,marketCap,price,volume,peRatio,open,close,low,high,dividendYield,low52,high52,priceTarget,exDivDate,nextEarningsDate,averageVolume,eps,beta&cn=100&f=s-is-%2524{id}") # Used by: "stats" query in make()
            return (self.base_url_v1, f"stocks/{id.lower()}/company/__data.json?x-sveltekit-trailing-slash=1&x-sveltekit-invalidated=001") # Used by: "profile" query in make()
        elif Type == "ipo" and period1:
            return (self.base_url_v6, f"{period1}") # Used by: "ipo" query in make()
        return (self.base_url_v2, f"{id}?formatted=true&includeAdjustedClose=true&interval=1d&userYfid=false&lang=en-US&region=US&period1={period1}&period2={period2}") # Used by: "price" query in make() (when start/end are provided)

    def make(self, query, *args, **kwargs):
        """
        Supported queries:
            - profile:    Company overview/profile (base_url_v1)
            - stats:      Statistics snapshot (base_url_v1)
            - last:       Recent/intraday/minute-by-minute price data (base_url_v3, "spark" endpoint)
            - financials: Financial statements (base_url_v4)
            - dividend_history: Dividends (base_url_v5)
            - price:      Historical price or "latest" price if range is today (base_url_v2)
            - ipo:        IPO calendar/listings (base_url_v6)
        """        
        if query.lower() == "ipo":
            period = kwargs.get('period')
            period = _normalize_dates.norm(period, future_date_check=True, date_format="%Y-%m", clip="end") if period else dtparse.now(format="%Y-%m")
            return self._construct_url(id=None, period1=period, Type="ipo")  
        ticker = args[0] if args else kwargs.get('ticker')
        start, end = kwargs.get('start'), kwargs.get('end')
        ticker = self._normalize_tickers(ticker)
        if query.lower() == "profile":
            return self._construct_url(id=ticker[0] if isinstance(ticker, list) else ticker)
        if query.lower() == "stats":
            return self._construct_url(id=ticker[0] if isinstance(ticker, list) else ticker, Type="stats")
           
        if query.lower() == "last":
            rng = kwargs.get("range", "1d")          
            interval = kwargs.get('interval', '1m')
            
            rng = _aliasmap.lookup(rng, mapping="ranges")
            interval = _aliasmap.lookup(interval, mapping="intervals")            
            
            interval = interval.lower()
            rng = rng.lower()
            if interval not in _INTERVAL_TO_MINUTES:
                raise ValueError(f"Unsupported interval '{interval}'. Valid intervals: {list(_INTERVAL_TO_MINUTES.keys())}")
            if rng not in _RANGE_TO_DAYS and rng not in ("ytd", "max"):
                raise ValueError(f"Unsupported range '{rng}'. Valid ranges: {list(_RANGE_TO_DAYS.keys()) + ['ytd', 'max']}")
            
            _enforce_valid_combo(rng, interval)
            
            # Coarsen the interval when the estimated history exceeds 100,000 points.
            new_iv = _auto_adjust_interval(rng, interval)
            if new_iv != interval:
                print(f"interval '{interval}' bumped to '{new_iv}' to limit payload")
                interval = new_iv

            days = _days_from_range(rng)
            pts  = float("inf") if days == float("inf") else days * 1440 / _INTERVAL_TO_MINUTES[interval]
            max_tks = int(_MAX_POINTS // pts) if pts != float("inf") else 0

            if max_tks < 1:
                raise ValueError(f"Even one ticker at range='{rng}' & interval='{interval}' exceeds {MAX_POINTS:,} points.")
            if len(ticker) > max_tks:
                raise ValueError(
                    f"Too many tickers: for range='{rng}', interval='{interval}', "
                    f"max {max_tks} tickers allowed (≈{int(pts):,} points each)."
                )
            
            return self._construct_url(id=ticker, f_rng=rng, f_interval=interval, Type="y_spark")
           
        if query.lower() == "financials":
            period = kwargs.get('period')
            return self._construct_url(id=ticker[0] if isinstance(ticker, list) else ticker, f_period=period, Type="exchange_company")
        if query.lower() == "dividend_history":
            return self._construct_url(id=ticker[0] if isinstance(ticker, list) else ticker, Type="div_payout")
        if query.lower() == "price":
            t = ticker[0] if isinstance(ticker, list) else ticker
            if start and end:
                start, end = _normalize_dates.norm(start, end)
                return self._construct_url(id=t, period1=start, period2=end)
            raise ValueError("Start and end dates are required for historical price queries.")    
           
        if query.lower() == "latest":
            return self._construct_url(id=ticker[0] if isinstance(ticker, list) else ticker, f_rng="1d", f_interval="1m", Type="y_spark")
    def __dir__(self): return ['make']    


# Forex URL routing.
class _Forex:
    """Build provider URLs for currency rates and conversions.

Validate currency codes and pairs against the local registry, normalize date
ranges, and apply query-specific filters and batching. Retrieval and parsing
are handled by the data clients."""
    def __init__(self):
        self.historical_batching_enabled = False
        self.bid_ask_batching_enabled = False
        self.major_forex_currencies = fxutil.which.major()
        self.ccy = None            
        self.interbank_base_url = 'https://www.mtfxgroup.com/api/rates/getLiveExhangeRate/?currencies='
        self.historical_base_url = 'https://www.mtfxgroup.com/api/rates/frequencyRateCustom/'
        self.bid_ask_url = 'https://api.nasdaq.com/api/quote/'
    
    def _normalize_currencies(self, currencies, currency_dict_type="major"):
        lst = []
        if isinstance(currencies, str): currencies = [currencies]
        if isinstance(currencies, list):
            if not all(isinstance(c, str) for c in currencies): raise ValueError("All elements in the currency list must be strings.")
            for c in currencies:
                result = _validate.fx_currency(c, currency_dict_type=currency_dict_type)
                if result is None: lst.append(_validate.validated_instrument)
        else: raise ValueError("Input must be either a string or a list of strings.")
        norm = list(dict.fromkeys(c.upper() for c in lst))
        return norm[0] if len(norm) == 1 else norm

    def _construct_url(self, id, filter_currencies=None, ignore_currencies=None, p1=None, p2=None):
        if all(x is None for x in [p1, p2]):
            ccy = self.major_forex_currencies.copy()
            id = re.sub(r'\s+', chr(32), id).strip()
            if len(id) == 3:
                filter_currencies = [filter_currencies] if isinstance(filter_currencies, str) else filter_currencies
                ignore_currencies = [ignore_currencies] if isinstance(ignore_currencies, str) else ignore_currencies
                if filter_currencies: ccy = [curr for curr in filter_currencies if curr in ccy]
                elif ignore_currencies: ccy = [curr for curr in ccy if curr not in ignore_currencies]
                else: 
                    if id in ccy: ccy.remove(id)
                s = '%2C'.join(ccy)
                return (self.interbank_base_url, f"{s}&source={id}")
        start = p1.replace('/', '%2F') if p1 else ""
        end = p2.replace('/', '%2F') if p2 else ""
        return (self.historical_base_url, f"?ratepair={id}&start_date={start}&end_date={end}")

    def make(self, query, *args, **kwargs):
        if query.lower() == "historical":
            pair = args[0] if args else kwargs.get('currency_pair')
            start = kwargs.get('start')
            end = kwargs.get('end')
            pair = self._normalize_currencies(pair)
            if start and end: sdate, edate = _normalize_dates.norm(start, end, future_date_check=True, date_format='%d/%m/%Y')
            elif start: sdate, edate = _normalize_dates.norm(start, start, future_date_check=True, date_format='%d/%m/%Y')
            else: raise ValueError("Both start and end dates are required for historical data.")
            if self.historical_batching_enabled and isinstance(pair, list) and len(pair) > 1:
                urls = [self._construct_url(id=c, p1=sdate, p2=edate) for c in pair]
                return urls if len(urls) > 1 else urls[0]
            if isinstance(pair, list): pair = pair[0]
            return self._construct_url(id=pair, p1=sdate, p2=edate)
        elif query.lower() == "interbank":
            bc = args[0] if args else kwargs.get('base_currency')
            if bc is None: raise ValueError("Base currency must be provided for 'interbank' queries.")
            fltr = args[1] if len(args) > 1 else kwargs.get('filter_currencies', [])
            ign = args[2] if len(args) > 2 else kwargs.get('ignore_currencies', [])
            fltr = fxutil.tokenize(fltr) if fltr else None
            ign = fxutil.tokenize(ign) if ign else None
            bc = self._normalize_currencies(bc)
            return self._construct_url(id=bc, filter_currencies=fltr, ignore_currencies=ign)
        elif query.lower() == "bid_ask":
            pair = args[0] if args else kwargs.get('currency_pair')
            pair = self._normalize_currencies(pair, currency_dict_type="all_currency_names")
            pair = pair[0] if isinstance(pair, list) else pair
            try:
                if not fxutil.query(pair, query_type="major_pairs", ret_type="bool"):
                    raise InvalidCurrencyPairError(f"Currency pair '{pair}' is invalid or not supported.")
            except Exception:
                raise InvalidCurrencyPairError(f"Currency pair '{pair}' is invalid or not supported.")
            return (self.bid_ask_url, f"{pair}/summary?assetclass=currencies")
        elif query.lower() == "convert":
            pair = args[0] if args else kwargs.get('currency_pair')
            _validate.fx_currency(pair)
            self.ccy = _validate.validated_instrument
            from datetime import date, timedelta
            end = date.today()
            start = end - timedelta(days=30)
            return self._construct_url(
                id=self.ccy, p1=start.strftime('%d/%m/%Y'), p2=end.strftime('%d/%m/%Y')
            )
        # The current endpoint is disabled because of provider bandwidth constraints.
        elif query.lower() == "current":
            raise Exception("The 'current' endpoint is currently disabled due to bandwidth constraints.")

    def __dir__(self): return ['make'] 


# Cryptocurrency URL routing.
class _Crypto:
    """Build provider URLs for cryptocurrency queries.

Resolve known slugs and coin IDs through the local registry, normalize currency
filters, and apply query-specific limits and batching. Retrieval and parsing
are handled by the data clients."""
    def __init__(self):
        self.historical_batching_enabled = False
        self.live_batching_enabled = False
        self.historical_base_url = 'https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical?'
        self.live_base_url = 'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/market-pairs/latest?'

    def _normalize_slugs(self, slugs):
        if isinstance(slugs, str): slugs = [slugs]; [_validate.crypto_slug_name(s) for s in slugs]
        elif isinstance(slugs, list):
            if not all(isinstance(s, str) for s in slugs): raise ValueError("All elements in the slug list must be strings.")
        else: raise ValueError("Input must be either a string or a list of strings.")
        norm = list(dict.fromkeys(s.lower() for s in slugs))
        return norm[0] if len(norm) == 1 else norm

    def _normalize_ids(self, ids):
        ID_list = []
        if isinstance(ids, str): ids = [ids]
        if isinstance(ids, list):
            if not all(isinstance(ID, str) for ID in ids): raise ValueError("All elements in the ID list must be strings.")
            for i in ids:
                result = _validate.crypto_slug_name(i)
                if result is None: ID_list.append(_validate.validated_instrument[1])
        else: raise ValueError("Input must be either a string or a list of strings.")
        norm = list(dict.fromkeys(ID for ID in ID_list))
        return norm[0] if len(norm) == 1 else norm

    def _construct_url(self, id, baseCurrency=None, quoteCurrency=None, limit=100, exchange_type='all', period1=None, period2=None):
        if all(x is None for x in [period1, period2]):
            endpoint = f"slug={id}&start=1&limit={limit}&category=spot&centerType=all&sort=cmc_rank_advanced&direction=desc&spotUntracked=true"
            if baseCurrency: endpoint += f'&baseCurrencyId={CurrencyQuery.SymbolreturnID(baseCurrency)}'
            if quoteCurrency: endpoint += f'&quoteCurrencyId={CurrencyQuery.SymbolreturnID(quoteCurrency)}'
            if exchange_type and exchange_type.lower() not in ['all', 'dex', 'cex']: exchange_type = 'all'
            endpoint = endpoint.replace("centerType=all", f'centerType={exchange_type.lower()}')
            return (self.live_base_url, endpoint)
        else:
            endpoint = f"id={id}&convertId=2781&timeStart={period1}&timeEnd={period2}&interval=1d"
            return (self.historical_base_url, endpoint)

    def make(self, query, *args, **kwargs):
        if query.lower() == "historical":
            slug = args[0] if args else kwargs.get('slug')
            if slug is None: raise ValueError("Slug name must be provided for 'historical' queries.")
            slug = [slug] if isinstance(slug, str) else slug
            start = args[1] if len(args) > 1 else kwargs.get('start')
            end = args[2] if len(args) > 2 else kwargs.get('end')
            ID = self._normalize_ids(slug)
            ID = [str(ID)] if not isinstance(ID, list) else [str(i) for i in ID]
            if not start: raise ValueError("Both start and end dates are required for historical data.")
            start, end = _normalize_dates.norm(start, end, future_date_check=True, date_format="utc_unix")
            if self.historical_batching_enabled:
                urls = [self._construct_url(id=i, period1=start, period2=end) for i in ID]
                return urls if len(urls) > 1 else urls[0]
            else:
                return self._construct_url(id=ID[0], period1=start, period2=end)
        elif query.lower() == "live":
            slug = args[0] if args else kwargs.get('slug')
            if slug is None: raise ValueError("Slug name must be provided for 'live' queries.")
            slug = [slug] if isinstance(slug, str) else slug
            base = args[1] if len(args) > 1 else kwargs.get('baseCurrencySymbol')
            quote = args[2] if len(args) > 2 else kwargs.get('quoteCurrencySymbol')
            limit = args[3] if len(args) > 3 else kwargs.get('limit', 100)
            exch = args[4] if len(args) > 4 else kwargs.get('exchangeType', 'all')
            slug = self._normalize_slugs(slug)
            if self.live_batching_enabled and isinstance(slug, list) and len(slug) > 1:
                urls = [self._construct_url(id=s, baseCurrency=base, quoteCurrency=quote, limit=limit, exchange_type=exch) for s in slug]
                return urls if len(urls) > 1 else urls[0]
            else:
                if isinstance(slug, list): slug = slug[0]
                return self._construct_url(id=slug, baseCurrency=base, quoteCurrency=quote, limit=limit, exchange_type=exch)
    def __dir__(self): return ['make']
    

# CPI URL routing.
class _CPI:
    """Build FRED series-page URLs from nonempty series identifiers.

    make() requires a series_id and raises ValueError when it is empty.
    This adapter assembles URLs; it does not fetch or validate series content.
    """
    def __init__(self): self.base_url_cpi = 'https://fred.stlouisfed.org/series/'
    def _construct_url(self, series_id): return f"{self.base_url_cpi}{series_id}"
    def make(self, series_id, *args, **kwargs):
        if not series_id: raise ValueError("Series ID is required")
        return self._construct_url(series_id)
    def __dir__(self): return ['make']
    

# Treasury URL routing.
class _TreasuryGov:
    """Build annual Treasury CSV URLs for bill rates and yield curves.

    make() accepts "tbill" or "tyield" and a period of None, "cy", YYYY or
    YYYYMM. A monthly period selects the year's download; the client filters
    the rows afterward. Invalid query names and period formats raise ValueError.
    Provider coverage is not checked by this URL builder.
    """
    def __init__(self):
        self.base_url = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/'
    def _construct_url(self, identifier, period=None):
        today = dtparse.nowCT(); current_year = today.year
        if identifier == 'tbill': csv_type = 'daily_treasury_bill_rates'
        elif identifier == 'tyield': csv_type = 'daily_treasury_yield_curve'
        else: raise ValueError(f"Unknown identifier: {identifier}")
        if period is None or str(period).lower() == 'cy': year = current_year
        else:
            p = str(period)
            if len(p) == 6 and p.isdigit(): year = int(p[:4])
            elif len(p) == 4 and p.isdigit(): year = int(p)
            else: raise ValueError("Period must be None, 'cy', a 4-digit year, or 6-digit yyyymm.")
        return f"{self.base_url}{year}/all?type={csv_type}&field_tdr_date_value={year}&page&_format=csv"
    def make(self, query, *args, **kwargs):
        period = args[0] if args else kwargs.get('period', None)
        if query.lower() == "tbill": return self._construct_url('tbill', period)
        elif query.lower() == "tyield": return self._construct_url('tyield', period)
        else: raise ValueError(f"Invalid query: {query}")
    def __dir__(self): return ['make']


crypto_adapter   = _Crypto()
forex_adapter    = _Forex()
equity_adapter   = _Equity()
cpi_adapter      = _CPI()
treasury_adapter = _TreasuryGov()

def __dir__():
    return __all__


