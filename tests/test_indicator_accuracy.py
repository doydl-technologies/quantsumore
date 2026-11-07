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

import math
import io
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from tests.indicator_accuracy import actual, audit, datasets
from tests.runtime import prepare_runtime


class IndicatorAccuracyTests(unittest.TestCase):


    def frame(self, close, high=None, low=None, volume=None):
        close = np.array(close, dtype=float)
        return pd.DataFrame({'Symbol': 'VERIFY', 'Date': pd.date_range('2024-01-01', periods=len(close)).strftime('%Y-%m-%d'),
                             'Open': close, 'Close': close, 'High': close + 1 if high is None else high,
                             'Low': close - 1 if low is None else low,
                             'Volume': np.full(len(close), 100.0) if volume is None else volume})

    def test_all_nine_indicators_against_independent_talib_binary(self):
        report = audit()
        failures = [check for check in report['checks'] if not (check['mask_equal'] and check['numeric_equal'])]
        self.assertEqual(failures, [])
        self.assertEqual(report['passed'], report['total'])
        self.assertEqual(report['total'], 661)

    def test_hand_calculated_moving_averages_and_population_bands(self):
        result = actual(self.frame([1, 2, 3, 4, 5]), 3, 'moving')
        np.testing.assert_allclose(result['SMA'].iloc[2:], [2, 3, 4])
        np.testing.assert_allclose(result['EMA'].iloc[2:], [2, 3, 4])
        np.testing.assert_allclose(result['BB_Upper'].iloc[2:], np.array([2, 3, 4]) + 2 * math.sqrt(2 / 3))
        np.testing.assert_allclose(result['BB_Lower'].iloc[2:], np.array([2, 3, 4]) - 2 * math.sqrt(2 / 3))
        self.assertTrue(result['EMA'].iloc[:2].isna().all())

    def test_hand_calculated_obv_equal_closes_and_adl_zero_range(self):
        obv = actual(self.frame([10, 11, 11, 9, 9, 10], volume=[100, 200, 300, 400, 0, 600]), 3, 'obv')
        np.testing.assert_array_equal(obv['OBV'], [100, 300, 300, -100, -100, 500])
        adl = actual(self.frame([10, 0, 5, 7.5], high=[10, 10, 5, 10], low=[0, 0, 5, 0], volume=[100, 200, 300, 100]), 3, 'adl')
        np.testing.assert_allclose(adl['AD_Line'], [100, -100, -100, -50])

    def test_hand_calculated_atr_and_directional_movement(self):
        frame = self.frame([10, 11, 10, 13, 12, 12], high=[11, 12, 11, 14, 13, 12], low=[9, 10, 9, 12, 11, 12])
        atr = actual(frame, 3, 'atr')
        np.testing.assert_allclose(atr['ATR'].iloc[3:], [8 / 3, 22 / 9, 44 / 27])
        rising = actual(self.frame(np.arange(10, 50)), 14, 'dmi')
        np.testing.assert_allclose(rising['+DI'].iloc[14:], 50)
        np.testing.assert_allclose(rising['-DI'].iloc[14:], 0)
        np.testing.assert_allclose(rising['ADX'].iloc[27:], 100)

    def test_aroon_uses_full_elapsed_period_and_latest_tied_extreme(self):
        oldest = actual(self.frame([3, 2.5, 2, 1.5], high=[5, 4, 3, 2], low=[1, 1, 1, 1]), 3, 'aroon')
        self.assertEqual(oldest['Aroon_Up'].iloc[-1], 0)
        self.assertEqual(oldest['Aroon_Down'].iloc[-1], 100)
        tied = actual(self.frame([3, 2.5, 3, 2.5], high=[5, 4, 5, 4], low=[1, 1, 1, 1]), 3, 'aroon')
        self.assertAlmostEqual(tied['Aroon_Up'].iloc[-1], 200 / 3)

    def test_stochastic_joint_warmup_and_zero_denominator_convention(self):
        result = actual(self.frame([1, 2, 3, 4, 5]), 3, 'stochastic')
        self.assertTrue(result['%K'].iloc[:4].isna().all())
        self.assertEqual(result['%K'].iloc[-1], 75)
        self.assertEqual(result['%D'].iloc[-1], 75)
        flat = actual(self.frame([10] * 40, high=[10] * 40, low=[10] * 40), 14, 'stochastic')
        np.testing.assert_allclose(flat[['%K', '%D']].iloc[15:], 0)
        rsi = actual(self.frame([10] * 40), 14, 'rsi')
        np.testing.assert_allclose(rsi['RSI'].iloc[14:], 0)

    def test_all_indicators_have_no_lookahead_and_preserve_nondefault_index(self):
        frame = dict(datasets())['nondefault_index']
        for indicator in ('moving', 'macd', 'rsi', 'dmi', 'aroon', 'obv', 'adl', 'stochastic', 'atr'):
            with self.subTest(indicator=indicator):
                long = actual(frame, 14, indicator)
                short = actual(frame.iloc[:120], 14, indicator)
                pd.testing.assert_frame_equal(long.iloc[:120], short)
                self.assertTrue(long.index.equals(frame.index))

    def test_exact_minimum_history_is_accepted_and_one_row_less_is_rejected(self):
        for indicator, length in {'moving': 14, 'macd': 34, 'rsi': 15, 'dmi': 28, 'aroon': 15, 'stochastic': 16, 'atr': 15}.items():
            with self.subTest(indicator=indicator):
                frame = self.frame(np.arange(10, 10 + length))
                actual(frame, 14, indicator)
                with self.assertRaises(ValueError):
                    actual(frame.iloc[:-1], 14, indicator)




if __name__ == '__main__':
    unittest.main(verbosity=2)
