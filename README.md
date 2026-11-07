 
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-light.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-dark.png">
    <img src="https://raw.githubusercontent.com/doydl-technologies/quantsumore/v3.0.0-beta.3/assets/png/quantsumore-endorsed-lockup-dark.png" alt="quantsumore — powered by DOYDL Technologies" width="700">
  </picture>
</p>

# 📦 quantsumore — Retired

> [!WARNING]
> **🛑 This project was retired on July 27, 2025, and remains unsupported.**
>
> Version **3.0.0b3** is a one-time corrective archival candidate, not a resumption of maintenance.
>
> After this correction, no further releases, compatibility fixes, endpoint repairs, support, or security updates are planned. Issues and pull requests are not being accepted.
>
> **⚠️ Important:** Use the archive to understand or reproduce legacy workflows. Do not rely on it for production systems, security-sensitive workloads, or financial decisions.
>
> Third-party data sources can change, restrict access, or stop responding without notice.

## 🔎 What the library does

**quantsumore** is a Python library for retrieving financial data and performing calculations with it.

It combines provider-specific data clients with local analysis tools and a desktop inflation calculator.

**💡 Example workflow**

You can request a stock's historical prices, receive them as a table, calculate RSI from those prices, and save the result as a CSV.

You can also retrieve CPI index values and use their ratio to translate a dollar amount between two periods.

### 🧰 Available components

| Component | What you supply | What it does and returns |
| --- | --- | --- |
| 📈 **Equity client** | A ticker such as AAPL and, for history, start/end dates | Retrieves provider-reported prices, company information and historical price tables. Legacy methods also expose financial statements, dividends, statistics and IPO data. |
| 💱 **Forex client** | A currency pair such as EURUSD and an amount or date range | Retrieves exchange-rate data and calculates currency conversions. Daily conversion results include the provider's observation date. |
| 🪙 **Cryptocurrency client** | A coin slug such as bitcoin, with optional exchange/currency filters | Retrieves market-pair quotes across trading venues and historical OHLCV tables. |
| 🏛️ **Treasury client** | A year or month | Retrieves U.S. Treasury bill rates and yield-curve tables, or summary dictionaries. |
| 💵 **CPI client and calculator** | An amount, original/target years and a month | Retrieves the CPI-U all-items index and calculates inflation-adjusted monetary amounts. A Tk desktop interface exposes these calculations. |
| 📊 **Technical analysis: `tAnalysis(data)`** | A table of one security's historical prices and volume | Calculates indicators locally, returns result tables and offers plotting methods. |
| 🧮 **Fundamental analysis: `fAnalysis`** | A ticker/reporting period, with statements available from its engine | Holds statements for the selected company, calculates financial ratios and common-size/vertical analyses, and exports Excel workbooks. |

### 📖 A few useful definitions

- **Ticker:** Identifies a security, such as `AAPL`.
- **Coin slug:** A provider identifier, such as `bitcoin`.
- **DataFrame:** A pandas table with labeled rows and columns.

Client methods return dictionaries, DataFrames or, for some legacy methods, other documented structures.

Use `type(result)` and inspect the returned fields before combining datasets.

**⚙️ How calculations work**

The clients retrieve observations from external services. The indicator, ratio, inflation-adjustment and spreadsheet-export calculations run in Python.

> **⚠️ Trading disclaimer:** The package does not make its heuristic buy/sell labels into validated trading predictions.

---

## 🏷️ Candidate status and requirements

- 🏷️ **Version:** Display tag `v3.0.0-beta.3`; Python package version `3.0.0b3`.
- 📚 **Documentation:** Version-specific documentation and image links target that tag and resolve when it is published. For an unpublished checkout, use the local installation below; corresponding documentation and images are under `docs/` and `assets/`.
- 🖥️ **Validated environment:** Windows x64, native CPython 3.13. Package metadata requires `>=3.13,<3.14`. Other operating systems are not covered by that validation.
- 🔓 **Authentication:** The abandoned quantsumore project-key service has been removed. No project API key or relay account is required.
- 🕒 **Data freshness:** Prices, FX rates, CPI values and yields have different units and reporting schedules. "Latest" means the provider's latest returned observation; inspect its currency and timestamp.
- 🧪 **Live verification:** Selected equity quote/profile/history calls, daily FX conversion, crypto market pairs, Treasury rates and CPI have been checked. Other legacy endpoints and every fundamental-analysis method are not comprehensively verified.

📄 See the complete retirement policy in [ARCHIVED.md](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/ARCHIVED.md).

---

## ⚙️ Install for local evaluation

The following commands use native Windows CPython from an **MSYS2 UCRT64** terminal.

### 1️⃣ Create a virtual environment

From your source checkout:

```sh
py -3.13 --version
py -3.13 -m venv .venv
```

If the Windows Python launcher is unavailable, invoke your native CPython 3.13 executable in place of `py -3.13`.

### 2️⃣ Install dependencies and the local candidate

```sh
.venv/Scripts/python.exe -m pip install -r requirements-runtime.txt
.venv/Scripts/python.exe -m pip install --no-deps .
```

**📌 Dependency note:** The snapshot is provided for reproducibility. Pinning only quantsumore's version does not pin all of its dependencies.

### 3️⃣ Install from PyPI after publication

**After publication**, the package version can instead be requested explicitly from PyPI inside a Python 3.13 environment:

```sh
.venv/Scripts/python.exe -m pip install --upgrade quantsumore==3.0.0b3
```

### ▶️ Run the examples

For the examples below, start the interpreter with:

```sh
.venv/Scripts/python.exe
```

Alternatively, save an example as `demo.py` and run:

```sh
.venv/Scripts/python.exe demo.py
```

The indicator calculations use NumPy/pandas. TA-Lib is used for development verification, not required for normal use.

---

## 🐍 First example: Calculate RSI without a network request

This example creates **invented prices**, so it works without a data provider or CSV file.

**📖 OHLCV** means open, high, low, close and volume for each observation.

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

**💡 Understanding the result**

`period=14` counts observations, not calendar days.

Early rows contain `NaN` while the indicator accumulates enough history. These are intentional warm-up gaps.

### 📂 Using your own CSV

Provide the following columns:

- `Date` (or `Timestamp`)
- `Open`, `High`, `Low`, `Close`
- `Volume`
- `Symbol` (or pass `ticker="AAPL"`)

A partial `column_map` can map your column names to these standard names.

```python
import pandas as pd
from quantsumore.analysis import tAnalysis

prices = pd.read_csv("prices.csv")
analysis = tAnalysis(prices, ticker="AAPL")
result = analysis.MACD().get_macd()
print(result.tail())
```

**⚠️ Data requirements**

Use one security per analysis object. If multiple symbols are present, the constructor selects rows for the first symbol; filter the input deliberately before analysis.

Numeric fields must convert to numbers, dates must parse, and enough distinct dates must be present for the selected indicator.

### 📊 Available indicator methods

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

Each method returns an indicator object.

Its getter, such as `get_rsi()` or `get_macd()`, returns a DataFrame.

**📉 Visualization:** Plotting methods such as `plot_rsi()` require a suitable display backend.

---

## 🌐 Retrieve live data

These examples require an internet connection.

> **⚠️ Provider availability:** Results and availability depend on the provider. A successful request does not guarantee an endpoint will continue working.

### 🔌 External data providers

| Provider | Data |
| --- | --- |
| 📈 Yahoo Finance | Stock prices |
| 🏢 StockAnalysis | Company profiles |
| 📑 Nasdaq | Several legacy company endpoints |
| 💱 MTFX | Currency rates |
| 🪙 CoinMarketCap | Cryptocurrency market pairs |
| 💵 FRED | Consumer Price Index |
| 🏛️ U.S. Treasury | Government rates |

The clients turn those providers' responses into Python objects.

Provider formats and access rules remain outside quantsumore's control.

### 📈 Stock quotes and price history

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

**📋 Understanding the output**

- `quote` is a dictionary.
- `prices` is a DataFrame.
- Historical data may contain a `Timestamp` column, which the analysis constructor recognizes as `Date`.

You can pass the history directly into:

```python
tAnalysis(prices)
```

Or save it as a CSV:

```python
prices.to_csv("aapl_history.csv", index=False)
```

### 💱 Currency conversion, crypto market pairs and Treasury rates

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

**💡 Important details**

- 💱 **Forex:** `EURUSD` means euros converted to U.S. dollars.
- 🪙 **Cryptocurrency:** Market-pair rows describe particular venues and trading pairs. Check each row's currency/exchange fields.
- 🏛️ **Treasury:** Methods offer a full table or summary according to their arguments. Interpret rates using returned labels and provider definitions.

### 💵 CPI and inflation adjustment

```python
from quantsumore.api import cpi

calculator = cpi.CPI_U.InflationAdjustment
print(calculator.data.tail())
print(calculator.data.attrs)
adjusted = calculator.select(100, 2000, 2024, month_input="July")
print(adjusted)
```

**🧮 How the calculation works**

The CPI value is an **index level**, not an inflation percentage.

Inflation-adjusted amounts use:

**Adjusted amount = Original amount × Target CPI ÷ Original CPI**

The result is rounded to two decimal places.

**⚡ Performance tip:** Fetch the calculator once and reuse it. Each new `InflationAdjustment` access downloads data.

**📊 Data source and conventions**

The default series is FRED `CPIAUCNS`, an all-items U.S. city-average CPI-U index that is not seasonally adjusted.

Provenance in `data.attrs` includes:

- Requested series
- Source URL
- Fetch time
- Latest observation date

The displayed `series_id` column retains a legacy internal identifier for compatibility. Use the attrs for the actual source series.

**⚠️ Missing months:** Missing requested months fall back to yearly averages. Those averages use available observations, so an incomplete year's average is a partial-year value.

📚 See [live CPI details](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/CPI_LIVE.md) for retrieval timeouts, error handling and data conventions.

### 🖥️ Desktop inflation calculator

```python
from quantsumore.gui import GUI
GUI.run()
```

This opens a Tk application with three interfaces:

- 💵 Adjusted-value calculations
- 📅 Current-year calculations
- 📊 Year-comparison calculations

**⚠️ Requirements:** Tkinter and a desktop display are required.

Importing `quantsumore.gui` fetches live CPI before the window is created. Provider errors can therefore prevent startup.

---

## 🧮 Financial statements, ratios and Excel output

`fAnalysis` is a supplied analyzer **instance**, holding the currently selected company's statements.

Calling it again changes that loaded company/period.

> **⚠️ Coverage note:** The financial-statement engine is provider-dependent and is outside the comprehensive live-coverage claim above.

### 🐍 Example: Financial statement analysis

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

### 📊 Supported analysis categories

- 💧 **Liquidity ratios:** Measures of short-term financial obligations.
- 📈 **Profitability ratios:** Measures of earnings performance.
- ⚖️ **Leverage ratios:** Measures related to debt and financial structure.
- 🔄 **Turnover ratios:** Measures of operational efficiency.
- 📑 **Common-size statements:** Percentages relative to a base figure.
- 📐 **Vertical analysis:** Formatted percentage values.
- 📗 **Excel exports:** Statement data written into workbooks.

These calculations run locally after the engine supplies the data.

**⚠️ Limitations:** Missing datasets or account labels can prevent a calculation, and exports require the expected statement structure.

---

## 🗃️ Reference data and CryptoConfig

Bundled ticker/crypto reference files help translate symbols, coin slugs and exchange identifiers into provider requests.

These are **frozen lookup snapshots**, distinct from live prices.

### 📂 Local reference files

Core imports copy missing reference files locally without downloading replacements.

- ✅ Each file becomes visible only after its copy is complete.
- ✅ Concurrent imports preserve files already created by another process or user.
- 🌐 The GUI entry is the live-fetch exception described earlier.

### 🪙 CryptoConfig metadata

The internal `CryptoConfig` helper refreshes SQLite metadata transactionally.

Its `snapshot()` method returns asset, exchange and currency collections from one consistent read.

**🔒 Data isolation:** Returned data is copied. Editing a returned list does not change stored metadata.

📚 Read [the CryptoConfig guide](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/CRYPTO_CONFIG.md) before customizing this workflow.

### ⚙️ Database paths

Custom `db_directory` paths may contain periods, such as `cache.v1`.

Missing directories are created when opening the database.

To select an explicit database-file path, pass it as `db_filename`.

---

## ⚠️ Errors and current limits

### 🚨 Error handling

- **API requests:** Provider calls can raise `APIRequestError`.
- **CPI retrieval:** Live CPI retrieval uses `CPIDataUnavailableError` and retains the original exception in `__cause__`.
- **Financial datasets:** Unavailable statements or dividends can raise dataset-specific exceptions.
- **Legacy calculations:** Some methods return `None` or print diagnostics when required values are unavailable.

### 🧪 Numerical compatibility

Corrected numerical indicators can differ from `3.0.0b2`.

**📌 Recommendation:** Recompute stored results and review thresholds when evaluating an upgrade.

### 📉 Trading signal limitations

Buy/sell, divergence and support/resistance labels are legacy heuristics.

Numerical indicator accuracy does not establish predictive performance.

### 🛑 End of maintenance

No unsupported endpoint repair, dependency upgrade or platform compatibility is promised after this corrective archive.

---

## 📚 Further reading

- 🔄 [Migration from 3.0.0b2](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/MIGRATION.md)
- 🖥️ [GUI behavior](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/docs/GUI.md)
- 🕘 [Release history](https://doydl.studio/pages/open-source/quantsumore/changelog/)
- 🗄️ [Retirement policy](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/ARCHIVED.md)
- 🔐 [Security policy](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/SECURITY.md)
- ⚖️ [Apache License 2.0](https://github.com/doydl-technologies/quantsumore/blob/v3.0.0-beta.3/LICENSE)

---

## ⚖️ Legal and data-use information

### 🏛️ Independence and third-party data

quantsumore is independent of the financial institutions and data providers it accesses.

Retrieved data belongs to the respective providers.

Verify it independently and review each provider's terms, including restrictions on commercial use.

**The source-code license does not grant rights to third-party data.**

### 📜 Warranty and liability

quantsumore is provided "as is", without warranty of any kind, express or implied.

No warranties are made concerning merchantability, fitness for a particular purpose, or non-infringement of the data.

In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.
