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
from math import isfinite
from io import StringIO
from datetime import datetime, timezone
from urllib.parse import urlencode

from ....date_parser import dtparse
from ....exceptions import (
    CPIDateParseError, 
    CPIDataUnavailableError
)

__all__ = ['CUUR0000AA0']



current_date = dtparse.nowCT(format='%Y-%m-%d')

class CUUR0000AA0:
    class Date:
        def __init__(self, html_content, force_end_date=None):
            self.html_content = html_content
            self.force_end_date = force_end_date or dtparse.subtract_months(current_date, 2)
            self.data = self.extract()
            self.abbreviated_months = {
                "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                "June": 6, "Jul": 7, "July": 7, "Aug": 8, "Sep": 9, "Oct": 10,
                "Nov": 11, "Dec": 12
            }
            self.months_pattern = '|'.join(list(self.abbreviated_months.keys()))
            self.pattern = rf'\b({self.months_pattern})\s(\d{{4}})\b'
            self.end_date = self.peel()

        def extract(self):
            if self.html_content:
                from lxml import html as Html
                tree = Html.fromstring(self.html_content)
                xpath = '//*[@id="mobile-meta-col"]'
                element = tree.xpath(xpath)
                if element:
                    return element[0].text_content()
            return None

        def peel(self):
            if self.data:
                match = re.search(self.pattern, self.data)
                if match:
                    month_abbr = match.group(1)
                    year = int(match.group(2))
                    month = self.abbreviated_months.get(month_abbr)
                    if month:
                        date = dtparse.build(year=year, month=month, day=1)
                        return date.strftime('%Y-%m-%d')
            return self.force_end_date 
        
        def date(self):
            """Returns date string or raises if unavailable."""
            if self.end_date is None:
                raise CPIDateParseError()
            return self.end_date        
           
        def __dir__(self):
            return ['date']

    class Data:
        """Fetch monthly FRED observations and retain the legacy calculator columns.

        current_date remains accepted for call compatibility; retrieval uses
        published observations rather than a chart-vintage or HTML date filter.
        """
        def __init__(self, start_date='1913-01-01', current_date=current_date, end_date=None,
                     series_id='CPIAUCNS'):
            self.start = start_date
            self.end = end_date
            self.current = current_date
            if not isinstance(series_id, str) or not series_id.strip():
                raise ValueError("A nonempty FRED series identifier is required.")
            self.series_id = series_id.strip().upper()
            self.url = self.construct_url()
            self.period_mapping = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            self.all_items = self.construct_data()
            
        def construct_url(self):
            """Request observations directly without chart styling or an HTML date lookup."""
            params = {'id': self.series_id}
            if self.start is not None:
                params['cosd'] = self.start
            if self.end is not None:
                params['coed'] = self.end
            return 'https://fred.stlouisfed.org/graph/fredgraph.csv?' + urlencode(params)

        def construct_data(self):
            """Fetch a live CSV with connect/read limits and preserve failure causes."""
            import pandas as pd
            import requests
            try:
                response = requests.get(
                    self.url, timeout=(3.05, 10),
                    headers={'User-Agent': 'quantsumore/3.0 (CPI data client)', 'Accept': 'text/csv'}
                )
                response.raise_for_status()
                raw = pd.read_csv(StringIO(response.text), na_values=['.'])
                date_column = next(
                    (column for column in raw.columns
                     if column.strip().lower() in ('date', 'observation_date')), None
                )
                if date_column is None or self.series_id not in raw.columns:
                    raise ValueError("CPI CSV lacks its date or requested series column.")
                dates = pd.to_datetime(raw[date_column], errors='raise')
                values = pd.to_numeric(raw[self.series_id], errors='raise')
                monthly = pd.DataFrame({'date': dates, 'value': values}).dropna()
                if self.start is not None:
                    monthly = monthly[monthly['date'] >= pd.Timestamp(self.start)]
                if self.end is not None:
                    monthly = monthly[monthly['date'] <= pd.Timestamp(self.end)]
                monthly = monthly.sort_values('date')
                if (monthly.empty or not (monthly['value'] > 0).all()
                        or not monthly['value'].map(isfinite).all()):
                    raise ValueError("CPI CSV contains no valid positive observations in the requested range.")
                if monthly['date'].dt.to_period('M').duplicated().any():
                    raise ValueError("CPI CSV contains duplicate monthly observations.")
                latest = monthly['date'].max().strftime('%Y-%m-%d')
                monthly['period'] = monthly['date'].dt.month.map(self.period_mapping)
                monthly['year'] = monthly['date'].dt.year.astype(int)
                monthly['value'] = monthly['value'].astype(float)
                # Retain the legacy output identifier; provenance uses the actual FRED series.
                monthly['series_id'] = 'CUUR0000AA0'
                monthly = monthly[['series_id', 'year', 'period', 'value']]
                annual = monthly.groupby('year')['value'].mean().round(1).reset_index()
                annual['series_id'] = 'CUUR0000AA0'
                annual['period'] = 'Average'
                result = pd.concat([monthly, annual[monthly.columns]], ignore_index=True)
                result.attrs.update(
                    source='FRED', source_series_id=self.series_id, source_url=self.url,
                    fetched_at=datetime.now(timezone.utc).isoformat(), latest_observation=latest,
                    annual_average='Mean of available monthly observations, rounded to one decimal.'
                )
                return result
            except (requests.RequestException, ValueError, KeyError, TypeError, OverflowError) as error:
                raise CPIDataUnavailableError(
                    f"Unable to retrieve live CPI series {self.series_id}: {error}"
                ) from error

        def all_items_index(self):
            """Returns pandas DataFrame with CPI data or raises if unavailable."""
            if self.all_items is None:
                raise CPIDataUnavailableError()
            return self.all_items        
           
        def __dir__(self):
            return ['all_items_index']

def __dir__():
    return __all__
