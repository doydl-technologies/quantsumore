# Live CPI retrieval

The inflation calculator fetches the published FRED CPIAUCNS CSV directly. It no longer requests a series HTML page to infer an end date, and it does not send chart styling, vintage or revision parameters. Omitting the end date includes the latest available observations rather than applying a guessed two-month cutoff.

One request uses a 3.05-second connect timeout and a 10-second read timeout. There is no automatic retry loop or key requirement. Provider connectivity can still fail; the client raises CPIDataUnavailableError with the original HTTP, timeout or parsing exception as its cause.

## Use

~~~python
from quantsumore.api import cpi

calculator = cpi.CPI_U.InflationAdjustment
print(calculator.data.attrs)
print(calculator.select(100, 2020, 2024, "January"))
~~~

To open the standalone calculator:

~~~python
from quantsumore.gui import GUI
GUI.run()
~~~

The GUI still loads its data during import. The fetch is now one bounded request; no bundled or synthetic dataset is substituted on failure.

## Data contract

The columns series_id, year, period and value are preserved. The series_id column retains the historical internal label CUUR0000AA0 for compatibility; it is not a BLS series identifier. The DataFrame attrs identify the actual requested FRED series, request URL, UTC fetch time and latest available observation date.

Missing observations marked with a dot are omitted. Invalid dates, duplicate monthly observations, incorrect series columns and nonpositive/nonfinite index values are rejected. Optional start/end bounds apply to the returned observations and their computed averages. Alternate requested series identifiers are now passed through to the CSV request and checked against the returned column.

Average rows retain the existing calculation: the mean of available months, rounded to one decimal. Incomplete years therefore represent available observations, not an estimated full year. The calculator selects its latest available month by calendar order, rather than sorting month names alphabetically.

## Official references

- [FRED CPIAUCNS series](https://fred.stlouisfed.org/series/CPIAUCNS)
- [FRED CSV observations](https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCNS)
- [BLS Python API example using CUUR0000SA0](https://www.bls.gov/developers/api_python.htm)
