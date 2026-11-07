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

from ....date_parser import dtparse
from ....strata_utils import IterDict
from ...parse_tools import (
    convert_to_float,
    convert_to_yield,
)
from ...shape_tools import is_valid_dataframe
from ....statement_types.types import FinancialStatement, DividendSummary, DividendHistory
from ....proxy import Proxy
from ....exceptions import (
    DividendHistoryNoDataError,
    DividendHistoryUnavailableError,
)
from ....markup import idextract

__all__ = ['dividend']



# Defer dependency imports until first use.
pd = Proxy("pandas", None)




"""
Expected Input: Dividend History API Response

This class expects as input the parsed JSON response from a dividend history endpoint, providing
summary and detailed dividend data for a given equity instrument.

Example Input Structure:
[
  {
    "<string-key>": {  # Usually a URL-encoded path or endpoint signature, e.g. "...+NVDA/dividends?assetclass=stocks"
      "response": {
        "data": {
          "dividendHeaderValues": [
            {"label": str, "value": str},  # e.g. "Ex-Dividend Date", "Dividend Yield", etc.
            # ...other header fields...
          ],
          "exDividendDate": str,             # e.g. "06/11/2025"
          "dividendPaymentDate": str,        # e.g. "07/03/2025"
          "yield": str,                      # e.g. "0.02%"
          "annualizedDividend": str,         # e.g. "0.04"
          "payoutRatio": str,                # e.g. "22.92"
          "dividends": {
            "asOf": str or null,
            "headers": {
              "exOrEffDate": str,
              "type": str,
              "amount": str,
              "declarationDate": str,
              "recordDate": str,
              "paymentDate": str
            },
            "rows": [
              {
                "exOrEffDate": str,        # Ex/EFF Date (e.g. "06/11/2025")
                "type": str,               # "Cash" (most common) or other types
                "amount": str,             # e.g. "$0.01"
                "declarationDate": str,    # e.g. "05/28/2025"
                "recordDate": str,         # e.g. "06/11/2025"
                "paymentDate": str,        # e.g. "07/03/2025"
                "currency": str            # e.g. "USD"
              },
              # ...more dividend events...
            ]
          }
        },
        "message": str or null,              # Usually null
        "status": {
          "rCode": int,                      # e.g. 200 (success)
          "bCodeMessage": str or null,       # May contain error or status info
          "developerMessage": str or null
        }
      }
    }
  }
]

Handling Non-Dividend Securities:
	• If a security does not pay dividends, all summary fields will be set to "N/A".
	• In this case, `"dividends": {"headers": null, "rows": null}`.
	• The message field may provide further context (e.g., "Dividend History for Non-Nasdaq symbols is not available").
	• Always check for "N/A" or nulls before processing data.    

Notes:
	• The top-level list supports batch queries for multiple instruments.
	• "<string-key>" is typically a full URL or encoded request signature.
	• The “dividends” sub-table contains the full historical payout record with headers and rows.
	• Dates are always strings, typically in "MM/DD/YYYY" format.
	• Amounts and yield are strings and may include currency symbols.
	• Defensive parsing is attempted for nulls, empty arrays, or partial data.
"""        
class dividend:
    DATE_COLS = ('exOrEffDate', 'declarationDate', 'recordDate', 'paymentDate')
    def __init__(self, json_content=None, verbose=False):
        self.summary=None; self.history=None; self.errors=[]
        if json_content is None: return
        self._content = IterDict.isNested(json_content)
        valid_chunks = self._validate_content(verbose)
        if valid_chunks:
            self._content = valid_chunks
            self.summary = DividendSummary(self._parse_summary())
            self.history = DividendHistory(self._parse_history())
    def _validate_content(self, verbose):
        valid, errs = [], []
        for entry in self._content:
            url, payload = list(entry.items())[0]
            resp = payload['response']; status = resp['status']; data = resp['data']
            ticker = idextract.extract(url, idextract.SYMBOL)
            rows = data.get('dividends', {}).get('rows')
            ok = (status['rCode'] == 200) and rows
            if ok: valid.append(entry); continue
            msg = None
            for key in ('message', 'errorMessage'):
                found = IterDict.filter(resp, key, r'^(?!None$).*', regex=True)
                if found: msg = IterDict.find(found, key); break
            if not msg: msg = "Dividend data could not be found."
            if "not exists" in str(msg):
                msg = ("Dividend History information is presently unavailable for this company. "
                       "It's possible that the company has delisted.")
            errs.append((ticker, msg.rstrip('.')+'.'))
        self.errors = errs
        if verbose and errs:
            for tkr, msg in errs: print(f"{tkr}: {msg}")
        return valid
    def _parse_summary(self):
        frames = []
        for chunk in self._content:
            url, payload = list(chunk.items())[0]
            header_rows = IterDict.find(payload, target_key='dividendHeaderValues')
            if not header_rows: continue
            df = pd.DataFrame(header_rows); df['URL'] = url; frames.append(df)
        if not frames: return pd.DataFrame()
        summary = pd.concat(frames, ignore_index=True)
        summary['Symbol'] = summary['URL'].apply(lambda url: idextract.extract(url, idextract.SYMBOL))
        summary = summary.drop(columns='URL')
        summary.columns = ['Metric','Value','Ticker']
        summary.loc[summary['Metric']=='Annual Dividend','Value'] = summary.loc[summary['Metric']=='Annual Dividend','Value'].apply(convert_to_float)
        summary.loc[summary['Metric']=='Dividend Yield','Value'] = summary.loc[summary['Metric']=='Dividend Yield','Value'].apply(convert_to_yield)
        summary.loc[summary['Metric']=='P/E Ratio','Value'] = summary.loc[summary['Metric']=='P/E Ratio','Value'].apply(convert_to_float)
        summary['Value'] = pd.to_datetime(summary['Value'], errors='coerce').dt.strftime('%Y-%m-%d').fillna(summary['Value'])
        mask_all_na = summary.groupby('Ticker')['Value'].apply(self._all_na)
        summary = summary[~summary['Ticker'].isin(mask_all_na[mask_all_na].index)]
        if is_valid_dataframe(summary) and summary['Ticker'].nunique()==1:
            tkr = summary['Ticker'].iloc[0]
            summary = summary.drop(columns='Ticker')
            summary.loc[len(summary)] = {'Metric':'Ticker','Value':tkr}
        return FinancialStatement(summary)
    def _parse_history(self):
        frames = []
        for chunk in self._content:
            url, payload = list(chunk.items())[0]
            rows = payload['response']['data']['dividends'].get('rows') or []
            if rows:
                df = pd.DataFrame(rows); df['URL'] = url; frames.append(df)
        if not frames: return pd.DataFrame()
        hist = pd.concat(frames, ignore_index=True)
        hist['Symbol'] = hist['URL'].apply(lambda url: idextract.extract(url, idextract.SYMBOL))
        hist = hist.drop(columns='URL')
        for col in self.DATE_COLS:
            if col in hist.columns:
                hist[col] = pd.to_datetime(hist[col], format='%m/%d/%Y', errors='coerce').dt.strftime('%Y-%m-%d').fillna(hist[col])
        if 'amount' in hist.columns:
            hist['amount'] = hist['amount'].apply(convert_to_float)
        hist['timeQueried'] = dtparse.now(utc=True, as_unix=True)
        hist['timeQueried'] = pd.to_datetime(hist['timeQueried'], unit='s').dt.strftime('%Y-%m-%d %H:%M:%S:%f')
        hist.columns = [c.replace('Symbol','Ticker') for c in hist.columns]
        return FinancialStatement(hist)
    @staticmethod
    def _all_na(values): return all(pd.isna(v) or v == 'N/A' for v in values)
    @property
    def DividendReport(self):
        if not is_valid_dataframe(self.summary):
            if self.errors: raise DividendHistoryNoDataError(self.errors)
            raise DividendHistoryUnavailableError()
        return self.summary
    @property
    def DividendData(self):
        if not is_valid_dataframe(self.history):
            if self.errors: raise DividendHistoryNoDataError(self.errors)
            raise DividendHistoryUnavailableError()
        return self.history
    def __dir__(self): return ['summary','history','errors','DividendReport','DividendData']

def __dir__():
    return __all__
