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

import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


import numpy as np
import pandas as pd
import talib

from tests.runtime import prepare_runtime


def datasets():
    fixture = pd.read_csv(ROOT / 'ohlcv.csv')
    yield 'illustrative_csv', fixture
    rng = np.random.default_rng(27413)
    count = 180
    times = np.arange(count, dtype=float)
    paths = {
        'oscillating': 100 + 5 * np.sin(times / 3) + 2 * np.cos(times / 7),
        'rising': 50 + times * .4,
        'falling': 150 - times * .4,
        'flat_zero_range': np.full(count, 100.0),
        'tied_extremes': 100 + np.repeat([0, 3, 0, -3, 0, 2], 30),
        'gaps': 100 + np.cumsum(rng.normal(0, 1, count)) + (times >= 60) * 20 - (times >= 120) * 30,
        'zero_volume': 100 + np.cumsum(rng.normal(0, .8, count)),
        'nondefault_index': 100 + np.cumsum(rng.normal(0, .8, count)),
    }
    for name, closes in paths.items():
        spread = np.zeros(count) if name == 'flat_zero_range' else np.full(count, 1.5)
        opens = closes + .3 * np.sin(times)
        if name == 'flat_zero_range':
            opens = closes.copy()
        frame = pd.DataFrame({'Symbol': 'VERIFY', 'Date': pd.date_range('2024-01-01', periods=count).strftime('%Y-%m-%d'),
                              'Open': opens, 'High': np.maximum(opens, closes) + spread,
                              'Low': np.minimum(opens, closes) - spread, 'Close': closes,
                              'Volume': np.zeros(count) if name == 'zero_volume' else 1000 + times % 17 * 137})
        if name == 'nondefault_index':
            frame.index = np.arange(1000, 1000 + count) * 2
        yield name, frame


def reference(frame, period):
    high, low, close, volume = (frame[column].to_numpy(dtype=float) for column in ('High', 'Low', 'Close', 'Volume'))
    upper, middle, lower = talib.BBANDS(close, period, 2, 2, 0)
    macd, signal, histogram = talib.MACD(close, 12, 26, 9)
    down, up = talib.AROON(high, low, period)
    k, d = talib.STOCHF(high, low, close, period, 3, 0)
    return {
        'moving': {'SMA': talib.SMA(close, period), 'EMA': talib.EMA(close, period),
                   'BB_Middle': middle, 'BB_Upper': upper, 'BB_Lower': lower},
        'macd': {'MACD_Line': macd, 'Signal_Line': signal, 'MACD_Histogram': histogram},
        'rsi': {'RSI': talib.RSI(close, period)},
        'dmi': {'+DI': talib.PLUS_DI(high, low, close, period), '-DI': talib.MINUS_DI(high, low, close, period),
                'ADX': talib.ADX(high, low, close, period)},
        'aroon': {'Aroon_Up': up, 'Aroon_Down': down},
        'obv': {'OBV': talib.OBV(close, volume)},
        'adl': {'AD_Line': talib.AD(high, low, close, volume)},
        'stochastic': {'%K': k, '%D': d},
        'atr': {'ATR': talib.ATR(high, low, close, period)},
    }


def actual(frame, period, indicator):
    from quantsumore.analysis import tAnalysis
    methods = {
        'moving': ('MovingAveragesAndBollingerBands', {'sma_period': period, 'ema_period': period, 'bb_period': period}),
        'macd': ('MACD', {}), 'rsi': ('RelativeStrengthIndex', {'period': period}),
        'dmi': ('DirectionalMovementIndex', {'period': period}), 'aroon': ('AroonIndicator', {'period': period}),
        'obv': ('OnBalanceVolume', {}), 'adl': ('AccumulationDistributionLine', {}),
        'stochastic': ('FastStochasticOscillator', {'k_period': period}), 'atr': ('AverageTrueRange', {'atr_period': period}),
    }
    method, kwargs = methods[indicator]
    with contextlib.redirect_stdout(io.StringIO()):
        return getattr(tAnalysis(frame.copy()), method)(**kwargs).df


def audit():
    checks = []
    with prepare_runtime():
        for name, frame in datasets():
            for period in (2, 5, 14, 25, 60):
                if len(frame) < 2 * period:
                    continue
                expected = reference(frame, period)
                for indicator, columns in expected.items():
                    if indicator in ('macd', 'obv', 'adl') and period != 14:
                        continue
                    result = actual(frame, period, indicator)
                    for column, target in columns.items():
                        values = result[column].to_numpy(dtype=float)
                        finite = np.isfinite(values) & np.isfinite(target)
                        mask_equal = np.array_equal(np.isfinite(values), np.isfinite(target))
                        numeric_equal = np.allclose(values[finite], target[finite], rtol=1e-8, atol=1e-8)
                        checks.append({'dataset': name, 'period': period, 'indicator': indicator, 'column': column,
                                       'mask_equal': bool(mask_equal), 'numeric_equal': bool(numeric_equal),
                                       'max_abs_error': float(np.max(np.abs(values[finite] - target[finite]))) if finite.any() else None,
                                       'actual_first': int(np.flatnonzero(np.isfinite(values))[0]) if np.isfinite(values).any() else None,
                                       'expected_first': int(np.flatnonzero(np.isfinite(target))[0]) if np.isfinite(target).any() else None})
    return {'recorded_at': datetime.now(timezone.utc).isoformat(), 'reference': 'TA-Lib',
            'wrapper_version': talib.__version__, 'c_version': talib.__ta_version__.decode(),
            'tolerance': {'relative': 1e-8, 'absolute': 1e-8}, 'checks': checks,
            'passed': sum(check['mask_equal'] and check['numeric_equal'] for check in checks), 'total': len(checks)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='indicator-current.json')
    args = parser.parse_args()
    report = audit()
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['passed']}/{report['total']} series comparisons passed against {report['reference']} {report['wrapper_version']}.")
    for indicator in ('moving', 'macd', 'rsi', 'dmi', 'aroon', 'obv', 'adl', 'stochastic', 'atr'):
        failures = [check for check in report['checks'] if check['indicator'] == indicator and not (check['mask_equal'] and check['numeric_equal'])]
        print(indicator, f'{len(failures)} failed comparisons')
    sys.exit(0 if report['passed'] == report['total'] else 1)
