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
import urllib.parse

__all__ = [
    "APIRequestError",    

    # CPI (Consumer Price Index) 
    "CPIError",
    "CPIDateParseError",
    "CPIDataUnavailableError",

    # Crypto 
    "CryptoPipelineError",
    "CryptoLiveQuoteError",
    "CryptoLiveQuoteNoDataError",
    "CryptoLiveQuoteUnavailableError",
    "CryptoHistoricalError",
    "CryptoHistoricalNoDataError",
    "CryptoHistoricalUnavailableError",

    # Dividend History 
    "DividendHistoryError",
    "DividendHistoryNoDataError",
    "DividendHistoryUnavailableError",

    # FX (Foreign Exchange) 
    "FXPipelineError",
    # Historical rates
    "FXHistoricalError",
    "FXNoDataError",
    "FXDataUnavailableError",
    # Interbank rates
    "FXInterbankError",
    "FXInterbankNoDataError",
    "FXInterbankDataUnavailableError",
    # Live bid/ask
    "LiveBidAskError",
    "LiveBidAskNoDataError",
    "LiveBidAskUnavailableError",
    # Live quote
    "LiveQuoteError",
    "LiveQuoteValidationError",
    "LiveQuoteUnavailableError",
    # Conversion
    "ConversionError",
    "ConversionValidationError",
    "ConversionNoDataError",    
    "ConversionUnavailableError",

    # Financials 
    "FinancialsError",
    "FinancialStatementUnavailableError",
    "FinancialDataNotLoadedError",
    "DividendDataNotLoadedError",

    # Equity (Stocks) 
    "EquityPipelineError",
    # IPO
    "IPOError",
    "IPONoDataError",
    "IPODataUnavailableError",
    # Latest price
    "LatestError",
    "LatestNoDataError",
    "LatestDataUnavailableError",
    # Historical price
    "HistoricalError",
    "HistoricalNoDataError",
    "HistoricalDataUnavailableError",
    # Last trade
    "LastTradeError",
    "LastTradeNoDataError",
    "LastTradeDataUnavailableError",
    # Quote statistics (HTML)
    "QuoteStatisticsError",
    "QuoteStatisticsValidationError",
    "QuoteStatisticsNoDataError",
    "QuoteStatisticsUnavailableError",
    # Profile (HTML)
    "CompanyProfileError",
    "CompanyProfileValidationError",
    "CompanyProfileNoDataError",
    "CompanyProfileUnavailableError",
   
    # Treasury/Yield 
    "TreasuryPipelineError",
    "TreasuryDataValidationError",
    "TreasuryNoDataError",
    "TreasuryDataUnavailableError",
    
    # Workbook Create     
    "FinancialsExportError",    
    "InvalidFinancialStatementIdentifier",    
    "NoFinancialStatementsProvided",    
    "WorkbookSaveError",        
    
    # Technical Analysis Create     
    "DataInitializationError",    
    
    # Warnings     
    "RatioCalcWarning",       

    # Tickers      
    "TickerNotFoundError",     
    "StockTickerError",          
    
    # Currency Pairs       
    'CurrencyPairError',
    'CurrencyPairNotFoundError',
    'InvalidCurrencyPairError',   
    
    # Crypto Slugs       
    "CryptoSlugError",
    "InvalidSlugTypeError",
    "CoinSlugNotFoundError",
    "CoinSlugIdMismatchError",    
]



# API Errors
   
   
class APIRequestError(RuntimeError):
    """Wrap a provider request failure while retaining its HTTP status."""
    import requests

    def __init__(self, original_exception: Exception):
        msg = str(original_exception)
        msg = re.sub(r'\s*for url:.*$', '', msg, flags=re.IGNORECASE)
        status = getattr(getattr(original_exception, "response", None), "status_code", None)
        if status:
            full_msg = f"HTTP Error {status}: {msg}"
        else:
            full_msg = msg
        super().__init__(full_msg)
        self.__cause__ = original_exception
        self.status_code = status
        
        
#  Financials Exceptions
class FinancialsError(Exception):
    """Base exception for financials-related errors."""
    pass

class FinancialStatementUnavailableError(FinancialsError):
    """
    Raised when a requested financial statement is unavailable or invalid.
    """
    pass

class FinancialDataNotLoadedError(FinancialsError):
    """
    Raised when the requested financial statement data has not been loaded.
    """
    pass

class DividendDataNotLoadedError(FinancialsError):
    """
    Raised when dividend data has not been loaded.
    """
    pass

#  Dividend Exceptions
class DividendHistoryError(Exception):
    """Base exception for dividend_history errors."""
    pass

class DividendHistoryNoDataError(DividendHistoryError):
    """
    Raised when the Nasdaq API returns no dividend data for the requested ticker(s).
    This includes cases where the ticker is delisted or the data block is missing/empty.
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{ticker}: {msg}" for ticker, msg in messages)
        super().__init__(f"No dividend data:\n{fmt}")

class DividendHistoryUnavailableError(DividendHistoryError):
    """
    Raised when, after validation and parsing, no usable dividend summary/history
    DataFrame could be produced, and there are no detailed API messages.
    """
    def __init__(self):
        super().__init__(
            "Dividend data is currently unavailable. Try again later or "
            "open an issue at https://github.com/cedricmoorejr/quantsumore."
        )

#  Statement Save Workbook Errors
class FinancialsExportError(Exception):
    """Base exception for all financial statement export errors."""
    pass

class InvalidFinancialStatementIdentifier(FinancialsExportError):
    """Raised when a provided financial statement identifier is invalid."""
    pass

class NoFinancialStatementsProvided(FinancialsExportError):
    """Raised when no valid financial statements are specified for export."""
    pass

class WorkbookSaveError(FinancialsExportError):
    """Raised when saving the workbook fails."""
    pass
   
#  Technical Analysis Errors
class DataInitializationError(Exception):
    """Raised when tAnalyze fails to initialize properly due to invalid or missing data."""
    pass
   
#  Ticker Errors
class StockTickerError(Exception):
    """Base exception for stock ticker lookup failures."""
    pass

class TickerNotFoundError(StockTickerError):
    """Raised when a stock ticker symbol cannot be found by the standard provider."""
    pass

#  Currency Pair Errors
class CurrencyPairError(Exception):
    """Base exception for currency pair lookup failures."""
    pass

class CurrencyPairNotFoundError(CurrencyPairError):
    """Raised when a currency pair cannot be found by the provider."""
    pass

class InvalidCurrencyPairError(CurrencyPairError):
    """Raised when the currency pair format is invalid."""
    pass

#  Crypto Slug Errors
class CryptoSlugError(Exception):
    """Base exception for coin slug lookup/validation failures."""
    pass

class InvalidSlugTypeError(CryptoSlugError):
    """Raised when the provided slug is not a string."""
    pass

class CoinSlugNotFoundError(CryptoSlugError):
    """Raised when the slug cannot be found or is not valid."""
    pass

class CoinSlugIdMismatchError(CryptoSlugError):
    """Raised when slug/id combination could not be resolved."""
    pass


        
#   CPI Data Pipeline Exceptions
class CPIError(Exception):
    """Base exception for all CPI data errors."""
    pass

class CPIDateParseError(CPIError):
    """
    Raised if CPI HTML content date cannot be parsed or found.
    """
    def __init__(self, message="Unable to parse end date from CPI HTML content."):
        super().__init__(message)

class CPIDataUnavailableError(CPIError):
    """
    Raised when CPI data could not be fetched or processed into a DataFrame.
    """
    def __init__(self, message=None):
        super().__init__(message or (
            "CPI data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        ))

#   Crypto Data Pipeline Errors
class CryptoPipelineError(Exception):
    """Base exception for all crypto data pipeline errors."""
    pass

class CryptoLiveQuoteError(CryptoPipelineError):
    """Base exception for errors in fetching live crypto quote data."""
    pass

class CryptoLiveQuoteNoDataError(CryptoLiveQuoteError):
    """
    Raised when the crypto live quote API returns no usable market data
    (e.g. missing or empty 'marketPairs' fields).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{slug}: {msg}" for slug, msg in messages)
        super().__init__(f"No live quote data:\n{fmt}")

class CryptoLiveQuoteUnavailableError(CryptoLiveQuoteError):
    """
    Raised when, after parsing and cleaning, no DataFrame could be produced
    (an unexpected failure).
    """
    def __init__(self):
        super().__init__(
            "Live crypto quote data is currently unavailable. "
            "Please try again later. If the issue persists, report it at "
            "https://github.com/cedricmoorejr/quantsumore."
        )

class CryptoHistoricalError(CryptoPipelineError):
    """Base exception for errors in fetching crypto historical quote data."""
    pass

class CryptoHistoricalNoDataError(CryptoHistoricalError):
    """
    Raised when the crypto historical API returns no usable data
    (e.g. empty or missing 'quotes' payloads).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{slug}: {msg}" for slug, msg in messages)
        super().__init__(f"No historical data:\n{fmt}")

class CryptoHistoricalUnavailableError(CryptoHistoricalError):
    """
    Raised when historical data could not be processed into a valid DataFrame,
    after parsing and cleaning have run.
    """
    def __init__(self):
        super().__init__(
            "Historical crypto data is currently unavailable. "
            "Please try again later. If the issue persists, report it at "
            "https://github.com/cedricmoorejr/quantsumore."
        )

#   FX Data Pipeline Exceptions
class FXPipelineError(Exception):
    """Base exception for all FX data pipeline errors."""
    pass

class FXHistoricalError(FXPipelineError):
    """Base exception for fx_historical errors."""

class FXNoDataError(FXHistoricalError):
    """
    Raised when the API returns no data for the requested
    time periods for one or more currency pairs.
    """
    def __init__(self, messages):
        if isinstance(messages, (list, tuple)):
            message = "\n".join(messages)
        else:
            message = str(messages)
        super().__init__(message)

class FXDataUnavailableError(FXHistoricalError):
    """
    Raised when currency data is entirely unavailable,
    after all retries or checks have failed.
    """
    def __init__(self):
        super().__init__(
            "Currency data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class FXInterbankError(FXPipelineError):
    """Base exception for interbank rate errors."""

class FXInterbankNoDataError(FXInterbankError):
    """
    Raised when the interbank API returns no usable data
    (e.g. empty or missing 'response' payloads).
    """
    def __init__(self, message="No interbank rate data available for the given query."):
        super().__init__(message)

class FXInterbankDataUnavailableError(FXInterbankError):
    """
    Raised when data could not be processed into a valid DataFrame,
    after parsing and cleaning have run.
    """
    def __init__(self):
        super().__init__(
            "Interbank rate data is currently unavailable. "
            "Please try again later. If the issue persists, report it at "
            "https://github.com/cedricmoorejr/quantsumore."
        )

class LiveBidAskError(FXPipelineError):
    """Base exception for live bid/ask errors."""

class LiveBidAskNoDataError(LiveBidAskError):
    """
    Raised when the API returns responses but no usable bid/ask payload
    (e.g. missing or empty 'data' fields for all symbols).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{sym}: {msg}" for sym, msg in messages)
        super().__init__(f"No bid/ask data:\n{fmt}")

class LiveBidAskUnavailableError(LiveBidAskError):
    """
    Raised when, after parsing and cleaning, no DataFrame could be produced
    (an unexpected failure).
    """
    def __init__(self):
        super().__init__(
            "Live bid/ask data is currently unavailable. "
            "Please try again later. If the issue persists, "
            "report it at https://github.com/cedricmoorejr/quantsumore."
        )

class LiveQuoteError(FXPipelineError):
    """Base exception for live_quote errors."""

class LiveQuoteValidationError(LiveQuoteError):
    """
    Raised when the HTML content validation fails (e.g. wrong page or malformed HTML).
    """
    def __init__(self, url):
        ticker = None
        parts = url.split("/quotes/")
        if len(parts) > 1:
            ticker = urllib.parse.unquote(parts[1].split("/")[0])
        msg = "Validation failed"
        if ticker:
            msg += f" for Ticker: {ticker}."
        else:
            msg += f" for URL: {url}."
        msg += " The page content did not match expected FX quote overview patterns."
        super().__init__(msg)
        
class LiveQuoteUnavailableError(LiveQuoteError):
    """
    Raised when, after parsing, no usable quote data was produced
    (i.e. still in an error state or parse produced nothing).
    """
    def __init__(self):
        super().__init__(
            "Currency data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class ConversionError(FXPipelineError):
    """Base exception for conversion errors."""

class ConversionValidationError(ConversionError):
    """
    Raised when the HTML content fails validation (e.g. wrong page or malformed HTML).
    """
    def __init__(self, url):
        ticker = None
        parts = url.split("/quotes/")
        if len(parts) > 1:
            ticker = urllib.parse.unquote(parts[1].split("/")[0])
        msg = "Validation failed"
        if ticker:
            msg += f" for Ticker: {ticker}."
        else:
            msg += f" for URL: {url}."
        msg += " The page content did not match expected FX quote overview patterns."
        super().__init__(msg)
        
class ConversionNoDataError(ConversionError):
    """
    Raised when the conversion API returns no usable data
    (e.g. empty or missing 'response' payloads).
    """
    def __init__(self, message="No conversion rate data available for the given query."):
        super().__init__(message)
        
class ConversionUnavailableError(ConversionError):
    """
    Raised when, after parsing and restructuring, no usable conversion data was produced.
    """
    def __init__(self):
        super().__init__(
            "Conversion data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

#  Equity Data Pipeline Exceptions
class EquityPipelineError(Exception):
    """Base exception for all equity data pipeline errors."""
    pass

class IPOError(EquityPipelineError):
    """Base exception for IPO data errors."""
    pass

class IPONoDataError(IPOError):
    """
    Raised when the IPO API returns no data for requested companies/tickers.
    """
    def __init__(self, messages):
        if isinstance(messages, (list, tuple)):
            msg = "\n".join(str(m) for m in messages)
        else:
            msg = str(messages)
        super().__init__(f"No IPO data:\n{msg}")

class IPODataUnavailableError(IPOError):
    """
    Raised when IPO data is entirely unavailable and no detailed message exists.
    """
    def __init__(self):
        super().__init__(
            "IPO data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class LatestError(EquityPipelineError):
    """Base exception for errors in fetching latest price data."""
    pass

class LatestNoDataError(LatestError):
    """
    Raised when the API returns no latest price data for the requested ticker(s).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{ticker}: {msg}" for ticker, msg in messages)
        super().__init__(f"No latest price data:\n{fmt}")

class LatestDataUnavailableError(LatestError):
    """
    Raised when latest price data cannot be processed into a DataFrame.
    """
    def __init__(self):
        super().__init__(
            "Latest equity price data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class HistoricalError(EquityPipelineError):
    """Base exception for errors in fetching historical price data."""
    pass

class HistoricalNoDataError(HistoricalError):
    """
    Raised when the API returns no historical price data for the requested ticker(s).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{ticker}: {msg}" for ticker, msg in messages)
        super().__init__(f"No historical price data:\n{fmt}")

class HistoricalDataUnavailableError(HistoricalError):
    """
    Raised when historical price data cannot be processed into a DataFrame.
    """
    def __init__(self):
        super().__init__(
            "Historical equity price data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class LastTradeError(EquityPipelineError):
    """Base exception for errors in fetching last trade price data."""
    pass

class LastTradeNoDataError(LastTradeError):
    """
    Raised when the API returns no last trade price data for the requested ticker(s).
    """
    def __init__(self, messages):
        fmt = "\n".join(f"{ticker}: {msg}" for ticker, msg in messages)
        super().__init__(f"No last trade price data:\n{fmt}")

class LastTradeDataUnavailableError(LastTradeError):
    """
    Raised when last trade price data cannot be processed into a DataFrame.
    """
    def __init__(self):
        super().__init__(
            "Last trade price data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )

class QuoteStatisticsError(EquityPipelineError):
    """Base exception for errors encountered in the quote_statistics pipeline."""
    pass

class QuoteStatisticsValidationError(QuoteStatisticsError):
    """
    Raised when HTML validation fails (e.g., wrong source, wrong symbol, or malformed markup).
    """
    pass    
        
class QuoteStatisticsNoDataError(QuoteStatisticsError):
    """
    Raised when no usable quote statistics were found in the parsed HTML content.
    """
    pass    

class QuoteStatisticsUnavailableError(QuoteStatisticsError):
    """
    Raised when, after all parsing and checks, no statistics data is returned.
    """
    pass    

class CompanyProfileError(EquityPipelineError):
    """Base exception for errors encountered in the profile pipeline."""
    pass

class CompanyProfileValidationError(CompanyProfileError):
    """
    Raised when HTML validation fails for the profile page.
    """
    pass
        
class CompanyProfileNoDataError(CompanyProfileError):
    """
    Raised when no usable profile data (bio/details/executives) was found in the HTML.
    """
    pass

class CompanyProfileUnavailableError(CompanyProfileError):
    """
    Raised when, after all parsing and checks, no profile data is returned.
    """
    pass

#  Treasury Yield Pipeline Errors
class TreasuryPipelineError(Exception):
    """Base exception for all Treasury yield pipeline errors."""
    pass

class TreasuryDataValidationError(TreasuryPipelineError):
    """
    Raised when input data (DataFrame or CSV) cannot be validated,
    is missing required columns, or fails a sanity check.
    """
    def __init__(self, message="Treasury input data failed validation."):
        super().__init__(message)

class TreasuryNoDataError(TreasuryPipelineError):
    """
    Raised when no usable Treasury rates are found for the requested
    period/type (e.g., the DataFrame is empty after filtering).
    """
    def __init__(self, message="No Treasury yield data available for the requested period/type."):
        super().__init__(message)

class TreasuryDataUnavailableError(TreasuryPipelineError):
    """
    Raised when no output (dict or DataFrame) could be produced
    after all processing attempts.
    """
    def __init__(self):
        super().__init__(
            "Treasury rate data is currently unavailable. Please try again later. "
            "If the issue persists, report it at https://github.com/cedricmoorejr/quantsumore."
        )





   
   


   
def __dir__():
    return __all__
