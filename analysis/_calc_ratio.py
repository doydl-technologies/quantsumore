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

from copy import deepcopy
import re
import io
import sys

from ..proxy import Proxy


__all__ = ['Ratios']



# Defer dependency imports until first use.
pd = Proxy("pandas", None)


def _ratio_output_(func, *args, **kwargs):
    """Call a function while capturing its printed output.

    Return its non-None result only if it printed nothing; otherwise return
    the captured text. Functions returning None without printing produce an
    empty string. sys.stdout is restored on exit, but redirection is global
    and is not synchronized across threads.
    """
    captured = io.StringIO() 
    old = sys.stdout       
    sys.stdout = captured  
    try:
        result = func(*args, **kwargs) 
        output = captured.getvalue()
    finally:
        sys.stdout = old
    if result is not None and output == '':
        return result 
    return output 
   


# Extract and normalize financial accounts before calculating ratios.

class Ratios:
    def __init__(self, analyze_instance):
        self.parent = analyze_instance
       
    def __leap_year(self, year):
        """Determine if the specified year is a leap year."""
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 366
        return 365   
       
    def __clean_statement(self, financial_statement, keep=None):
        """Cleans a financial statement DataFrame, replacing '--' and empty strings with pd.NA, optionally keeping certain original markers."""
        valid = ["markers", "blanks", "all"]
        if keep and keep.lower() not in valid:
            raise ValueError("Invalid value for 'keep'. Choose 'all', 'markers', or 'blanks'.")
        statement = deepcopy(financial_statement)
        statement.replace(['--', ''], pd.NA, inplace=True)
        statement = statement.apply(pd.to_numeric, errors='coerce').astype(float)
        if keep == "all":
            return statement.where(~financial_statement.isin(['--', '']), financial_statement)
        elif keep == "markers":
            return statement.where(~financial_statement.isin(['--']), financial_statement)
        elif keep == "blanks":
            return statement.where(~financial_statement.isin(['']), financial_statement)
        return statement
       
    def __prepare_statement(self, attribute_name):
        statement = getattr(self.parent, attribute_name, None)
        if statement is None:
            return None
        cleaned_statement = self.__clean_statement(statement, keep="markers")
        if cleaned_statement.empty:
            return None
        return cleaned_statement   
       
    def __account(self, statement, account_name, missing_accounts=None, period_selection=None):
        """ Retrieves and cleans an account series from a financial statement DataFrame, handling missing or placeholder values. """
        account_series = statement.loc[account_name]
        if any(value == '--' for value in account_series):
            if missing_accounts is not None:
                missing_accounts.append(account_name)
            return None
        cleaned_series = account_series.apply(lambda x: None if x == '--' else x)
        if isinstance(period_selection, str) and re.match(r"\d{4}-\d{2}-\d{2}", period_selection):
            return cleaned_series.get(period_selection)
        elif period_selection == 1:
            return cleaned_series.iloc[0]
        elif period_selection == 2:
            return cleaned_series.iloc[-1]
        return cleaned_series
       
    def __account_series(self, account_series, inverse=False):
        """ Adjusts financial figures in a given series by normalizing each amount to reflect daily values, accounting for leap years. """           	
        adjusted = {}
        for date, amount in account_series.items():
            year = pd.to_datetime(date).year 
            days_in_year = self.__leap_year(year)
            if inverse:
                adjusted[date] = days_in_year / amount
            else:
                adjusted[date] = amount / days_in_year
        return pd.Series(adjusted)
       
    # Dividend ratios.
    def _dividend_yield(self):
        try:
            summary = self.parent.dividend_report
            if summary is not None and 'Dividend Yield' in summary['Metric'].values:
                value = summary.loc[summary['Metric'] == 'Dividend Yield', 'Value'].values
                if value.size > 0:
                    return float(value[0])
        except:
            print("Error: Dividend Yield is not a valid float.")
        return None

    def _ex_dividend_date(self):
        summary = self.parent.dividend_report
        if summary is not None and 'Ex-Dividend Date' in summary['Metric'].values:
            value = summary.loc[summary['Metric'] == 'Ex-Dividend Date', 'Value'].values
            if value.size > 0:
                return value[0]
        return None

    def _annual_dividend(self):
        try:
            summary = self.parent.dividend_report
            if summary is not None and 'Annual Dividend' in summary['Metric'].values:
                value = summary.loc[summary['Metric'] == 'Annual Dividend', 'Value'].values
                if value.size > 0:
                    return float(value[0])
        except:
            print("Error: Annual Dividend is not a valid float.")
        return None

    # Ratios.
    def _current_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')
        if balance_sheet is not None:
            missing_accounts = []
            current_assets = self.__account(balance_sheet, 'Total Current Assets' , missing_accounts)
            current_liabilities = self.__account(balance_sheet, 'Total Current Liabilities', missing_accounts)  
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            
            if (current_liabilities != 0).all():
                return current_assets / current_liabilities
            else:
                print("Current liabilities is zero or negative, cannot compute current ratio.")
                return None                        
        return None
       
    def _quick_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')
        if balance_sheet is not None:
            missing_accounts = []
            cash = self.__account(balance_sheet, 'Cash and Cash Equivalents', missing_accounts)
            short_term_investments = self.__account(balance_sheet, 'Short-Term Investments', missing_accounts)
            receivables = self.__account(balance_sheet, 'Net Receivables', missing_accounts)
            current_liabilities = self.__account(balance_sheet, 'Total Current Liabilities', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            
            if (current_liabilities != 0).all():
                return (cash + short_term_investments + receivables) / current_liabilities
            else:
                print("Current liabilities is zero or negative, cannot compute quick ratio.")
                return None                        
        return None
       
    def _cash_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')
        if balance_sheet is not None:
            missing_accounts = []
            cash = self.__account(balance_sheet, 'Cash and Cash Equivalents', missing_accounts)
            short_term_investments = self.__account(balance_sheet, 'Short-Term Investments', missing_accounts)
            current_liabilities = self.__account(balance_sheet, 'Total Current Liabilities', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None

            if (current_liabilities != 0).all():
                return (cash + short_term_investments) / current_liabilities
            else:
                print("Current liabilities is zero or negative, cannot compute cash ratio.")
                return None
        return None

    def _debt_to_equity_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')    
        if balance_sheet is not None:
            missing_accounts = []
            short_term_debt = self.__account(balance_sheet, 'Short-Term Debt / Current Portion of Long-Term Debt', missing_accounts)
            long_term_debt = self.__account(balance_sheet, 'Long-Term Debt', missing_accounts)
            total_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            
            if (total_equity != 0).all():
                return (short_term_debt + long_term_debt) / total_equity
            else:
                print("Total equity contains zero or negative values, cannot compute debt-to-equity ratio.")
                return None
        return None
    
    def _debt_to_capital_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')
        if balance_sheet is not None:
            missing_accounts = []                
            short_term_debt = self.__account(balance_sheet, 'Short-Term Debt / Current Portion of Long-Term Debt', missing_accounts)
            long_term_debt = self.__account(balance_sheet, 'Long-Term Debt', missing_accounts)
            equity = self.__account(balance_sheet, 'Total Equity', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            total_capital = (short_term_debt + long_term_debt) + equity
            if (total_capital != 0).all():
                return (short_term_debt + long_term_debt) / total_capital
            else:
                print("Total capital contains zero or negative values, cannot compute debt-to-capital ratio.")
                return None
        return None

    def _gross_profit_margin_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            gross_profit = self.__account(income_statement, 'Gross Profit', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return gross_profit / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute gross profit margin ratio.")
                return None
        return None

    def _operating_profit_margin_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            operating_income = self.__account(income_statement, 'Operating Income', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return operating_income / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute operating profit margin ratio.")
                return None
        return None

    def _net_profit_margin(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            net_income = self.__account(income_statement, 'Net Income', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return net_income / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute net profit margin.")
                return None
        return None

    def _ebit_margin(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            ebit = self.__account(income_statement, 'Earnings Before Interest and Tax', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            
            if (total_revenue != 0).all():
                return ebit / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute EBIT margin.")
                return None
        return None

    def _pretax_profit_margin_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            earnings_before_tax = self.__account(income_statement, 'Earnings Before Tax', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return earnings_before_tax / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute pretax profit margin ratio.")
                return None
        return None

    def _capex_ratio(self):
        cashflow_statement = self.__prepare_statement('cash_flow_statement')
        if cashflow_statement is not None:
            missing_accounts = []
            net_cash_flow_operating = self.__account(cashflow_statement, 'Net Cash Flow-Operating', missing_accounts)
            capital_expenditures = self.__account(cashflow_statement, 'Capital Expenditures', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (capital_expenditures != 0).all():
                return net_cash_flow_operating / capital_expenditures
            else:
                print("Capital expenditures contain zero or negative values, cannot compute capex ratio.")
                return None
        return None

    def _free_cash_flow_to_operating_cash_flow_ratio(self):
        cashflow_statement = self.__prepare_statement('cash_flow_statement')
        if cashflow_statement is not None:
            missing_accounts = []
            free_cash_flow = _ratio_output_(self._capex_ratio)
            if not isinstance(free_cash_flow, pd.Series):
                print(free_cash_flow.strip())
                return None
            net_cash_flow_operating = self.__account(cashflow_statement, 'Net Cash Flow-Operating', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (net_cash_flow_operating != 0).all():
                return free_cash_flow / net_cash_flow_operating
            else:
                print("Net cash flow operating contains zero or negative values, cannot compute free cash flow to operating cash flow ratio.")
                return None
        return None

    def _rd_to_revenue_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            rd_expense = self.__account(income_statement, 'Research and Development', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return rd_expense / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute R&D to revenue ratio.")
                return None
        return None

    def _sga_to_revenue_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            sga_expense = self.__account(income_statement, 'Sales, General and Admin.', missing_accounts)
            total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (total_revenue != 0).all():
                return sga_expense / total_revenue
            else:
                print("Total revenue contains zero or negative values, cannot compute SG&A to revenue ratio.")
                return None
        return None

    def _interest_coverage_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            ebit = self.__account(income_statement, 'Earnings Before Interest and Tax', missing_accounts)
            interest_expense = self.__account(income_statement, 'Interest Expense', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (interest_expense != 0).all():
                return ebit / interest_expense
            else:
                print("Interest expense contains zero or negative values, cannot compute interest coverage ratio.")
                return None
        return None

    def _tax_burden(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []
            net_income  = self.__account(income_statement, 'Net Income', missing_accounts)                
            earnings_before_tax = self.__account(income_statement, 'Earnings Before Tax', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (earnings_before_tax != 0).all():
                return net_income / earnings_before_tax
            else:
                print("Earnings before tax contains zero or negative values, cannot compute tax burden.")
                return None
        return None

    def _interest_burden(self):
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None:
            missing_accounts = []       
            earnings_before_tax = self.__account(income_statement, 'Earnings Before Tax', missing_accounts)
            ebit  = self.__account(income_statement, 'Earnings Before Interest and Tax', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            if (ebit != 0).all():
                return earnings_before_tax / ebit
            else:
                print("EBIT contains zero or negative values, cannot compute interest burden.")
                return None
        return None

    def _defensive_interval_ratio(self):
        balance_sheet = self.__prepare_statement('balance_sheet')
        income_statement = self.__prepare_statement('income_statement')
        if balance_sheet is not None and income_statement is not None:
            missing_accounts = []
            cash = self.__account(balance_sheet, 'Cash and Cash Equivalents', missing_accounts)
            short_term_investments = self.__account(balance_sheet, 'Short-Term Investments', missing_accounts)
            net_receivables = self.__account(balance_sheet, 'Net Receivables', missing_accounts)
            inventory = self.__account(balance_sheet, 'Inventory', missing_accounts)
            cost_of_revenue = self.__account(income_statement, 'Cost of Revenue', missing_accounts)
            r_and_d = self.__account(income_statement, 'Research and Development', missing_accounts)
            sga = self.__account(income_statement, 'Sales, General and Admin.', missing_accounts)
            if missing_accounts:
                print(f"Defensive Interval Ratio could not be calculated because of missing account data from: {', '.join(missing_accounts)}")
                return None
            total_liquid_assets = cash + short_term_investments + net_receivables
            total_operating_expenses = cost_of_revenue + r_and_d + sga
            daily_operating_expenses = self.__account_series(total_operating_expenses)
            
            if (daily_operating_expenses != 0).all():
                return total_liquid_assets / daily_operating_expenses
            else:
                print("Daily operating expenses contain zero or negative values, cannot compute defensive interval ratio.")
                return None
        return None

    def _fixed_charge_coverage_ratio(self, lease_payments=0):
        statement = self.__prepare_statement('income_statement')
        if statement is not None:
            missing_accounts = []
            ebit = self.__account(statement, 'Earnings Before Interest and Tax', missing_accounts)
            interest_payments = self.__account(statement, 'Interest Expense', missing_accounts)
            if missing_accounts:
                print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                return None
            total_fixed_charges = interest_payments + lease_payments
            if (total_fixed_charges != 0).all():
                return (ebit + lease_payments) / total_fixed_charges
            else:
                print("Total fixed charges contain zero or negative values, cannot compute fixed charge coverage ratio.")
                return None
        return None
    
    def _receivables_turnover_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            periods = income_statement.columns
            for i in range(1, len(periods)):
                current_period = periods[i]
                previous_period = periods[i-1]
                net_receivables_current = self.__account(balance_sheet, 'Net Receivables', missing_accounts, current_period)
                net_receivables_previous = self.__account(balance_sheet, 'Net Receivables', missing_accounts, previous_period)
                total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None    
                average_receivables = (net_receivables_current + net_receivables_previous) / 2
                if average_receivables != 0:
                    ratio = total_revenue / average_receivables
                    ratios[current_period] = ratio
                else:
                    print(f"Average receivables for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _inventory_turnover_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            periods = income_statement.columns
            for i in range(1, len(periods)):
                current_period = periods[i]
                previous_period = periods[i-1]            
                inventory_current = self.__account(balance_sheet, 'Inventory', missing_accounts, current_period)
                inventory_previous = self.__account(balance_sheet, 'Inventory', missing_accounts, previous_period)
                cogs = self.__account(income_statement, 'Cost of Revenue', missing_accounts, current_period)            
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None            
                average_inventory = (inventory_current + inventory_previous) / 2
                if average_inventory != 0:
                    ratio = cogs / average_inventory
                    ratios[current_period] = ratio
                else:
                    print(f"Average inventory for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _days_sales_outstanding(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            days_in_periods = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)        
            date_series = pd.to_datetime(periods)
            for i in range(len(date_series) - 1):
                days_in_periods.append((date_series[i] - date_series[i + 1]).days)
            average_interval = sum(days_in_periods) / len(days_in_periods)
            days_in_periods.append(int(average_interval)) 
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                days_in_period = days_in_periods[i]
                current_receivables = self.__account(balance_sheet, 'Net Receivables', missing_accounts, current_period)
                previous_receivables = self.__account(balance_sheet, 'Net Receivables', missing_accounts, previous_period)
                total_revenue = self.__account(income_statement, 'Total Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_receivables = (current_receivables + previous_receivables) / 2
                if average_receivables != 0:
                    ratio = (average_receivables / total_revenue) * days_in_period
                    ratios[current_period] = ratio
                else:
                    print(f"Average receivables for period {current_period} is zero or negative, cannot compute days sales outstanding ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _days_inventory_on_hand(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')    
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            days_in_periods = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True) 
            date_series = pd.to_datetime(periods)
            for i in range(len(date_series) - 1):
                days_in_periods.append((date_series[i] - date_series[i + 1]).days)
            average_interval = sum(days_in_periods) / len(days_in_periods)
            days_in_periods.append(int(average_interval)) 
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                days_in_period = days_in_periods[i]
                current_inventory = self.__account(balance_sheet, 'Inventory', missing_accounts, current_period)
                previous_inventory = self.__account(balance_sheet, 'Inventory', missing_accounts, previous_period)
                cogs = self.__account(income_statement, 'Cost of Revenue', missing_accounts, current_period)            
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_inventory = (current_inventory + previous_inventory) / 2
                if average_inventory != 0:
                    ratio = (average_inventory / cogs) * days_in_period
                    ratios[current_period] = ratio
                else:
                    print(f"Average inventory for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _payables_turnover_ratio(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')    
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True) 
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                current_payables = self.__account(balance_sheet, 'Accounts Payable', missing_accounts, current_period)
                previous_payables = self.__account(balance_sheet, 'Accounts Payable', missing_accounts, previous_period)
                cogs = self.__account(income_statement, 'Cost of Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_payables = (current_payables + previous_payables) / 2                    
                if average_payables != 0:
                    ratio = cogs / average_payables
                    ratios[current_period] = ratio
                else:
                    print(f"Average payables for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None
       
    def _days_of_payables(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')    
        if income_statement is not None and balance_sheet is not None:
            ratios = {}
            missing_accounts = []
            days_in_periods = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True) 
            date_series = pd.to_datetime(periods)
            for i in range(len(date_series) - 1):
                days_in_periods.append((date_series[i] - date_series[i + 1]).days)
            average_interval = sum(days_in_periods) / len(days_in_periods)
            days_in_periods.append(int(average_interval)) 
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                days_in_period = days_in_periods[i]
                current_payables = self.__account(balance_sheet, 'Accounts Payable', missing_accounts, current_period)
                previous_payables = self.__account(balance_sheet, 'Accounts Payable', missing_accounts, previous_period)
                cogs = self.__account(income_statement, 'Cost of Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None
                average_payables = (current_payables + previous_payables) / 2
                if average_payables != 0:
                    ratio = (average_payables / cogs) * days_in_period
                    ratios[current_period] = ratio
                else:
                    print(f"Average payables for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None           
      
    def _cash_conversion_cycle(self):
        dio = self._days_inventory_on_hand()
        dso = self._days_sales_outstanding()
        dpo = self._days_of_payables()
        ccc = pd.Series(index=dio.index)
        for period in ccc.index:
            missing_components = []        
            if period not in dio:
                missing_components.append("Days Inventory on Hand (DIO)")
            if period not in dso:
                missing_components.append("Days Sales Outstanding (DSO)")
            if period not in dpo:
                missing_components.append("Days of Payables (DPO)")
            if missing_components:
                ccc[period] = None
                print(f"Missing components for period {period}: {', '.join(missing_components)}. Cannot calculate CCC.")
                return None
            else:
                ccc[period] = dio[period] + dso[period] - dpo[period]
        return ccc

    def _return_on_equity(self):
        income_statement = self.__prepare_statement('income_statement')
        balance_sheet = self.__prepare_statement('balance_sheet')
        if income_statement is not None and balance_sheet is not None:    
            missing_accounts = []
            ratios = {}    
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                net_income = self.__account(income_statement, 'Net Income', missing_accounts, current_period)
                current_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts, current_period)
                previous_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts, previous_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_equity = (current_equity + previous_equity) / 2
                if average_equity != 0:
                    ratio = (net_income / average_equity) * 100
                    ratios[current_period] = ratio
                else:
                    print(f"Average equity for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None 

    def _working_capital_turnover(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:    
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            ratios = {}
            missing_accounts = []
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                current_assets = self.__account(balance_sheet, 'Total Current Assets', missing_accounts, current_period)
                previous_assets = self.__account(balance_sheet, 'Total Current Assets', missing_accounts, previous_period)
                current_liabilities = self.__account(balance_sheet, 'Total Current Liabilities', missing_accounts, current_period)
                previous_liabilities = self.__account(balance_sheet, 'Total Current Liabilities', missing_accounts, previous_period)
                net_sales = self.__account(income_statement, 'Total Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_working_capital = (
                    ((current_assets - current_liabilities) +
                     (previous_assets - previous_liabilities)) / 2
                )            
                if average_working_capital != 0:
                    ratio = net_sales / average_working_capital
                    ratios[current_period] = ratio
                else:
                    print(f"Average working capital for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None  

    def _fixed_asset_turnover(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:        
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            missing_accounts = []
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                current_fixed_assets = self.__account(balance_sheet, 'Fixed Assets', missing_accounts, current_period)
                previous_fixed_assets = self.__account(balance_sheet, 'Fixed Assets', missing_accounts, previous_period)
                net_sales = self.__account(income_statement, 'Total Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_fixed_assets = (current_fixed_assets + previous_fixed_assets) / 2
                if average_fixed_assets != 0:
                    ratio = net_sales / average_fixed_assets
                    ratios[current_period] = ratio
                else:
                    print(f"Average fixed assets for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None   

    def _total_asset_turnover(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            missing_accounts = []
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                current_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, current_period)
                previous_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, previous_period)
                net_sales = self.__account(income_statement, 'Total Revenue', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_total_assets = (current_total_assets + previous_total_assets) / 2
                if average_total_assets != 0:
                    ratio = net_sales / average_total_assets
                    ratios[current_period] = ratio
                else:
                    print(f"Average total assets for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None
       
    def _operating_return_on_assets(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            missing_accounts = []
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                operating_income = self.__account(income_statement, 'Operating Income', missing_accounts, current_period)
                current_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, current_period)
                previous_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, previous_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None
                average_total_assets = (current_total_assets + previous_total_assets) / 2            
                if average_total_assets != 0:
                    ratio = (operating_income / average_total_assets) * 100
                    ratios[current_period] = ratio
                else:
                    print(f"Average total assets for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _return_on_assets(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            missing_accounts = []
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                net_income = self.__account(income_statement, 'Net Income', missing_accounts, current_period)
                current_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, current_period)
                previous_total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, previous_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                average_total_assets = (current_total_assets + previous_total_assets) / 2
                if average_total_assets != 0:
                    ratio = (net_income / average_total_assets) * 100
                    ratios[current_period] = ratio
                else:
                    print(f"Average total assets for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _equity_multiplier(self):
        """Calculate and return the Financial Leverage Ratio."""      	
        balance_sheet = self.__prepare_statement('balance_sheet')  
        if balance_sheet is not None:
            missing_accounts = []    
            periods = sorted(balance_sheet.columns, key=pd.to_datetime)
            ratios = {}
            for period in periods:
                total_assets = self.__account(balance_sheet, 'Total Assets', missing_accounts, period)
                total_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts, period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                if total_equity != 0:
                    ratio = total_assets / total_equity
                    ratios[period] = ratio
                else:
                    print(f"Total equity for period {current_period} is zero or negative, cannot compute ratio.")
                    return None                        
            return pd.Series(ratios)
        return None   

    def _return_on_invested_capital_pre_tax(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:
            missing_accounts = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                ebit = self.__account(income_statement, 'Earnings Before Interest and Tax', missing_accounts, current_period)        
                current_portion_long_term_debt = self.__account(balance_sheet, 'Short-Term Debt / Current Portion of Long-Term Debt', missing_accounts, current_period)  
                long_term_debt = self.__account(balance_sheet, 'Long-Term Debt', missing_accounts, current_period)                
                total_debt = current_portion_long_term_debt + long_term_debt      
                total_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts, current_period)
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                total_invested_capital = total_debt + total_equity
                if total_invested_capital != 0:
                    ratio = (ebit / total_invested_capital) * 100
                    ratios[current_period] = ratio
                else:
                    print(f"Total invested capital for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

    def _return_on_invested_capital_after_tax(self):
        balance_sheet = self.__prepare_statement('balance_sheet')  
        income_statement = self.__prepare_statement('income_statement')
        if income_statement is not None and balance_sheet is not None:
            missing_accounts = []
            periods = sorted(balance_sheet.columns, key=pd.to_datetime, reverse=True)
            ratios = {}
            for i in range(len(periods) - 1):
                current_period = periods[i]
                previous_period = periods[i + 1]
                ebit = self.__account(income_statement, 'Earnings Before Interest and Tax', missing_accounts, current_period)
                income_tax = self.__account(income_statement, 'Income Tax', missing_accounts, current_period)                    
                current_portion_long_term_debt = self.__account(balance_sheet, 'Short-Term Debt / Current Portion of Long-Term Debt', missing_accounts, current_period)  
                long_term_debt = self.__account(balance_sheet, 'Long-Term Debt', missing_accounts, current_period)                  
                total_debt = current_portion_long_term_debt + long_term_debt       
                total_equity = self.__account(balance_sheet, 'Total Equity', missing_accounts, current_period)
                effective_tax_rate = income_tax / ebit if ebit != 0 else 0
                if missing_accounts:
                    print(f"Ratio could not be calculated because of missing account data: {', '.join(missing_accounts)}")   
                    return None 
                total_invested_capital = total_debt + total_equity
                if total_invested_capital != 0:
                    ratio = (ebit * (1 - effective_tax_rate) / total_invested_capital) * 100
                    ratios[current_period] = ratio
                else:
                    print(f"Total invested capital for period {current_period} is zero or negative, cannot compute days inventory on hand ratio.")
                    return None                        
            return pd.Series(ratios)
        return None

def __dir__():
    return __all__
