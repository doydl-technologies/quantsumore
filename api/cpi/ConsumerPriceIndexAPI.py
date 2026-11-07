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

"""Retrieve CPI data and calculate inflation adjustments."""
from ..prep import cpi_adapter
from .parse._inflation import CUUR0000AA0 


__all__ = ['engine']



class APIClient:
    def __init__(self, adapter):
        self.adapter = adapter
        self.CPI_U = self._CPI_U(self)
       
    def _all_urban(
        self,
        series_id='CPIAUCNS',
    ):  
        """
        Fetches and returns Consumer Price Index (CPI) data for all urban consumers.

        This method retrieves CPI data for all urban consumers based on the specified `series_id`.
        The default `series_id` of 'CPIAUCNS' corresponds to the all-items Consumer Price Index for
        all urban consumers in the United States. The data is fetched, processed, and returned as a 
        DataFrame containing CPI metrics by year and month.

        Parameters:
        ----------
        series_id : str, optional
            The series ID for the CPI data to query. Defaults to 'CPIAUCNS' (all-items CPI for all urban consumers in the U.S.).

        Returns:
        -------
        pandas.DataFrame
            A DataFrame containing the processed CPI data for the requested series. Columns typically include:
            - 'year': The year of the CPI data.
            - 'period': The period or month (e.g., 'January', 'Average').
            - 'value': The CPI value for the specified period.
            Request, HTTP and parsing failures raise CPIDataUnavailableError
            with the underlying error available as its cause. Requests use
            bounded connect/read timeouts rather than scraping an HTML page.
        """    	
        return CUUR0000AA0.Data(series_id=series_id).all_items_index()

    # Internal CPI interface, exposed through APIClient.CPI_U.
    class _CPI_U:
        """Expose inflation calculations through the parent client's CPI retrieval.

        Each InflationAdjustment access fetches CPI data and constructs a helper.
        Availability and observation dates depend on the returned provider data.
        """
        def __init__(self, engine):
            self.engine = engine

        @property
        def InflationAdjustment(self):
            data = self.engine._all_urban()
            return _InflationAdjustment(data)
           
    def __dir__(self):
        return ['CPI_U'] 


# Internal inflation-adjustment helper for the CPI interface.
class _InflationAdjustment:
    """Calculate inflation adjustments from supplied CPI observations.

    data must support the DataFrame operations used for year, period and value
    columns. Month normalization accepts numbers, abbreviations and names.
    Calculations use yearly averages or available monthly observations; select()
    falls back to yearly averages when either requested month is missing.
    """
    def __init__(self, data):
        if data is None:
            raise ValueError("Failed to fetch or process CPI data.")
        self.data = data
        self.max_year = self.data['year'].max()
        self.min_year = self.data['year'].min()
        self.month_map = {
            '1': 'January', '01': 'January', 'January': 'January', 'Jan': 'January',
            '2': 'February', '02': 'February', 'February': 'February', 'Feb': 'February',
            '3': 'March', '03': 'March', 'March': 'March', 'Mar': 'March',
            '4': 'April', '04': 'April', 'April': 'April', 'Apr': 'April',
            '5': 'May', '05': 'May', 'May': 'May',
            '6': 'June', '06': 'June', 'June': 'June',
            '7': 'July', '07': 'July', 'July': 'July',
            '8': 'August', '08': 'August', 'August': 'August', 'Aug': 'August',
            '9': 'September', '09': 'September', 'September': 'September', 'Sep': 'September',
            '10': 'October', 'October': 'October', 'Oct': 'October',
            '11': 'November', 'November': 'November', 'Nov': 'November',
            '12': 'December', 'December': 'December', 'Dec': 'December'
        }
        months = self.data.loc[
            (self.data['year'] == self.max_year) & (self.data['period'] != 'Average'), 'period'
        ].map(self._normalize_month)
        if months.empty or months.isna().any():
            raise ValueError("CPI data must contain valid monthly observations for its latest year.")
        month_order = {self.month_map[str(number)]: number for number in range(1, 13)}
        self.current_month = max(months, key=month_order.__getitem__)

    def _normalize_month(self, month_input):
        """
        Normalizes a month input to a standard month name used in the CPI data.

        This method takes various representations of a month (numeric strings, abbreviations, or full names)
        and converts them to a canonical month name that matches the format used in the CPI DataFrame.

        Parameters:
        ----------
        month_input : str or int
            The month input to normalize. Can be a numeric string (e.g., '03', '3'), 
            a full month name (e.g., 'March'), or a common abbreviation (e.g., 'Mar').

        Returns:
        -------
        str or None
            The standardized month name (e.g., 'March'), or None if the input could not be matched.
        """
        month_input = str(month_input).capitalize()
        return self.month_map.get(month_input, None)

    def _validate(self, amount=None, year=None, month=None, n_years=None):
        """
        Validates and converts input parameters for inflation adjustment calculations.

        This method checks and converts the provided parameters to the correct types, and ensures that
        all values are within valid ranges for CPI calculations. Raises descriptive ValueErrors if any
        validation fails.

        Parameters:
        ----------
        amount : float or None, optional
            The monetary amount to validate and convert to float, if provided.
        year : int or None, optional
            The year to validate and convert to int, if provided. Must be within the range of available CPI years.
        month : str or None, optional
            The month to validate and normalize, if provided. Accepted values include numeric strings, abbreviations, or full names.
        n_years : int or None, optional
            The number of years for a year-by-year calculation. Must be a non-negative integer if provided.

        Returns:
        -------
        tuple
            A tuple containing the validated and converted (amount, year, month, n_years) values.

        Raises:
        ------
        ValueError
            If any of the input parameters are of an incorrect type or outside of valid ranges.
        """
        if amount is not None:
            try:
                amount = float(amount)
            except ValueError:
                raise ValueError("Amount must be a number.")
        if year is not None:
            try:
                year = int(year)
            except ValueError:
                raise ValueError("Year must be a numeric value.")
            if year > self.max_year or year < self.min_year:
                raise ValueError(f"Year must be between {self.min_year} and {self.max_year}.")
        if month is not None:
            month = self._normalize_month(month)
            if month is None:
                raise ValueError("Please enter a valid month.")
        if n_years is not None:
            try:
                n_years = int(n_years)
            except ValueError:
                raise ValueError("n_years must be a numeric value.")
            if n_years < 0:
                raise ValueError("n_years must be a non-negative integer.")
        return (amount, year, month, n_years)

    def _get_cpi(self, year, period='Average'):
        """
        Retrieves the Consumer Price Index (CPI) value for a given year and period.

        This method looks up the CPI value in the data for the specified year and period
        (month or 'Average'). If a matching entry is found, the corresponding CPI value is returned;
        otherwise, returns None.

        Parameters:
        ----------
        year : int
            The year for which to retrieve the CPI value.
        period : str, optional
            The period (typically a month name or 'Average') for which to retrieve the CPI.
            Defaults to 'Average'.

        Returns:
        -------
        float or None
            The CPI value for the specified year and period, or None if not available.
        """
        cpi_value = self.data[(self.data['year'] == year) & (self.data['period'] == period)]['value']
        return cpi_value.iloc[0] if not cpi_value.empty else None

    def select(self, original_amount, original_year, target_year, month_input):
        """
        Calculates and returns the inflation-adjusted value for a given amount and time period.

        This method computes the equivalent value of a specified amount of money from one year
        in the dollars of another year, optionally using a specific month. If data for the exact
        month is unavailable, the calculation defaults to yearly averages.

        Parameters:
        ----------
        original_amount : float
            The amount of money to adjust for inflation.
        original_year : int
            The year from which the original amount originates.
        target_year : int
            The year to which the amount should be adjusted.
        month_input : str
            The month for the calculation (e.g., "January", "03", "Mar"), or 'Average' to use the yearly average.

        Returns:
        -------
        float
            The adjusted value in the target year's dollars, rounded to two decimal places.
        """
        original_amount, original_year, month, _  = self._validate(amount=original_amount, year=original_year, month=month_input)
        _, target_year, _, _ = self._validate(year=target_year)

        cpi_original = self._get_cpi(original_year, month)
        cpi_target = self._get_cpi(target_year, month)

        # If either CPI data point is missing, default both to yearly averages and alert the user
        if cpi_original is None or cpi_target is None:
            print(f"Since we do not have the month value for {month} {target_year if cpi_target is None else original_year}, we will be switching to averages of the years.")
            cpi_original = self._get_cpi(original_year)
            cpi_target = self._get_cpi(target_year)

        if cpi_original is None or cpi_target is None:
            raise ValueError("CPI data not available for the provided dates.")

        adjusted_value = (original_amount / cpi_original) * cpi_target
        print(f"${original_amount:.2f} from {original_year} is equivalent to ${adjusted_value:.2f} in {target_year} dollars.")
        return round(adjusted_value, 2)

    def year_by_year(self, original_amount, n_years):
        """
        Calculates the inflation-adjusted value of an amount for each year over a specified period.

        This method computes the equivalent value of a given amount in each of the past `n_years`,
        relative to the most recent CPI data. Adjustments use monthly data when available,
        or fallback to yearly averages.

        Parameters:
        ----------
        original_amount : float
            The original amount of money to evaluate.
        n_years : int
            The number of years back from the most current year to include in the calculation.

        Returns:
        -------
        dict
            A dictionary where each key is a year and the value is the inflation-adjusted amount
            for that year, rounded to two decimal places.
        """
        original_amount, _, _, n_years = self._validate(amount=original_amount, n_years=n_years)
        results = {}
        current_cpi = self._get_cpi(self.max_year, self.current_month) or self._get_cpi(self.max_year, 'Average')
        target_years = range(self.max_year - n_years, self.max_year)
        for year in target_years:
            month_cpi = self._get_cpi(year, self.current_month)
            if not month_cpi:
                month_cpi = self._get_cpi(year, 'Average')
                print(f"Month-specific CPI for {self.current_month} {year} not available, using yearly average.")
            if month_cpi:
                adjusted_value = (original_amount / month_cpi) * current_cpi
                results[year] = round(adjusted_value, 2)
        return results

    def month_by_month(self, amount):
        """
        Calculates the value of a specified amount for each month of the current year using CPI data.

        This method evaluates the given amount against the Consumer Price Index for each month of
        the most recent year available, showing how the value changes with inflation throughout the year.

        Parameters:
        ----------
        amount : float
            The amount of money to adjust using monthly CPI values.

        Returns:
        -------
        dict
            A dictionary where each key is a month and the value is the equivalent amount
            in the most current month's dollars, rounded to two decimal places.
        """
        amount = self._validate(amount=amount)[0]
        results = {}
        monthly_data = self.data[(self.data['year'] == self.max_year) & (self.data['period'] != 'Average')]
        current_cpi = self._get_cpi(self.max_year, self.current_month)

        for _, row in monthly_data.iterrows():
            month = row['period']
            cpi_value = row['value']
            if current_cpi:
                adjusted_value = (amount / cpi_value) * current_cpi
                results[month] = round(adjusted_value, 2)
            else:
                results[month] = 'CPI data missing for current month'
        return results

    def __dir__(self):
        return ['select', 'year_by_year', 'month_by_month', 'data']


engine = APIClient(cpi_adapter)

def __dir__():
    return __all__




