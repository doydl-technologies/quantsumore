<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-light.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-dark.png">
    <img src="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-dark.png" alt="quantsumore — powered by DOYDL Technologies" width="700">
  </picture>
</p>

# quantsumore — retired

> [!WARNING]
> **This project was retired on July 27, 2025, and remains unsupported.**
> Version 3.0.0b3 is a one-time corrective archival candidate, not a resumption of maintenance.
> After this correction, no further releases, compatibility fixes, endpoint repairs, support
> or security updates are planned. Issues and pull requests are not being accepted.
>
> Use the archive to understand or reproduce legacy workflows. Do not rely on it for
> production systems, security-sensitive workloads or financial decisions. Third-party
> data sources can change, restrict access or stop responding without notice.

## What the library does

quantsumore is a Python library for retrieving financial data and performing calculations with it. It combines provider-specific data clients with local analysis tools and a desktop inflation calculator.

For example, you can request a stock's historical prices, receive them as a table, calculate RSI from those prices, and save the result as a CSV. You can also retrieve CPI index values and use their ratio to translate a dollar amount between two periods.

| Component | What you supply | What it does and returns |
| --- | --- | --- |
| Equity client | A ticker such as AAPL and, for history, start/end dates | Retrieves provider-reported prices, company information and historical price tables. Legacy methods also expose financial statements, dividends, statistics and IPO data. |
| Forex client | A currency pair such as EURUSD and an amount or date range | Retrieves exchange-rate data and calculates currency conversions. Daily conversion results include the provider's observation date. |
| Cryptocurrency client | A coin slug such as bitcoin, with optional exchange/currency filters | Retrieves market-pair quotes across trading venues and historical OHLCV tables. |
| Treasury client | A year or month | Retrieves U.S. Treasury bill rates and yield-curve tables, or summary dictionaries. |
| CPI client and calculator | An amount, original/target years and a month | Retrieves the CPI-U all-items index and calculates inflation-adjusted monetary amounts. A Tk desktop interface exposes these calculations. |
| Technical analysis: `tAnalysis(data)` | A table of one security's historical prices and volume | Calculates indicators locally, returns result tables and offers plotting methods. |
| Fundamental analysis: `fAnalysis` | A ticker/reporting period, with statements available from its engine | Holds statements for the selected company, calculates financial ratios and common-size/vertical analyses, and exports Excel workbooks. |

A **ticker** identifies a security; a **coin slug** is a provider identifier such as bitcoin. A **DataFrame** is a pandas table with labeled rows and columns. Client methods return dictionaries, DataFrames or, for some legacy methods, other documented structures. Use `type(result)` and inspect the returned fields before combining datasets.

The clients retrieve observations from external services. The indicator, ratio, inflation-adjustment and spreadsheet-export calculations run in Python. The package does not make its heuristic buy/sell labels into validated trading predictions.

## Candidate status and requirements

- Display tag: **v3.0.0-beta.3**; Python package version: **3.0.0b3**.
- Version-specific documentation and image links target that tag and resolve when it is published. For an unpublished checkout, use the local installation below; the corresponding documentation and images are present under `docs/` and `assets/`.
- The recorded environment is **Windows x64, native CPython 3.13**. Package metadata requires `>=3.13,<3.14`. Other operating systems are not covered by that validation.
- The abandoned quantsumore project-key service is removed. No project API key or relay account is required.
- Prices, FX rates, CPI values and yields have different units and reporting schedules. "Latest" means the provider's latest returned observation; inspect its currency and timestamp.
- Live checks cover selected equity quote/profile/history calls, daily FX conversion, crypto market pairs, Treasury rates and CPI. Other legacy endpoints and every fundamental-analysis method are not comprehensively verified.

See the retirement policy in [ARCHIVED.md](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/ARCHIVED.md).

## Install for local evaluation

The following commands use native Windows CPython from an **MSYS2 UCRT64** terminal. Create a virtual environment once, from the source checkout:

```sh
py -3.13 --version
py -3.13 -m venv .venv
```

If the Windows Python launcher is unavailable, invoke your native CPython 3.13 executable in place of `py -3.13`.

Install the recorded dependency snapshot and this local candidate:

```sh
.venv/Scripts/python.exe -m pip install -r requirements-runtime.txt
.venv/Scripts/python.exe -m pip install --no-deps .
```

The snapshot is provided for reproducibility. Pinning only quantsumore's version does not pin all of its dependencies.

**After publication**, the package version can instead be requested explicitly from PyPI inside a Python 3.13 environment:

```sh
.venv/Scripts/python.exe -m pip install --upgrade quantsumore==3.0.0b3
```

For the examples below, start the interpreter with `.venv/Scripts/python.exe`, or save a Python example as `demo.py` and run `.venv/Scripts/python.exe demo.py`. The indicator calculations use NumPy/pandas; TA-Lib is used for development verification, not required for normal use.

## First example: calculate RSI without a network request

This creates **invented prices**, so it works without a data provider or CSV file. OHLCV means open, high, low, close and volume for each observation.

```python
import pandas as pd
from quantsumore.analysis import tAnalysis

close = [100 + 0.2 * i + (i % 5 - 2) * 0.1 for i in range(60)]
prices = pd.DataFrame({
    "Date": pd.date_range("2024-01-01", periods=60, freq="B"),
    "Open": close,
    "High": [price + 1 for price in close],
    "Low": [price - 1 for price in close],
    "Close": close,
    "Volume": [1000 + 10 * i for i in range(60)],
    "Symbol": "DEMO",
})

analysis = tAnalysis(prices)
rsi = analysis.RelativeStrengthIndex(period=14).get_rsi()
print(rsi.tail())
```

`period=14` counts observations, not calendar days. Early rows contain NaN while the indicator accumulates enough history; these are intentional warm-up gaps.

### Using your own CSV

Provide Date (or Timestamp), Open, High, Low, Close and Volume columns. Include Symbol, or pass `ticker="AAPL"` to supply it. A partial `column_map` can map your column names to these standard names.

```python
import pandas as pd
from quantsumore.analysis import tAnalysis

prices = pd.read_csv("prices.csv")
analysis = tAnalysis(prices, ticker="AAPL")
result = analysis.MACD().get_macd()
print(result.tail())
```

Use one security per analysis object. If multiple symbols are present, the constructor selects rows for the first symbol; filter the input deliberately before analysis. Numeric fields must convert to numbers, dates must parse, and enough distinct dates must be present for the selected indicator.

### Available indicator methods

| Method | Calculation |
| --- | --- |
| `DirectionalMovementIndex()` | Positive/negative directional indicators and ADX trend-strength values |
| `AroonIndicator()` | Aroon Up/Down from recent high/low positions |
| `OnBalanceVolume()` | Cumulative signed volume |
| `AccumulationDistributionLine()` | Cumulative price/volume money-flow measure |
| `MACD()` | Fast/slow exponential-average difference, signal line and histogram |
| `RelativeStrengthIndex()` | Wilder-smoothed relative strength |
| `FastStochasticOscillator()` | Position of close within the recent price range, with smoothing |
| `MovingAveragesAndBollingerBands()` | SMA, EMA and population-deviation bands |
| `AverageTrueRange()` | Wilder-smoothed true range |

Each method returns an indicator object. Its getter, such as `get_rsi()` or `get_macd()`, returns a DataFrame. Plotting methods such as `plot_rsi()` require a suitable display backend.

## Retrieve live data

These examples need internet access. Results and availability depend on the provider; a successful request is not a promise that an endpoint will continue working.

The prepared routes use Yahoo Finance for prices, StockAnalysis for company profiles, Nasdaq for several legacy company endpoints, MTFX for currency rates, CoinMarketCap for cryptocurrency market pairs, FRED for CPI and the U.S. Treasury for government rates. The clients turn those providers' responses into Python objects; provider formats and access rules remain outside quantsumore's control.

### Stock quotes and price history

```python
from datetime import date, timedelta
from quantsumore.api import equity

quote = equity.Latest(ticker="AAPL")
print(quote["Ticker"], quote["Price"], quote["Currency"], quote["quoteTimeUTC"])

end = date.today()
prices = equity.Historical(
    ticker="AAPL",
    start=str(end - timedelta(days=365)),
    end=str(end),
)
print(prices.head())
```

`quote` is a dictionary. `prices` is a DataFrame that can be passed to `tAnalysis(prices)` or saved with `prices.to_csv("aapl_history.csv", index=False)`. Historical data may contain a Timestamp column, which the analysis constructor recognizes as Date.

### Currency conversion, crypto market pairs and Treasury rates

```python
from datetime import date
from quantsumore.api import forex, crypto, treasury

conversion = forex.CurrencyConversion(currency_pair="EURUSD", conversion_amount=100)
print(conversion)

market_pairs = crypto.Latest(slug="bitcoin", limit=1)
print(market_pairs.head())

yield_curve = treasury.Yield(period=date.today().year, full_table=True)
print(yield_curve.tail())
```

EURUSD means euros converted to U.S. dollars. Crypto market-pair rows describe particular venues and trading pairs; check each row's currency/exchange fields. Treasury methods offer a full table or a summary according to their arguments; interpret rates using the returned labels and provider definitions.

### CPI and inflation adjustment

```python
from quantsumore.api import cpi

calculator = cpi.CPI_U.InflationAdjustment
print(calculator.data.tail())
print(calculator.data.attrs)
adjusted = calculator.select(100, 2000, 2024, month_input="July")
print(adjusted)
```

The CPI value is an **index level**, not an inflation percentage. The calculation is original amount × target CPI ÷ original CPI, rounded to two decimal places. Fetch the calculator once and reuse it; each new `InflationAdjustment` access downloads data.

The default series is FRED CPIAUCNS, an all-items U.S. city-average CPI-U index that is not seasonally adjusted. Provenance in `data.attrs` includes the requested series, source URL, fetch time and latest observation date. The displayed `series_id` column retains a legacy internal identifier for compatibility; use the attrs for the actual source series.

Missing requested months fall back to yearly averages. Those averages use available observations, so an incomplete year's average is a partial-year value. See [live CPI details](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/CPI_LIVE.md) for retrieval timeouts, error handling and data conventions.

### Desktop inflation calculator

```python
from quantsumore.gui import GUI
GUI.run()
```

This opens a Tk application with adjusted-value, current-year and year-comparison tabs. It needs Tkinter and a desktop display. Importing `quantsumore.gui` fetches live CPI before the window is created; provider errors can therefore prevent startup.

## Financial statements, ratios and Excel output

`fAnalysis` is a supplied analyzer **instance**, holding the currently selected company's statements. Calling it again changes that loaded company/period. The financial-statement engine is provider-dependent and is outside the comprehensive live-coverage claim above.

For a legacy endpoint that returns the required statements:

```python
from quantsumore.analysis import fAnalysis

fAnalysis("AAPL", "Annual")
print(fAnalysis.income_statement)
print(fAnalysis.current_ratio())
common_size = fAnalysis.CommonSize("Income Statement")
print(common_size)
fAnalysis.writeStatement("statements.xlsx", include_common_size=True)
```

Ratios include liquidity, profitability, leverage and turnover measures. A common-size statement adds percentages relative to a base figure; vertical analysis returns formatted percentage values. These calculations run locally after the engine supplies the data. Missing datasets or account labels can prevent a calculation, and exports require the expected statement structure.

## Reference data and CryptoConfig

Bundled ticker/crypto reference files help translate symbols, coin slugs and exchange identifiers into provider requests. They are frozen lookup snapshots, distinct from live prices. Core imports copy missing reference files locally without downloading replacements. Each file becomes visible only after its copy is complete, and concurrent imports preserve files already created by another process or user. The GUI entry is the live-fetch exception described above.

The internal `CryptoConfig` helper refreshes SQLite metadata transactionally. Its `snapshot()` method returns asset, exchange and currency collections from one consistent read. Returned data is copied; editing a returned list does not change the stored metadata. Use [the CryptoConfig guide](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/CRYPTO_CONFIG.md) before customizing this workflow.

Custom `db_directory` paths may contain periods, such as `cache.v1`; missing directories are created when opening the database. To select an explicit database-file path, pass it as `db_filename`.

## Errors and current limits

- Provider calls can raise `APIRequestError`. Live CPI retrieval uses `CPIDataUnavailableError` and retains the original exception in `__cause__`.
- Unavailable statements/dividends can raise dataset-specific exceptions. Some legacy calculations return None or print a diagnostic when required values are unavailable.
- Corrected numerical indicators can differ from 3.0.0b2. Recompute stored results and review thresholds when evaluating an upgrade.
- Buy/sell, divergence and support/resistance labels are legacy heuristics. Numerical indicator accuracy does not establish predictive performance.
- No unsupported endpoint repair, dependency upgrade or platform compatibility is promised after this corrective archive.

## Further reading

- [Migration from 3.0.0b2](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/MIGRATION.md)
- [GUI behavior](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/GUI.md)
- [Release history](https://doydl.studio/pages/open-source/quantsumore/changelog/)
- [Retirement policy](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/ARCHIVED.md)
- [Security policy](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/SECURITY.md)
- [Apache License 2.0](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/LICENSE)

## Legal and data-use information

quantsumore is independent of the financial institutions and data providers it accesses. Retrieved data belongs to the respective providers. Verify it independently and review each provider's terms, including restrictions on commercial use. The source-code license does not grant rights to third-party data.

quantsumore is provided "as is", without warranty of any kind, express or implied. No warranties are made concerning merchantability, fitness for a particular purpose, or non-infringement of the data. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.
