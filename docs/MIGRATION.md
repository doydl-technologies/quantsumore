# Migration from 3.0.0b2

## Removed project credentials

Do not pass api_key to equity, forex, crypto or analysis methods. APIKey exports, quota helpers, credential files and the project relay module were removed. For example:

~~~python
from quantsumore.api import equity
quote = equity.Latest(ticker="AAPL")
~~~

No replacement project API key is required. Direct provider access remains subject to provider availability. Removing the obsolete credential layer does not guarantee permanent endpoint availability. Review source signatures for affected callers.

## Numerical differences

Corrected numeric values and warm-up masks can differ from 3.0.0b2. Recompute stored outputs and review downstream thresholds rather than comparing only the last row. EMA/MACD use SMA seeds; RSI, ATR and directional movement use Wilder recurrences; Bollinger bands use population standard deviation. Aroon spans N elapsed periods (N+1 observations) and picks the latest tied extreme. OBV starts with first-row volume and does not add volume for unchanged closes. Zero-range stochastic and both-zero RSI conventions match the pinned reference (zero after warm-up). ADX requires 2N observations; MACD retains 12/26/9 defaults.

Only numeric indicator columns are independently verified. Divergence, support/resistance and buy/sell labels are legacy heuristics; predictive performance is not established.

## Runtime and lookup snapshots

Use CPython 3.13 and requirements-runtime.txt for the verified environment. Python 3.8-3.12 compatibility from earlier metadata is not claimed by this correction. Bundled lookups are frozen snapshots, copied to the configured application-data directory on first use without an import-time GitHub request. Existing user lookup files are not overwritten. Market-data calls remain live network operations.

This is an unsupported archival correction; no ongoing maintenance is resumed.

## Crypto metadata refresh and cache access

CryptoConfig now commits replacements atomically and propagates write/validation errors; callers must handle them rather than relying on printed messages. Successful to_sqlite() calls reload committed metadata.

Use snapshot() to obtain cryptos, exchanges and pairs from one transaction. Existing collection properties return copied, freshly read lists. They are read-only views; mutating returned data no longer edits the cache. saved_json_content also copies data: assign the complete updated input before writing it.

See docs/CRYPTO_CONFIG.md for concurrency guarantees and limits.
