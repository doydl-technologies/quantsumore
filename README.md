<p align="center">
  <img src="https://raw.githubusercontent.com/cedricmoorejr/defunct-quantsumore/main/gui/assets/quantsumore_logo.png" alt="quantsumore Logo" width="700"/>
</p>




# 🚀 Power Up Your Financial Analysis with quantsumore

---

> [!WARNING]
> **This project is no longer maintained.** No further updates, compatibility fixes,
> endpoint repairs, or security fixes are planned. Because `quantsumore` relies on
> third-party data sources, functionality may stop working without notice.

---

<table border=1 cellpadding=10 width="100%"><tr><td>

<div align="center">

### ⚠️ **LEGAL DISCLAIMER** ⚠️

</div>

**quantsumore** is an API client that enables access to data from various sources.

🔴 **Note the following critical information**:

---

### Important Information

👉 `quantsumore` is an independent Python library designed to provide users with access to market data across various financial instruments. The library is not associated with, endorsed by, or affiliated with any financial institutions or data providers. All data accessed through quantsumore is owned and disseminated by respective data providers.

Users are advised to independently verify the accuracy of the data obtained via quantsumore and should base investment decisions on their own judgment supplemented by professional advice. The developers of quantsumore disclaim all responsibility for any inaccuracies, errors, or omissions in the data provided.

---

### No Warranty

👉 `quantsumore` is provided "as is", without warranty of any kind, express or implied. No warranties are made concerning the merchantability, fitness for a particular purpose, or non-infringement of the data. In no event shall the authors or copyright holders be liable for any claim, damages, or other liability, whether in an action of contract, tort or otherwise, arising from, out of, or in connection with the software or the use or other dealings in the software.

---

### Personal Use

👉 Please note that the APIs are intended primarily for personal and non-commercial use. Users should refer to the individual terms of use for guidelines on commercial applications.


</td></tr></table>





### Summary of the `quantsumore` Library

[![Downloads](https://static.pepy.tech/badge/quantsumore)](https://pepy.tech/project/quantsumore)
[![Downloads](https://static.pepy.tech/badge/quantsumore/month)](https://pepy.tech/project/quantsumore)
[![Downloads](https://static.pepy.tech/badge/quantsumore/week)](https://pepy.tech/project/quantsumore)
![Static Badge](https://img.shields.io/badge/status-unmaintained-red)

The `quantsumore` library is a comprehensive Python package designed for retrieving and analyzing a wide range of financial market data. It provides specialized API clients to fetch data from various financial markets, including cryptocurrencies, equities, Forex, Treasury instruments, and Consumer Price Index (CPI) metrics. Below is an overview of the key API clients and their functionalities.

## Table of Contents
- [Installation](#installation)
- [Using the `quantsumore` API Clients](#using-the-quantsumore-api-clients)
  - [Cryptocurrency Data](#cryptocurrency-data)
  - [Consumer Price Index (CPI)](#consumer-price-index-cpi)
  - [Equity and Stock Data](#equity-and-stock-data)
  - [Forex Data](#forex-data)
  - [Treasury Data](#treasury-data)
- [Introduction to Financial Analysis](#introduction-to-financial-analysis)
  - [Setting Up Financial and Technical Analysis](#setting-up-financial-and-technical-analysis)
  - [Using Financial Statements, Ratios, and Indicators](#using-financial-statements-ratios-and-indicators)
  - [Examples of Financial and Technical Analysis Applications](#examples-of-financial-and-technical-analysis-applications)

# Installation
To start using the `quantsumore` API clients for financial data analysis, follow these steps to install the package.

### Installing the `quantsumore` Package

You can install `quantsumore` directly from PyPI using `pip`. Open your terminal and run the following command:

```bash
pip install quantsumore
```

This will install the `quantsumore` package along with any required dependencies.


# Using the `quantsumore` API Clients
## Cryptocurrency Data

The `crypto` API client allows users to easily fetch both real-time and historical cryptocurrency market data.

### Importing the Cryptocurrency API Client

```python
from quantsumore.api import crypto
```

### Fetching Latest Cryptocurrency Data

```python
# Fetch the latest market data for Bitcoin in USD from Binance
latest_data = crypto.Latest(slug="bitcoin", baseCurrencySymbol="USD", quoteCurrencySymbol="JPY", cryptoExchange="binance", limit=100, exchangeType="all")
print(latest_data)
```

### Fetching Historical Cryptocurrency Data

```python
# Fetch historical data for Bitcoin from January 1, 2024, to January 10, 2024
historical_data = crypto.Historical(slug="bitcoin", start="2024-01-01", end="2024-01-10")
print(historical_data)
```

<br>

## Consumer Price Index (CPI)

The `cpi` API client allows users to fetch CPI data for all urban consumers and perform inflation adjustments.

### Importing the CPI API Client

```python
from quantsumore.api import cpi
```

### Accessing CPI Data

```python
# Access CPI data for all urban consumers
cpi_data = cpi.CPI_U.InflationAdjustment.data
print(cpi_data)
```

### Performing Inflation Adjustments

```python
# Adjust $100 from the year 2000 to its equivalent in 2024
adjusted_value = cpi.CPI_U.InflationAdjustment.select(original_amount=100, original_year=2000, target_year=2024, month_input="July")
print(f"Adjusted value: ${adjusted_value}")
```

<br>

## Equity and Stock Data

The `equity` API client provides users with tools to fetch company information, financial stats, and both real-time and historical stock price data.

### Importing the Equity API Client

```python
from quantsumore.api import equity
```
### Fetching Company Information

```python
# Fetch company bio for Apple Inc.
company_bio = equity.Profile.bio(ticker="AAPL")
print(company_bio)
```

### Fetching Latest Stock Price

```python
# Fetch the latest stock price for Apple Inc.
latest_price = equity.Latest(ticker="AAPL")
print(f"Latest stock price for AAPL: {latest_price}")
```

### Fetching Historical Stock Price Data

```python
# Fetch historical stock price data for Apple from January 1, 2024, to January 10, 2024
historical_data = equity.Historical(ticker="AAPL", start="2024-01-01", end="2024-01-10")
print(historical_data)
```

<br>

## Forex Data

The `forex` API client allows users to fetch Forex-related data, including exchange rates, currency conversions, and interbank rates.

### Importing the Forex API Client

```python
from quantsumore.api import forex
```
### Currency Conversion

```python
# Convert 100 Euros to USD based on the latest conversion rates
conversion_data = forex.CurrencyConversion(currency_pair="EURUSD", conversion_amount=100)
print(conversion_data)
```


### Fetching Historical Exchange Rates

```python
# Fetch historical exchange rates for EUR/USD from January 1, 2024, to January 10, 2024
historical_data = forex.Historical(currency_pair="EURUSD", start="2024-01-01", end="2024-01-10")
print(historical_data)
```

<br>

## Treasury Data

The `treasury` API client enables users to fetch U.S. Treasury-related data, including bill rates and yield curves.

### Importing the Treasury API Client

```python
from quantsumore.api import treasury
```

### Fetching Treasury Bill Rates

```python
# Fetch the latest Treasury bill rates for the current year
tbill_rates = treasury.TBill(period="CY")
print(tbill_rates)
```

### Fetching Daily Treasury Yield Curve Rates

```python
# Fetch the latest yield curve rates for the year 2023
yield_rates = treasury.Yield(period=2023)
print(yield_rates)
```

---

# Introduction to Financial Analysis

The `fAnalysis` and `tAnalysis` classes, provided by the `quantsumore` library, offer comprehensive tools for conducting both fundamental and technical analysis of financial data. These modules allow users to explore a company's financial health through statements and ratios (fundamental analysis) and detect market trends, potential buy/sell signals, and volatility through technical indicators (technical analysis).

This guide will show you how to:
- Access financial statements, ratios, and common size financial statements.
- Compute technical indicators such as RSI, MACD, DMI, and Bollinger Bands.

### Setting Up Financial and Technical Analysis

#### Importing and Initializing `fAnalysis` (Fundamental Analysis)
```python
from quantsumore.analysis import fAnalysis
```

#### Importing and Initializing `tAnalysis` (Technical Analysis)

Next, initialize the `tAnalysis` class with your financial data for technical analysis:

```python
import pandas as pd
import numpy as np
from quantsumore.analysis import tAnalysis

# Sample data setup
data = pd.DataFrame({
    'Date': pd.date_range(start='2020-01-01', periods=100),
    'High': np.random.rand(100) * 100 + 150,
    'Low': np.random.rand(100) * 100 + 100,
    'Open': np.random.rand(100) * 100 + 125,
    'Close': np.random.rand(100) * 100 + 130,
    'Volume': np.random.randint(100, 1000, size=100),
    'Symbol': ['AAPL'] * 100
})

# Initialize the tAnalysis class
analyze = tAnalysis(data)
```

### Using Financial Statements, Ratios, and Indicators

#### Overview of Methods and Indicators

##### Fundamental Analysis with `fAnalysis`
`fAnalysis` provides a wide range of methods for accessing and analyzing financial data:
- **Financial Statements**: Income statement, balance sheet, cash flow statement.
- **Liquidity Ratios**: Current ratio, quick ratio, cash ratio.
- **Solvency Ratios**: Debt-to-equity ratio, debt-to-capital ratio.
- **Profitability Indicators**: Net profit margin, gross profit margin, operating profit margin.
- **Efficiency Ratios**: Inventory turnover ratio, receivables turnover ratio.
- **Common Size Statements**: Convert statements into common-size formats for easier comparison.

##### Technical Analysis with `tAnalysis`
`tAnalysis` offers methods to compute various technical indicators:
- **Directional Movement Index (DMI) & Average Directional Index (ADX)**: Trend strength indicators.
- **Aroon Indicator**: Trend detection.
- **On Balance Volume (OBV)**: Volume analysis for price movements.
- **Accumulation/Distribution Line (A/D Line)**: Volume and price trends.
- **MACD**: Momentum and trend-following indicator.
- **RSI**: Overbought/oversold conditions.
- **Stochastic Oscillator**: Market momentum and sensitivity.
- **Moving Averages & Bollinger Bands**: Trend analysis and volatility bands.
- **ATR**: Volatility measure.

### Examples of Financial and Technical Analysis Applications

#### Fundamental Analysis Examples

##### Accessing Financial Statements

```python
# Fetch financial data for a specific ticker and period
fAnalysis('AAPL', 'Q')

# Access the balance sheet and income statement
income_statement = fAnalysis.income_statement
balance_sheet = fAnalysis.balance_sheet
```

##### Calculating Financial Ratios

```python
# Calculate key financial ratios
current_ratio = fAnalysis.current_ratio()
debt_to_equity_ratio = fAnalysis.debt_to_equity_ratio()

print(f"Current Ratio: {current_ratio}")
print(f"Debt to Equity Ratio: {debt_to_equity_ratio}")
```

##### Dividend Analysis

```python
# Access dividend data if available
dividend_yield = fAnalysis.dividend_yield()
print(f"Dividend Yield: {dividend_yield}")
```

##### Generating Common Size Financial Statements

```python
# Convert the income statement to a common size statement
common_size_income = fAnalysis.CommonSize("Income Statement")
print(common_size_income)
```

#### Technical Analysis Examples

##### Computing and Visualizing DMI and ADX

```python
# Compute DMI and ADX
dmi = analyze.DirectionalMovementIndex(period=14, adx_threshold=25)
dmi.plot_indicators()
```

##### Using the Aroon Indicator

```python
# Compute Aroon and plot
aroon = analyze.AroonIndicator(period=25)
aroon.plot_aroon()
```

##### Evaluating Market Volume with OBV

```python
# Compute On Balance Volume and detect divergences
obv = analyze.OnBalanceVolume()
obv.plot_obv_with_divergence()
```

##### Analyzing Price and Volume with the Accumulation/Distribution Line

```python
# Compute A/D Line and plot
adl = analyze.AccumulationDistributionLine()
adl.plot_ad_line_with_divergence()
```

##### MACD for Trend Following

```python
# Compute MACD and visualize
macd = analyze.MACD()
macd.plot_macd()
```

##### Identifying Overbought or Oversold Conditions with RSI

```python
# Compute RSI and plot
rsi = analyze.RelativeStrengthIndex()
rsi.plot_rsi()
```

##### Fast Stochastic Oscillator for Sensitivity to Market Movements

```python
# Compute Stochastic Oscillator
stochastic = analyze.FastStochasticOscillator()
stochastic.plot_stochastic()
```

##### Combining Moving Averages and Bollinger Bands for Trend Analysis

```python
# Compute and plot SMA, EMA, and Bollinger Bands
mabb = analyze.MovingAveragesAndBollingerBands()
mabb.plot_indicators()
```

##### Using ATR to Assess Market Volatility

```python
# Compute ATR and visualize
atr = analyze.AverageTrueRange()
atr.plot_atr()
```
---



