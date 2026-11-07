# -*- coding: utf-8 -*-
#
## ╭────────────────────────────────────────────────────────────────────────────────────────────╮
## │  Library         : doydl's Finance API Client — quantsumore                                 │
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
## ╰────────────────────────────────────────────────────────────────────────────────────────────╯
#

"""Retrieve, analyze and export company financial statements.

The configured engine supplies financial statements and dividend data. Load a
ticker and period before accessing statements or ratios; available methods
depend on which datasets are loaded. Statement accessors return copies of the
cached data. Excel exports use the statement layout registry."""
from copy import deepcopy

from ._frameworks import WriteExcel
from ..date_parser import dtparse
from ..exceptions import (
    FinancialDataNotLoadedError,
    DividendDataNotLoadedError,
    WorkbookSaveError,
    InvalidFinancialStatementIdentifier,
    NoFinancialStatementsProvided,
    TickerNotFoundError,
)
from ._calc_ratio import Ratios
from ._calc_common import Common_Size
from ._calc_vertical import Vertical_Analysis
from ..proxy import Proxy
from ..strata_utils import IterDict


__all__ = ['fAnalyze']





# Defer dependency imports until first use.
pd = Proxy("pandas", None)

class fAnalyze:
    """Load financial statements and dividends through a configured engine.

    Call the instance with a ticker and period before accessing statements,
    ratios, common-size analysis or Excel exports. Successful loads are cached
    by ticker and period. Statement accessors return copies and raise
    dataset-specific exceptions when their data is unavailable.

    The engine must implement Process(ticker, period). Its results supply the
    income statement, balance sheet, cash flow statement and dividend datasets.
    Missing-data handling depends on the requested analysis method.
    """
    def __init__(self, engine):
        """Store the data engine and initialize analysis helpers and the cache.

        engine must provide Process(ticker, period). No company data is loaded
        until the instance is called with a ticker and reporting period.
        """
        self.engine = engine
        self.ticker = None       
        self._income_statement = pd.DataFrame()  
        self._balance_sheet = pd.DataFrame()  
        self._cash_flow_statement = pd.DataFrame() 
        self.dividend_data = None
        self.dividend_report = None
        
        self.ratios = Ratios(self)   
        self.common_size = Common_Size(self)       
        self.vertical_analysis = Vertical_Analysis(self)   
        self.cache = {}      

    class Statement:
        """Wrap a financial DataFrame indexed by account, with periods as columns.

        Attribute and item access delegate to the DataFrame. list_accounts()
        excludes rows containing only missing values. LineItem() matches accounts
        case-insensitively and accepts a column label, "current" or "past" as its
        optional timeframe. Parsed column dates are cached for timeframe lookups.
        Missing accounts raise KeyError; unsupported timeframes raise ValueError.
        """
        def __init__(self, data):
            """Wrap a DataFrame or convert array-like data to one.

            The constructor does not validate account names or reporting-period labels.
            """
            self.data = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
            self._parsed_dates = None

        def __getattr__(self, item):
            return getattr(self.data, item)

        def __getitem__(self, key):
            return self.data[key]

        def __setitem__(self, key, value):
            self.data[key] = value

        def __repr__(self):
            return repr(self.data)

        def list_accounts(self):
            statement = self.data.replace('', pd.NA)
            filtered_statement = statement.dropna(how='all')
            accounts = filtered_statement.index.tolist()
            return accounts

        def _get_parsed_dates(self):
            if self._parsed_dates is None:
                self._parsed_dates = {col: dtparse.parse(date_input=col) for col in self.data.columns}
            return self._parsed_dates

        def LineItem(self, account_name, timeframe=None):
            account_name_lower = account_name.lower()
            accounts_lower_map = {acct.lower(): acct for acct in self.list_accounts()}
            if account_name_lower not in accounts_lower_map:
                raise KeyError(f"Account '{account_name}' not found in the financial statement.")
            original_account_name = accounts_lower_map[account_name_lower]
            if timeframe:
                dates = self._get_parsed_dates()
                if timeframe == "current":
                    selected_date = dtparse.parse(date_input=max(dates.values()), to_format='%Y-%m-%d')
                elif timeframe == "past":
                    selected_date = dtparse.parse(date_input=min(dates.values()), to_format='%Y-%m-%d')
                else:
                    if timeframe in dates:
                        selected_date = timeframe
                    else:
                        raise ValueError("Invalid timeframe specified.")
                return self.data.loc[original_account_name, selected_date]
            return self.data.loc[original_account_name]
           
        def __dir__(self):
            return ['LineItem'] 
           
    def __assert_data_available(self, required_data):
        """ Verify that all required data objects are present and non-empty."""
        for data in required_data:
            if data is None or (hasattr(data, 'empty') and data.empty):
                raise AttributeError("Required financial data is not available.")

    def __fillna_empty(self, df):
        """ Return a copy of the DataFrame with all missing values (NaN/NA) replaced by empty strings."""    	
        df = deepcopy(df)
        return df.fillna("")
       
    def is_loaded(self, df):
        return df is not None and not df.empty      
           
    def __call__(self, ticker, period):
        """ Calls the instance as a function to fetch and process financial data for a specified ticker and period."""    	
        self.get_financial_data(ticker, period)
        
    def get_financial_data(self, ticker, period):
        """Load statement and dividend datasets for a ticker and reporting period.

        ticker must be a string, or a nonempty list/tuple whose first item is used.
        period is passed to the configured engine. Cached ticker/period results are
        reused; otherwise engine.Process() supplies financial_statements and dividend
        entries.

        Each statement is loaded independently when it is a nonempty DataFrame.
        Missing statements and dividend datasets remain unavailable through their
        accessors. Status messages are printed, while engine and parsing exceptions
        can propagate. A non-string ticker raises ValueError; an empty ticker
        sequence raises TickerNotFoundError.
        """
        if isinstance(ticker, (list, tuple)):
            if not ticker:
                raise TickerNotFoundError("Cannot find ticker symbol!")
            ticker = ticker[0]

        if not isinstance(ticker, str):
            raise ValueError("Ticker must be a single string value.")

        self.ticker = ticker.strip()
        
        cache_key = (self.ticker, period)
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            self.income_statement = cached_data['income_statement']
            self.balance_sheet = cached_data['balance_sheet']
            self.cash_flow_statement = cached_data['cash_flow_statement']
            self.dividend_data = cached_data.get('dividend_data', None)
            self.dividend_report = cached_data.get('dividend_report', None)
        else:
            data = self.engine.Process(self.ticker, period)
            statements = data.get('financial_statements', [])

            if not statements:
                self.income_statement     = None
                self.balance_sheet        = None
                self.cash_flow_statement  = None
                print(f"Financial Statements could not be loaded for {self.ticker}.")

            else:
                income, balance, cash_flow = statements[0]

                loaded_income = (
                    self.__fillna_empty(income)
                    if isinstance(income, pd.DataFrame) and not income.empty else None
                )
                loaded_balance = (
                    self.__fillna_empty(balance)
                    if isinstance(balance, pd.DataFrame) and not balance.empty else None
                )
                loaded_cashflow = (
                    self.__fillna_empty(cash_flow)
                    if isinstance(cash_flow, pd.DataFrame) and not cash_flow.empty else None
                )

                self.income_statement     = loaded_income
                self.balance_sheet        = loaded_balance
                self.cash_flow_statement  = loaded_cashflow

                self.cache[cache_key] = {
                    'income_statement':     loaded_income,
                    'balance_sheet':        loaded_balance,
                    'cash_flow_statement':  loaded_cashflow,
                }

                if self.is_loaded(loaded_income) and self.is_loaded(loaded_balance) and self.is_loaded(loaded_cashflow):
                    print(f"Financial Statements successfully loaded for {self.ticker}.")
                else:
                    missing = []
                    if loaded_income is None or loaded_income.empty:
                        missing.append("Income Statement")
                    if loaded_balance is None or loaded_balance.empty:
                        missing.append("Balance Sheet")
                    if loaded_cashflow is None or loaded_cashflow.empty:
                        missing.append("Cash Flow Statement")

                    print(f"Financial Statements loaded for {self.ticker}.")
                    print(f"  • Missing: {', '.join(missing)}")                

            divs = data.get('dividend', [])

            if isinstance(divs, str) and divs.startswith("Error:"):
                self.dividend_report = None
                self.dividend_data   = None
                print(divs.replace("Error: ", ""))

            elif not divs:
                self.dividend_report = None
                self.dividend_data   = None
                print(f"No dividend data available for {self.ticker}.")

            else:
                report, hist = divs[0]
                if report is not None and hist is not None:
                    self.dividend_report = report
                    self.dividend_data   = hist
                    self.cache[cache_key].update({
                        'dividend_report': report,
                        'dividend_data':   hist
                    })
                    print(f"Dividend data successfully loaded for {self.ticker}.")
                else:
                    self.dividend_report = None
                    self.dividend_data   = None
                    print(f"No valid dividend data found for {self.ticker}.")

                
    # Return copies so callers cannot mutate cached statements.
    # Setters normalize statement data and clear the stored value for None.
    
    # Income statement.
    @property
    def income_statement(self):
        stmt = self._income_statement
        if not hasattr(stmt, 'data') or stmt.data.empty:
            raise FinancialDataNotLoadedError(f"No income‐statement data loaded for ticker {self.ticker!r}.")
        return deepcopy(stmt)
       
    @income_statement.setter
    def income_statement(self, value):
        self._income_statement = self.Statement(value) if value is not None else pd.DataFrame()

    # Balance sheet.
    @property
    def balance_sheet(self):
        bs = self._balance_sheet
        if not hasattr(bs, 'data') or bs.data.empty:
            raise FinancialDataNotLoadedError(f"No balance‐sheet data loaded for ticker {self.ticker!r}.")
        return deepcopy(bs)   
       
    @balance_sheet.setter
    def balance_sheet(self, value):
        self._balance_sheet = self.Statement(value) if value is not None else pd.DataFrame()

    # Cash flow statement.
    @property
    def cash_flow_statement(self):
        cf = self._cash_flow_statement
        if not hasattr(cf, 'data') or cf.data.empty:
            raise FinancialDataNotLoadedError(f"No cash‐flow‐statement data loaded for ticker {self.ticker!r}.")
        return deepcopy(cf)
       
    @cash_flow_statement.setter
    def cash_flow_statement(self, value):
        self._cash_flow_statement = self.Statement(value) if value is not None else pd.DataFrame()

    # Dividends.
    @property
    def dividend_data(self):
        if self._dividend_data is None:
            raise DividendDataNotLoadedError(f"No raw dividend data loaded for ticker {self.ticker!r}.")
        return deepcopy(self._dividend_data)    
       
    @dividend_data.setter
    def dividend_data(self, value):
        self._dividend_data = value

    @property
    def dividend_report(self):
        if self._dividend_report is None:
            raise DividendDataNotLoadedError(f"No dividend‐summary report loaded for ticker {self.ticker!r}.")
        return deepcopy(self._dividend_report)   
       
    @dividend_report.setter
    def dividend_report(self, value):
        self._dividend_report = value


    

    
    def dividend_yield(self):
        """Calculate and return the company’s dividend yield.

        Returns:
        ---------
            float or None: The dividend yield as a decimal (e.g., 0.024 for 2.4%), or None if unavailable.

        Raises:
        --------
            DividendDataNotLoadedError: If required dividend data is not available.

        Notes:
        -------
            Dividend yield represents the ratio of annual dividends per share to the share price.
        """
        self.__assert_data_available([self.dividend_data, self.dividend_report])
        return self.ratios._dividend_yield()

    def ex_dividend_date(self):
        """Retrieve the company’s most recent ex-dividend date.

        Returns:
        --------
            str or None: The ex-dividend date as a string in 'YYYY-MM-DD' format, or None if unavailable.

        Raises:
        -------
            DividendDataNotLoadedError: If required dividend data is not available.

        Notes:
        ------
            The ex-dividend date is the cutoff date for being eligible to receive the next dividend payment.
        """
        self.__assert_data_available([self.dividend_data, self.dividend_report])
        return self.ratios._ex_dividend_date()

    def annual_dividend(self):
        """Return the total annual dividend paid per share.

        Returns:
        --------
            float or None: The annual dividend per share, or None if unavailable.

        Raises:
        -------
            DividendDataNotLoadedError: If required dividend data is not available.

        Notes:
        ------
            This value reflects the sum of all dividends paid over the past year for each outstanding share.
        """
        self.__assert_data_available([self.dividend_data, self.dividend_report])
        return self.ratios._annual_dividend()

    def current_ratio(self):
        """Calculate and return the current ratio from the balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The current ratio (current assets divided by current liabilities),
            either as a single float or a series by period, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is not available.

        Notes:
        ------
            The current ratio is a key liquidity metric indicating the company’s ability to cover short-term obligations.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._current_ratio()
           
    def quick_ratio(self):
        """Calculate and return the quick ratio from the balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The quick ratio (also known as the acid-test ratio), or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is not available.

        Notes:
        ------
            The quick ratio measures a company’s ability to meet short-term obligations using its most liquid assets
            (excluding inventory). A ratio above 1 generally indicates good short-term financial health.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._quick_ratio()


    def cash_ratio(self):
        """Calculate and return the cash ratio from the balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The cash ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is not available.

        Notes:
        ------
            The cash ratio is the most conservative liquidity ratio, measuring a company’s ability to pay
            short-term obligations with only its cash and cash equivalents.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._cash_ratio()


    def debt_to_equity_ratio(self):
        """Calculate and return the debt to equity ratio from the balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The debt-to-equity ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is not available.

        Notes:
        ------
            This ratio indicates the relative proportion of shareholders' equity and debt used to finance a company’s assets.
            A higher ratio may indicate greater financial risk.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._debt_to_equity_ratio()

    def debt_to_capital_ratio(self):
        """Calculate and return the debt-to-capital ratio from the balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The debt-to-capital ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is not available.

        Notes:
        ------
            The debt-to-capital ratio measures the proportion of a company’s capital structure that is financed by debt,
            providing insights into leverage and risk.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._debt_to_capital_ratio()

    def gross_profit_margin_ratio(self):
        """Calculate and return the gross profit margin ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The gross profit margin ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is not available.

        Notes:
        ------
            Gross profit margin is a profitability ratio that shows the percentage of revenue that exceeds the cost of goods sold (COGS).
            It provides insight into a company’s production efficiency.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._gross_profit_margin_ratio()

    def operating_profit_margin_ratio(self):
        """Calculate and return the operating profit margin ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The operating profit margin ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is not available.

        Notes:
        ------
            Operating profit margin measures the proportion of revenue left after covering operating expenses.
            It’s a key indicator of operational efficiency.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._operating_profit_margin_ratio()

    def net_profit_margin(self):
        """Calculate and return the net profit margin from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The net profit margin, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is not available.

        Notes:
        ------
            Net profit margin is the percentage of revenue remaining after all expenses, taxes, and costs have been deducted.
            It is a comprehensive measure of profitability.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._net_profit_margin()

    def ebit_margin(self):
        """Calculate and return the EBIT margin from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The EBIT (Earnings Before Interest and Taxes) margin, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The EBIT margin shows the percentage of revenue remaining after operating and non-operating expenses,
            excluding interest and taxes. It’s a key indicator of operating profitability.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._ebit_margin()

    def rd_to_revenue_ratio(self):
        """Calculate and return the R&D to revenue ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The ratio of research & development (R&D) expense to total revenue, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            This ratio measures the portion of revenue invested in research and development. It’s useful for evaluating a company’s focus on innovation.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._rd_to_revenue_ratio()

    def sga_to_revenue_ratio(self):
        """Calculate and return the SG&A to revenue ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The ratio of selling, general, and administrative (SG&A) expense to revenue, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The SG&A to revenue ratio reflects operating expenses (excluding COGS) as a share of total revenue,
            helping to assess cost control and operational efficiency.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._sga_to_revenue_ratio()

    def interest_coverage_ratio(self):
        """Calculate and return the interest coverage ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The interest coverage ratio (EBIT / interest expense), or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The interest coverage ratio shows how easily a company can pay interest on outstanding debt.
            Higher values indicate stronger ability to meet interest obligations.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._interest_coverage_ratio()

    def pretax_profit_margin_ratio(self):
        """Calculate and return the pretax profit margin ratio from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The pretax profit margin ratio, or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The pretax profit margin measures earnings before tax as a percentage of revenue,
            highlighting profitability before tax obligations.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._pretax_profit_margin_ratio()

    def tax_burden(self):
        """Calculate and return the tax burden from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The tax burden ratio (net income / earnings before tax), or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The tax burden reflects the proportion of earnings before tax that remains after taxes are paid,
            indicating the effective tax rate.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._tax_burden()

    def interest_burden(self):
        """Calculate and return the interest burden from the income statement.

        Returns:
        --------
            float or pandas.Series or None: The interest burden ratio (earnings before tax / EBIT), or None if unavailable.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The interest burden measures how much EBIT is reduced by interest expense before tax, providing insight into financing costs.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._interest_burden()

    def capex_ratio(self):
        """Calculate and return the CAPEX ratio from the cash flow statement.

        Returns:
        --------
            float or pandas.Series or None: The ratio of net operating cash flow to capital expenditures (CAPEX).

        Raises:
        -------
            FinancialDataNotLoadedError: If required cash flow statement data is missing.

        Notes:
        ------
            This ratio shows how much operating cash flow is being used for capital investment.
            It provides insight into the sustainability of a company’s capital spending.
        """
        self.__assert_data_available([self.cash_flow_statement])
        return self.ratios._capex_ratio()

    def free_cash_flow_to_operating_cash_flow_ratio(self):
        """Calculate and return the ratio of free cash flow to operating cash flow from the cash flow statement.

        Returns:
        --------
            float or pandas.Series or None: The ratio of free cash flow to operating cash flow.

        Raises:
        -------
            FinancialDataNotLoadedError: If required cash flow statement data is missing.

        Notes:
        ------
            This ratio indicates the proportion of operating cash flow that remains after capital expenditures,
            reflecting the company’s financial flexibility.
        """
        self.__assert_data_available([self.cash_flow_statement])
        return self.ratios._free_cash_flow_to_operating_cash_flow_ratio()

    def defensive_interval_ratio(self):
        """Calculate and return the defensive interval ratio using the income statement and balance sheet.

        Returns:
        --------
            float or pandas.Series or None: The defensive interval ratio (liquid assets / daily operating expenses).

        Raises:
        -------
            FinancialDataNotLoadedError: If required financial statement data is missing.

        Notes:
        ------
            The defensive interval ratio measures how many days a company can cover its operating expenses
            using only its most liquid assets. It is a conservative liquidity metric.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])   
        return self.ratios._defensive_interval_ratio()

    def fixed_charge_coverage_ratio(self, lease_payments=0):
        """Calculate and return the fixed charge coverage ratio from the income statement.

        Args:
        -----
            lease_payments (float, optional): Additional lease payments to include in fixed charges. Default is 0.

        Returns:
        --------
            float or pandas.Series or None: The fixed charge coverage ratio, or None if data is missing.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement data is missing.

        Notes:
        ------
            The fixed charge coverage ratio evaluates a company’s ability to meet its fixed financial obligations,
            including interest and lease payments.
        """
        self.__assert_data_available([self.income_statement])
        return self.ratios._fixed_charge_coverage_ratio(lease_payments=lease_payments)

    def receivables_turnover_ratio(self):
        """Calculate and return the receivables turnover ratio using the income statement and balance sheet.

        Returns:
        --------
            pandas.Series or None: The receivables turnover ratio for each period, or None if data is missing.

        Raises:
        -------
            FinancialDataNotLoadedError: If required statement data is missing.

        Notes:
        ------
            This ratio measures how many times receivables are collected during a period,
            indicating the effectiveness of credit and collection policies.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])   
        return self.ratios._receivables_turnover_ratio()

    def inventory_turnover_ratio(self):
        """Calculate and return the inventory turnover ratio using the income statement and balance sheet.

        Returns:
        --------
            pandas.Series or None: The inventory turnover ratio for each period, or None if data is missing.

        Raises:
        -------
            FinancialDataNotLoadedError: If required statement data is missing.

        Notes:
        ------
            The inventory turnover ratio shows how often inventory is sold and replaced over a period.
            Higher values may indicate efficient inventory management.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])        
        return self.ratios._inventory_turnover_ratio()

    def days_sales_outstanding(self):
        """Calculate and return the Days Sales Outstanding (DSO) using the income statement and balance sheet.

        Returns:
        --------
            pandas.Series or None: The DSO for each period, or None if data is missing.

        Raises:
        -------
            FinancialDataNotLoadedError: If required statement data is missing.

        Notes:
        ------
            DSO measures the average number of days it takes to collect payment after a sale.
            Lower values generally indicate more efficient collections.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._days_sales_outstanding()
      
    def days_inventory_on_hand(self):
        """Calculate and return the Days Inventory On Hand (DIOH).

        Returns:
        --------
            pandas.Series or None: The average number of days inventory is held before being sold, for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            DIOH measures inventory efficiency, indicating how quickly a company sells its inventory.
            Lower values generally reflect more efficient inventory management.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._days_inventory_on_hand()

    def payables_turnover_ratio(self):
        """Calculate and return the Payables Turnover Ratio.

        Returns:
        --------
            pandas.Series or None: The ratio for each period, indicating how quickly payables are paid.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            This ratio shows how many times a company pays off its accounts payable during a period.
            Higher values may signal prompt payment to suppliers.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._payables_turnover_ratio()

    def days_of_payables(self):
        """Calculate and return the Number of Days Payables Ratio.

        Returns:
        --------
            pandas.Series or None: The average number of days the company takes to pay its suppliers, for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            This metric indicates the average time the company takes to settle its accounts payable.
            Higher values may indicate longer credit terms from suppliers or delayed payments.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._days_of_payables()

    def cash_conversion_cycle(self):
        """Calculate and return the Cash Conversion Cycle (CCC).

        Returns:
        --------
            pandas.Series or None: The cash conversion cycle for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required component data is missing.

        Notes:
        ------
            The CCC measures the time (in days) it takes for a company to convert its investments in inventory
            and other resources into cash flows from sales. It combines DSO, DIOH, and days of payables.
        """
        return self.ratios._cash_conversion_cycle()

    def return_on_equity(self):
        """Calculate and return the Return on Equity (ROE).

        Returns:
        --------
            pandas.Series or None: The ROE for each period, representing net income as a percentage of average shareholders' equity.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            ROE measures a company's profitability by revealing how much profit a company generates with the money
            shareholders have invested.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._return_on_equity()

    def working_capital_turnover(self):
        """Calculate and return the Working Capital Turnover Ratio.

        Returns:
        --------
            pandas.Series or None: The working capital turnover ratio for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            This ratio measures how efficiently a company uses its working capital to generate sales.
            Higher values indicate efficient use of short-term assets and liabilities.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._working_capital_turnover()

    def fixed_asset_turnover(self):
        """Calculate and return the Fixed Asset Turnover Ratio.

        Returns:
        --------
            pandas.Series or None: The fixed asset turnover ratio for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            The fixed asset turnover ratio measures how effectively a company uses its fixed assets
            to generate revenue. Higher values typically indicate better utilization of fixed assets.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._fixed_asset_turnover()

    def total_asset_turnover(self):
        """Calculate and return the Total Asset Turnover Ratio.

        Returns:
        --------
            pandas.Series or None: The total asset turnover ratio for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            This ratio measures how efficiently a company uses all of its assets to generate revenue.
            Higher values typically indicate better asset utilization.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._total_asset_turnover()

    def operating_return_on_assets(self):
        """Calculate and return the Operating Return on Assets (OROA).

        Returns:
        --------
            pandas.Series or None: The operating return on assets for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            OROA measures how efficiently a company’s operating income is generated from its total assets.
            It is useful for evaluating core business profitability, excluding non-operating items.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._operating_return_on_assets()

    def return_on_assets(self):
        """Calculate and return the Return on Assets (ROA).

        Returns:
        --------
            pandas.Series or None: The return on assets for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            ROA expresses net income as a percentage of average total assets.
            It is a key metric for understanding overall profitability and asset efficiency.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._return_on_assets()

    def equity_multiplier(self):
        """Calculate and return the Equity Multiplier.

        Returns:
        --------
            pandas.Series or None: The equity multiplier (financial leverage) for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required balance sheet data is missing.

        Notes:
        ------
            The equity multiplier reflects a company’s financial leverage by showing how much of assets
            are financed by shareholders’ equity. Higher values indicate greater leverage.
        """
        self.__assert_data_available([self.balance_sheet])
        return self.ratios._equity_multiplier()

    def return_on_invested_capital_pre_tax(self):
        """Calculate and return the Pre-Tax Return on Invested Capital (ROIC).

        Returns:
        --------
            pandas.Series or None: The pre-tax ROIC for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            Pre-tax ROIC measures the efficiency and profitability of company capital investments before taxes.
            It is useful for comparing returns across companies regardless of their tax environments.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._return_on_invested_capital_pre_tax()

    def return_on_invested_capital_after_tax(self):
        """Calculate and return the After-Tax Return on Invested Capital (ROIC).

        Returns:
        --------
            pandas.Series or None: The after-tax ROIC for each period.

        Raises:
        -------
            FinancialDataNotLoadedError: If required income statement or balance sheet data is missing.

        Notes:
        ------
            After-tax ROIC accounts for the impact of income taxes and provides a realistic measure of capital returns.
            It is a key metric for evaluating value creation from the company’s invested capital.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet])
        return self.ratios._return_on_invested_capital_after_tax()



    
    
    def CommonSize(self, financial_statement):
        """
        Generate a common size version of the specified financial statement.

        Parameters:
        -----------
            financial_statement : str
                Identifier for the financial statement to analyze. Accepts any of the following:
                - Income Statement: "I", "IS", "Income", "Income_Statement", "Income Statement"
                - Balance Sheet: "B", "BS", "Balance Sheet", "Balance_Sheet"
                - Cash Flow Statement: "C", "CF", "Cash", "Cash Flow", "Cash_Flow",
                  "Cash Flow Statement", "Cash_Flow_Statement"

        Returns:
        -----------
            pandas.DataFrame : A common size financial statement where each value is expressed
                               as a percentage of a key base (e.g., total revenue or total assets).

        Notes:
        -----------
            This is useful for comparing financial performance across companies or time periods
            regardless of absolute scale.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet, self.cash_flow_statement])
        return self.common_size._CommonSize(financial_statement=financial_statement) 

    def VerticalAnalysis(self, financial_statement):
        """
        Perform a vertical analysis on the specified financial statement.

        Parameters:
        -----------
            financial_statement : str
                Identifier for the financial statement to analyze. Accepts any of the following:
                - Income Statement: "I", "IS", "Income", "Income_Statement", "Income Statement"
                - Balance Sheet: "B", "BS", "Balance Sheet", "Balance_Sheet"
                - Cash Flow Statement: "C", "CF", "Cash", "Cash Flow", "Cash_Flow",
                  "Cash Flow Statement", "Cash_Flow_Statement"

        Returns:
        -----------
            pandas.DataFrame : A DataFrame showing the vertical analysis, where each line item
                               is presented as a percentage of a key figure (e.g., total revenue or assets).

        Notes:
        -----------
            Vertical analysis highlights the relative weight of each line item within a statement,
            aiding internal structure analysis and trend detection.
        """  	
        self.__assert_data_available([self.income_statement, self.balance_sheet, self.cash_flow_statement])
        return self.vertical_analysis._VerticalAnalysis(financial_statement=financial_statement) 



    
    
    def writeStatement(self, save_path, financial_statements=None, include_common_size=False):
        """Write selected statements to a new Excel workbook at save_path.

        All three statements must be loaded. financial_statements may be a statement
        alias or a list of aliases; a falsy value selects all statements. Aliases
        include "Income Statement"/"I"/"IS", "Balance Sheet"/"B"/"BS", and
        "Cash Flow Statement"/"C"/"CF". include_common_size=True selects
        percentage columns alongside the original values.

        The output replaces an existing file at save_path. NoFinancialStatementsProvided
        is raised if selection leaves no statements. Dataset-access errors propagate;
        workbook-writing failures are reported as WorkbookSaveError.
        """
        self.__assert_data_available([self.income_statement, self.balance_sheet, self.cash_flow_statement])

        valid_statements = {
            "Income Statement": ["I", "IS", "Income", "Income_Statement", "Income Statement"],
            "Balance Sheet": ["Balance Sheet", "B", "BS", "Balance_Sheet"],
            "Cash Flow Statement": ["Cash Flow Statement", "Cash_Flow_Statement", "C", "CF", "Cash Flow", "Cash_Flow", "Cash"],
        }
        if include_common_size:
            formats = "common_size"
        else:
            formats = "standard"
            
        statements = {
            "standard": {
                "Income Statement": self.income_statement,
                "Balance Sheet": self.balance_sheet,
                "Cash Flow Statement": self.cash_flow_statement
            },
            "common_size": {
                "Income Statement": self.common_size._CommonSize(financial_statement="Income Statement"),
                "Balance Sheet": self.common_size._CommonSize(financial_statement="Balance Sheet"),
                "Cash Flow Statement": self.common_size._CommonSize(financial_statement="Cash Flow Statement")
            }
        }[formats]               

        if financial_statements:
            if isinstance(financial_statements, str):
                financial_statements = [financial_statements]
            try:
                resolved_statements = [IterDict.key_from_mapping(f, valid_statements, invert=False) for f in financial_statements]
                statements = {name: stmt for name, stmt in statements.items() if name in resolved_statements}
            except KeyError as e:
                raise InvalidFinancialStatementIdentifier(f"Invalid financial statement identifier: {e}")

        if not statements:
            raise NoFinancialStatementsProvided("No valid financial statements provided to write.")

        try:
            with WriteExcel() as excel_writer:
                for name, statement in statements.items():
                    excel_writer.write_statement(statement)
                excel_writer.save(filename=save_path)
        except WorkbookSaveError:
            raise
        except Exception as e:
            raise WorkbookSaveError(f"An error occurred while writing statements: {e}") from e

    # List analysis methods for interactive discovery according to loaded data.
    
    def __dir__(self):
        available_attributes = []       
        financial_statements_exist = (
            hasattr(self._income_statement, 'data') and not self._income_statement.data.empty and
            hasattr(self._balance_sheet, 'data') and not self._balance_sheet.data.empty and
            hasattr(self._cash_flow_statement, 'data') and not self._cash_flow_statement.data.empty
        )
        if financial_statements_exist:
            available_attributes.extend([
                "CommonSize", "balance_sheet", "capex_ratio", "cash_flow_statement", "current_ratio",
                "debt_to_equity_ratio", "ebit_margin", "free_cash_flow_to_operating_cash_flow_ratio", "gross_profit_margin_ratio", "income_statement",
                "interest_coverage_ratio", "net_profit_margin", "operating_profit_margin_ratio", "quick_ratio", "rd_to_revenue_ratio",
                "sga_to_revenue_ratio", "cash_ratio", "pretax_profit_margin_ratio", "tax_burden", "interest_burden",
                "debt_to_capital_ratio", "defensive_interval_ratio", "fixed_charge_coverage_ratio", "receivables_turnover_ratio", "inventory_turnover_ratio",
                "writeStatement", "Statement", "VerticalAnalysis", "days_sales_outstanding", "days_inventory_on_hand",
                "payables_turnover_ratio", "days_of_payables", "cash_conversion_cycle", "return_on_equity", "working_capital_turnover",
                "fixed_asset_turnover", "total_asset_turnover", "operating_return_on_assets", "return_on_assets", "equity_multiplier",
                "return_on_invested_capital_pre_tax", "return_on_invested_capital_after_tax",
            ])
            if self._dividend_data is not None and self._dividend_report is not None:
                available_attributes.extend([
                    "dividend_data", "dividend_report", "dividend_yield",
                    "ex_dividend_date", "annual_dividend"
                ])
        return available_attributes  

def __dir__():
    return __all__
