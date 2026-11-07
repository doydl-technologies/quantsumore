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

from datetime import datetime as dt, timedelta as td, date as d, timezone as tmz
import re

from .proxy import Proxy

__all__ = ['dtparse']




# Defer dependency imports until first use.
pd = Proxy("pandas", None)
np = Proxy("numpy")


class dt_parse:
    # Default formats used when resetting the parser.
    DEFAULT_DATE_FORMATS = [
        '%Y.%m.%d', '%m.%d.%Y', '%B %d, %Y', '%b %d, %Y',
        '%d.%m.%Y', '%d %b %Y', '%d %B %Y', '%b %d %Y',
        '%Y%m%d',  '%d%m%Y',  '%A, %B %d %Y', '%Y-%m-%dT%H:%M:%SZ',
        '%a, %d %b %Y %H: %M:%S', '%Y-%m', '%Y-%m-%d %H:%M',
        '%Y-%m-%d %I:%M %p', '%Y-%m-%d %H:%M:%S', '%a, %d %b %Y', 
        '%Y-%m-%d %H:%M:%S.%f', '%a, %d %b %Y %H:%M:%S',
    ]

    def __init__(self):
        """Initialize date formats, the ISO regex and timezone/substitution helpers.

        Cache the last successful format and keep separate format lists for
        dot-inclusive and dot-exclusive inputs.
        """
        self.date_formats = list(self.DEFAULT_DATE_FORMATS)
        self._refresh_format_lists()
        self.iso_format = re.compile(
            r'^'
              r'\d{4}-\d{2}-\d{2}'            # date
              r'T'
              r'\d{2}:\d{2}:\d{2}'            # time
              r'(?:\.\d+)?'                   # optional fractional
              r'(?:Z|[+-]\d{2}:\d{2})?'       # Z or +HH:MM or -HH:MM
            r'$'
        )
        self.formats_with_dots = [fmt for fmt in self.date_formats if '.' in fmt]
        self.formats_without_dots = [fmt for fmt in self.date_formats if '.' not in fmt]
        self.last_successful_format = None
    
        self.ET = self.EasternTime(self)         
        self.sub = self.SubstituteClass(self)           

    _DIRECTIVE_CHARS = 'aAbBpPzZxXwWdDmMyYHIfSjUWCcGguV'   # Single-letter format directives.
    _FLAG_CHARS      = '-_0'                               # Supported padding flags.
    _MISSING_PERCENT = re.compile(
        rf'''(?<!%)                 # not already a directive
            (?P<flag>(?<![A-Za-z])  # flag allowed only if the char in front
            [{_FLAG_CHARS}])?       #   isn’t a letter (so dash in “Y-m-d” is safe)
            (?P<dir>[{_DIRECTIVE_CHARS}])
        ''',
        re.VERBOSE
    )    
    _MULTI_SPACE  = re.compile(r'\s+')
    _AROUND_COLON = re.compile(r'\s*:\s*')    
    
    @staticmethod        
    def _clean_whitespace(date_string):
        """
        Normalize whitespace in an input:
          - If it's a list/tuple, join its items with single spaces.
          - Collapse any run of whitespace (tabs, newlines, multiple spaces) into one space.
          - Remove *all* spaces immediately before *and* after colons (e.g. "00:  00:00" → "00:00:00").
          - Trim leading/trailing whitespace.
        """
        if isinstance(date_string, (list, tuple)):
            s = ' '.join(str(x) for x in date_string)
        else:
            s = str(date_string)

        s = dt_parse._MULTI_SPACE.sub(' ', s)

        s = dt_parse._AROUND_COLON.sub(':', s)

        return s.strip()
    
    @staticmethod    
    def _normalize_format(fmt: str) -> str:
        """
        Normalize a datetime format string by injecting missing '%' symbols.

        Parameters:
        -----------
            fmt : str
                A shorthand datetime format string, possibly missing percent signs
                (e.g., "Y-m-d" instead of "%Y-%m-%d").

        Returns:
        -----------
            str : A fully normalized format string compatible with `strptime`.

        Notes:
        -----------
            If the input already contains a percent sign ('%'), it is returned unchanged.
            Otherwise, this method adds a leading '%' to any valid directive and its optional flag.
        """
        # If the user has already typed any ‘%’, treat the pattern as complete.
        if '%' in fmt:
            return fmt

        # Insert missing format-directive markers.
        return dt_parse._MISSING_PERCENT.sub(
            lambda m: '%' + (m.group('flag') or '') + m.group('dir'),
            fmt
        )

    def _refresh_format_lists(self):
        """Rebuild dot-inclusive and dot-exclusive format lists.

        Called during initialization and by add()/flush() after changing the
        configured formats. These lists select the format search order.
        """
        self.formats_with_dots    = [f for f in self.date_formats if '.' in f]
        self.formats_without_dots = [f for f in self.date_formats if '.' not in f]
        
    def _is_date_str(self, text):
        """Return whether a string contains a recognized strftime/strptime directive.

        Non-string inputs return False.
        """
        date_format_string_pattern = re.compile(r"%[aAbBcdHImMpSUwWxXyYZ]")
        if not isinstance(text, str):
            return False
        return bool(date_format_string_pattern.search(text))

    def _is_datetimeType(self, obj, format='%Y-%m-%d', strf=False):
        """
        Determine if an object is date-like or datetime-like.

        Parameters:
        -----------
            obj : Any
                The object to evaluate for date or datetime-like attributes.
            
            format : str, optional
                Format string to use if `strf` is True. Defaults to '%Y-%m-%d'.

            strf : bool, optional
                If True, return the object formatted as a string using `format`.
                If False, return a boolean indicating date-likeness.

        Returns:
        -----------
            bool or str : 
                - If `strf` is True and the object is date-like or datetime-like, returns a formatted string.
                - If `strf` is False, returns True if the object has date/datetime attributes, else False.

        Notes:
        -----------
            A datetime-like object must have all of: year, month, day, hour, minute, second, microsecond.
            A date-like object must have year, month, and day only.
        """
        date_attrs = {'year', 'month', 'day'}
        datetime_attrs = date_attrs.union({'hour', 'minute', 'second', 'microsecond'})

        if all(hasattr(obj, attr) for attr in datetime_attrs):
            if strf:
                return obj.strftime(format)
            return True
        elif all(hasattr(obj, attr) for attr in date_attrs) and not any(hasattr(obj, attr) for attr in datetime_attrs - date_attrs):
            if strf:
                return obj.strftime(format)
            return True
        return False

    def _from_pywintypes_datetime(self, obj):
        """
        Convert a `pywintypes.datetime` object to a standard `datetime.datetime`.

        Parameters:
        -----------
            obj : Any
                The object to attempt to convert.

        Returns:
        -----------
            datetime.datetime or original object :
                A converted `datetime.datetime` object if `obj` is a `pywintypes.datetime` or has datetime-like attributes;
                otherwise, returns the original object unchanged.

        Notes:
        -----------
            This method is useful when interoperating with Windows COM objects that expose
            `pywintypes.datetime`. It will preserve `tzinfo` if available.
        """
        # Accept Windows COM datetimes and compatible objects with datetime attributes.
        if ((type(obj).__module__ == "pywintypes" and type(obj).__name__ == "datetime") or
            (hasattr(obj, "year") and hasattr(obj, "microsecond") and (hasattr(obj, "tzinfo") or hasattr(obj, "day")))):
            tzinfo = getattr(obj, 'tzinfo', None)
            return dt(
                obj.year,
                obj.month,
                obj.day,
                obj.hour,
                obj.minute,
                obj.second,
                obj.microsecond,
                tzinfo=tzinfo
            )
        return obj

    def _is_iso(self, text):
        """Match the configured ISO datetime pattern, including its timezone suffix.

        Accepts optional fractional seconds followed by Z or an explicit offset.
        """
        if not isinstance(text, str):
            return False
        return bool(self.iso_format.match(text))        

    def _add_missing_seconds(self, date_str):
        """
        Normalize datetime strings by ensuring seconds are present in the time portion.

        Parameters:
        -----------
            date_str : str
                A string that may contain a date and time (e.g., "2024-01-01 12:34").

        Returns:
        -----------
            str : A modified string with seconds included in the time portion if:
                  - The time portion is present, and
                  - The prefix is a parseable date.
                  Otherwise, returns the original string unchanged.

        Notes:
        -----------
            The function performs the following:
              1. Strips excessive whitespace.
              2. Uses regex to extract date and time parts.
              3. Verifies if the prefix is a valid date using `self.parse()`.
              4. Adds ":00" if seconds are missing from the time.
              5. Preserves microseconds if present.
        """
        cleaned = " ".join(date_str.split())
        
        pattern = r'^(?P<prefix>.*?)\s*(?P<time>(?P<hours>\d{1,2}):(?P<minutes>\d{2})(?::(?P<seconds>\d{2})(?:\.(?P<microseconds>\d+))?)?)\s*$'
        time_regex = re.compile(pattern)
        match = time_regex.search(cleaned)
        
        if not match:
            return date_str

        prefix = match.group("prefix")
        
        # Parse the date prefix without re-entering second padding.
        if prefix:
            try:
                parsed_date = self.parse(prefix, _skip_missing=True)
            except Exception:
                # Leave unrecognized date prefixes unchanged.
                return date_str
            if not isinstance(parsed_date, dt):
                return date_str

        hours = match.group("hours")
        minutes = match.group("minutes")
        seconds = match.group("seconds")
        microseconds = match.group("microseconds")

        if seconds is None:
            seconds = "00"

        new_time_str = f"{hours}:{minutes}:{seconds}"
        if microseconds:
            new_time_str += f".{microseconds}"

        if prefix:
            new_str = prefix.strip() + " " + new_time_str
        else:
            new_str = new_time_str

        return new_str
        
    def parse(self, date_input, *, from_format=None, to_format=None,
              to_unix_timestamp=False, include_timezone=False,
              timezone_offset='+00:00', keep_time=True,
              _skip_missing=False):          # Prevent recursive second-padding while parsing the date prefix.
        """
        Parse and convert date inputs into datetime objects, strings, or Unix timestamps.

        This method supports flexible parsing of individual or batch date inputs, allowing
        optional formatting, Unix timestamp conversion, and ISO-8601 support.

        Parameters:
        -----------
            date_input : str, datetime, list, np.ndarray, or pd.Series
                The input date(s) to parse or convert.

            from_format : str, optional
                A format string used to explicitly parse the input. If not provided, the
                parser will attempt to infer the format.

            to_format : str, optional
                A format string used to convert the parsed result into a formatted string.

            to_unix_timestamp : bool, optional
                If True, return the result as a Unix timestamp (seconds since epoch).

            include_timezone : bool, optional
                If True, preserve timezone info (only applies to ISO strings). Defaults to False.

            timezone_offset : str, optional
                Timezone offset to use when constructing ISO 8601 strings. Defaults to '+00:00'.

            keep_time : bool, optional
                If False, strip time info and return only the date. Defaults to True.

            _skip_missing : bool, optional
                Internal use only. If True, skips automatic time normalization.

        Returns:
        -----------
            datetime.datetime, str, int, list, or pd.Series :
                The parsed result, which may be:
                - a datetime object
                - a formatted string
                - a Unix timestamp
                - a list or Series of any of the above, depending on input type

        Raises:
        -----------
            ValueError : If the input format cannot be recognized or conversion fails.

        Notes:
        -----------
            - This parser can automatically patch incomplete time strings (e.g., missing seconds).
            - If `from_format` is not provided, all known formats are tried in order.
            - The method is optimized to reuse the last successful format to speed up repeated parsing.
            - ISO 8601 strings ending in 'Z' are interpreted as UTC.
        """
        def _parser(date_string):
            date_str = re.sub(r'(?<=\d{2}):(\d{3,6})$', r'.\1', date_string) # Fix nonstandard microseconds
            
            # 1. Try last successful format first (if it exists)            
            if self.last_successful_format:
                try:
                    parsed_date = dt.strptime(date_str, self.last_successful_format)
                    if to_unix_timestamp:
                        return int(parsed_date.timestamp())
                    if not from_format and self._is_date_str(to_format):
                        return parsed_date.strftime(to_format)
                    return parsed_date
                except ValueError:
                    pass

            # 2. Try all known formats                   
            for format_list in [self.formats_with_dots, self.formats_without_dots]:
                for date_format in format_list:
                    try:
                        parsed_date = dt.strptime(date_str, date_format)
                        self.last_successful_format = date_format
                        if to_unix_timestamp:
                            return int(parsed_date.timestamp())
                        if not from_format and self._is_date_str(to_format):
                            return parsed_date.strftime(to_format)
                        return parsed_date
                    except ValueError:
                        continue

            # 3. Try alternate separators ('.' → '/' or '-') if needed                    
            new_separators = ['/', '-']            
            for sep in new_separators:
                for date_format in self.formats_with_dots:
                    new_format = date_format.replace('.', sep)
                    try:
                        parsed_date = dt.strptime(date_str, new_format)
                        self.last_successful_format = new_format
                        if to_unix_timestamp:
                            return int(parsed_date.timestamp())
                        if not from_format and self._is_date_str(to_format):
                            return parsed_date.strftime(to_format)
                        return parsed_date
                    except ValueError:
                        continue

            if from_format and to_format:
                try:
                    parsed_date = dt.strptime(date_str, from_format)
                    if to_unix_timestamp:
                        return int(parsed_date.timestamp())
                    formatted_date = parsed_date.strftime(to_format)
                    return formatted_date
                except ValueError:
                    raise ValueError("Date format not recognized and fallback failed.")
                
            elif from_format:
                try:
                    parsed_date = dt.strptime(date_str, from_format)
                    if to_unix_timestamp:
                        return int(parsed_date.timestamp())
                    return parsed_date
                except ValueError:
                    raise ValueError("Date format not recognized.")
            raise ValueError("Date format not recognized.")
        
        if isinstance(date_input, str):
            date_input = self._clean_whitespace(date_input)
        
        # 1. Handle Win32 objects (e.g., pywintypes.datetime)
        date_input = self._from_pywintypes_datetime(date_input)     
        
        # 2. Pad missing seconds (only if not skipped and input is str)
        if (not _skip_missing
                and isinstance(date_input, str)
                and not self._is_datetimeType(date_input)):
            date_input = self._add_missing_seconds(date_input)

        if self._is_datetimeType(date_input):
            if to_unix_timestamp:
                return int(date_input.timestamp())
            if to_format and self._is_date_str(to_format):
                return date_input.strftime(to_format)
            return date_input        

        # 4. If ISO-8601 (UTC-Z), parse with optional timezone inclusion        
        if isinstance(date_input, str) and self._is_iso(date_input):
            iso_str = date_input
            if iso_str.endswith('Z'):
                iso_str = iso_str[:-1] + '+00:00'
            parsed = dt.fromisoformat(iso_str)
            if not include_timezone and parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            if to_unix_timestamp:
                return int(parsed.timestamp())
            if to_format:
                return parsed.strftime(to_format)
            return parsed if keep_time else parsed.date()       

        # 5. General parsing for str, list, np.ndarray, or pd.Series                
        try:
            if isinstance(date_input, str):
                return _parser(date_input)
            elif isinstance(date_input, list) or isinstance(date_input, np.ndarray):
                return [_parser(date_str) for date_str in date_input]
            elif isinstance(date_input, pd.Series):
                date_input = date_input.astype(str)
                return date_input.apply(_parser)
        except ValueError as e:
            if not _skip_missing:
                raise ValueError(f"Cannot parse due to error: {e}")
            return        

    class EasternTime:
        def __init__(self, parent):
            self.parent = parent
            
        def isDST(self, date_value=None):
            """
            Determine whether a given date falls within Daylight Saving Time (DST) in Eastern Time.

            Parameters:
            -----------
                date_value : datetime.datetime, optional
                    The date to evaluate. If None, the current UTC time is used.

            Returns:
            -----------
                bool : True if the date falls within the DST period (EDT); otherwise False.

            Notes:
            -----------
                DST is defined as the period from the second Sunday in March
                to the first Sunday in November, starting at 2:00 AM.
            """       	
            date_value = date_value if date_value else dt.utcnow()
            dst_start = dt(date_value.year, 3, 8)
            dst_end = dt(date_value.year, 11, 1) 
            while dst_start.weekday() != 6: 
                dst_start += td(days=1)
            while dst_end.weekday() != 6:
                dst_end += td(days=1)
            dst_start = dst_start.replace(hour=2)
            dst_end = dst_end.replace(hour=2)
            return dst_start <= date_value < dst_end 

        def now(self):
            """Return naive Eastern local time by offsetting current UTC for DST.

            The returned datetime has no timezone metadata.
            """
            now_utc = dt.utcnow()
            year = now_utc.year
            dst_start = dt(year, 3, 8, 2) + td(days=(6 - dt(year, 3, 8, 2).weekday()))
            dst_end = dt(year, 11, 1, 2) + td(days=(6 - dt(year, 11, 1, 2).weekday()))
            if dst_start <= now_utc.replace(tzinfo=None) < dst_end:
                offset = td(hours=-4) # Eastern Daylight Time (UTC-4)
            else:
                offset = td(hours=-5) # Eastern Standard Time (UTC-5)
            now_est_edt = now_utc + offset
            return now_est_edt

        def nowOffset(self, datetime_datetime_obj=None):
            """
            Get the UTC offset for Eastern Time in hours.

            Parameters:
            -----------
                datetime_datetime_obj : datetime.datetime, optional
                    A datetime object with timezone info. If provided and timezone-aware,
                    its UTC offset is used. Otherwise, the offset is computed from the current time.

            Returns:
            -----------
                float : UTC offset in hours (-4.0 for EDT or -5.0 for EST).

            Notes:
            -----------
                If no datetime is provided or the object lacks timezone info,
                this method infers the offset using the current UTC time and DST rules.
            """      	
            def has_timezone(dte):
                if isinstance(dte, dt):
                    return isinstance(dt.tzinfo, tmz)
                else:
                    return None
            if datetime_datetime_obj:
                if has_timezone(datetime_datetime_obj):
                    offset = datetime_datetime_obj.utcoffset()
                    offset_seconds = offset.total_seconds()
                    return offset_seconds/3600
            now_utc = dt.utcnow()
            year = now_utc.year
            dst_start = dt(year, 3, 8, 2) + td(days=(6 - dt(year, 3, 8, 2).weekday()))
            dst_end = dt(year, 11, 1, 2) + td(days=(6 - dt(year, 11, 1, 2).weekday()))
            if dst_start <= now_utc.replace(tzinfo=None) < dst_end:
                return -4 # Eastern Daylight Time (UTC-4)
            else:
                return -5 # Eastern Standard Time (UTC-5)
            return 0
    
        def __dir__(self):
            return ['isDST', 'now', 'nowOffset'] 
    
    class SubstituteClass:
        def __init__(self, parent):        
            """Store the parent date parser used to validate substitutions."""
            self.parent = parent                    
            self.time = self.TimeClass(self.parent).time                                  
        
        class TimeClass:
            def __init__(self, parent):
                self.parent = parent
        	
            def time(self, date_str, hours=None, minutes=None, seconds=None, microseconds=None):
                """
                Inject or modify time components in a datetime string.

                This method:
                  1. Extracts a time substring from the input string if present.
                  2. Verifies that the date portion is valid and parseable.
                  3. Replaces or appends time components (hours, minutes, seconds, microseconds).
                  4. Returns the updated string if valid, otherwise returns the original input.

                Parameters:
                -----------
                    date_str : str
                        A string containing a date and optionally a time portion.
                    
                    hours : str or int, optional
                        Override value for hours (default is parsed or "00").
                    
                    minutes : str or int, optional
                        Override value for minutes (default is parsed or "00").
                    
                    seconds : str or int, optional
                        Override value for seconds (default is parsed or None).
                    
                    microseconds : str or int, optional
                        Override value for microseconds (default is parsed or None).

                Returns:
                -----------
                    str : A modified datetime string with updated time components,
                          or the original string if parsing fails.

                Notes:
                -----------
                    - If no time is found but the string is date-parseable, time will be appended.
                    - Microseconds are padded to 6 digits when provided.
                    - Useful for programmatically filling in or correcting time data.
                """
                pattern = (
                    r'^(?P<prefix>.*?)\s*'                # capture anything (non-greedy) until whitespace
                    r'(?P<time>'
                    r'(?P<hours>\d{1,2}):(?P<minutes>\d{2})'
                    r'(?:'
                    r':(?P<seconds>\d{2})'
                    r'(?:\.(?P<microseconds>\d+))?'
                    r')?'
                    r')\s*$'
                )
                time_regex = re.compile(pattern)
                cleaned_date_str = " ".join(date_str.split())
                match = time_regex.search(cleaned_date_str)
                
                if match:
                    prefix = match.group("prefix")
                    try:
                        parsed_date = self.parent.parse(prefix)
                    except Exception:
                        return date_str
                    if not isinstance(parsed_date, dt):
                        return date_str

                    parts = match.groupdict()
                    found_hours = parts.get("hours")
                    found_minutes = parts.get("minutes")
                    found_seconds = parts.get("seconds")
                    found_microseconds = parts.get("microseconds")
                    final_hours = str(hours) if hours is not None else found_hours
                    final_minutes = str(minutes) if minutes is not None else found_minutes
                    final_seconds = str(seconds) if seconds is not None else found_seconds
                    final_microseconds = str(microseconds) if microseconds is not None else found_microseconds
                    if final_microseconds is not None:
                        final_microseconds = final_microseconds.ljust(6, '0')
                        
                    new_time_str = f"{final_hours}:{final_minutes}"
                    if final_seconds is not None:
                        new_time_str += f":{final_seconds}"
                        if final_microseconds is not None:
                            new_time_str += f".{final_microseconds}"

                    time_start, time_end = match.span("time")
                    new_str = cleaned_date_str[:time_start] + new_time_str + cleaned_date_str[time_end:]
                    return new_str

                else:
                    try:
                        parsed_date = self.parent.parse(cleaned_date_str)                    	
                    except Exception:
                        return date_str
                    if not isinstance(parsed_date, dt):
                        return date_str

                    final_hours = str(hours) if hours is not None else "00"
                    final_minutes = str(minutes) if minutes is not None else "00"
                    final_seconds = str(seconds) if seconds is not None else "00"
                    final_microseconds = None
                    if microseconds is not None:
                        final_microseconds = str(microseconds).ljust(6, '0')
                    new_time_str = f"{final_hours}:{final_minutes}:{final_seconds}"
                    if final_microseconds:
                        new_time_str += f".{final_microseconds}"
                        
                    return f"{cleaned_date_str} {new_time_str}"

        def __dir__(self):
            return ['time'] 
           
    def add(self, *formats):
        """
        Add one or more new date format strings to the parser.

        Parameters:
        -----------
            *formats : str
                One or more datetime format strings. If any directive characters are
                missing a leading '%', they will be automatically corrected.

        Notes:
        -----------
            Duplicate formats are ignored. After new formats are added, the
            internal dot-sensitive format lists are refreshed.
        """
        for raw in formats:
            fmt = self._normalize_format(raw)
            if fmt not in self.date_formats:
                self.date_formats.append(fmt)
        self._refresh_format_lists()        

    def flush(self, successful_reset=False):
        """Restore the default formats and rebuild the format search lists.

        successful_reset=True also clears the last successful format; the default
        False retains that cached format.
        """
        self.date_formats = list(self.DEFAULT_DATE_FORMATS)
        self._refresh_format_lists()
        if successful_reset:
            self.last_successful_format = None  
            
    def now(self, utc=False, as_unix=False, format=None, date_only=False):
        """Get the current date and time in local or UTC format.

        Parameters:
        -----------
            utc : bool, optional
                If True, returns the current UTC time. Defaults to False.

            as_unix : bool, optional
                If True, returns the time as a Unix timestamp (int). Defaults to False.

            format : str, optional
                If provided, returns the date/time formatted as a string.

            date_only : bool, optional
                If True, returns only the date (no time component). Defaults to False.

        Returns:
        -----------
            datetime.datetime, datetime.date, int, or str :
                - A `datetime` object (default),
                - A `date` object (if `date_only=True` and no format),
                - A Unix timestamp (if `as_unix=True`),
                - A formatted string (if `format` is provided).
        """
        current = dt.utcnow() if utc else dt.now()
        if date_only:
            if as_unix:
                # Strip time, then return unix timestamp at midnight
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)
                return self.unix_timestamp(current)
            if format:
                return current.strftime(format)
            return current.date()
        if as_unix:
            return self.unix_timestamp(current)
        return current.strftime(format) if format else current

    def nowCT(self, as_unix=False, format=None, date_only=False):
        """
        Get the current time in U.S. Central Time (CT), adjusting for DST.

        Parameters:
        -----------
            as_unix : bool, optional
                If True, returns the time as a Unix timestamp. Defaults to False.

            format : str, optional
                If provided, returns the CT time as a formatted string.

            date_only : bool, optional
                If True, returns only the date (no time component). Defaults to False.

        Returns:
        -----------
            datetime.datetime, datetime.date, int, or str :
                - A `datetime` object (default),
                - A `date` object (if `date_only=True` and no format),
                - A Unix timestamp (if `as_unix=True`),
                - A formatted string (if `format` is provided).

        Notes:
        -----------
            - Automatically applies DST adjustment (UTC-5 or UTC-6 depending on date).
            - Relies on `EasternTime.isDST()` for determining DST applicability.
        """
        now_utc = dt.utcnow()
        if self.EasternTime.isDST(now_utc):
            current = now_utc - td(hours=5)  # UTC-5 for DST
        else:
            current = now_utc - td(hours=6)  # UTC-6 for Standard Time

        if date_only:
            if as_unix:
                # Midnight timestamp for the current date in CT
                current = current.replace(hour=0, minute=0, second=0, microsecond=0)
                return self.unix_timestamp(current)
            if format:
                return current.strftime(format)
            return current.date()

        if as_unix:
            return self.unix_timestamp(current)
        return current.strftime(format) if format else current

    def make_timezone_aware(self, date_value, offset_hours):
        """
        Convert a naive datetime object into a timezone-aware one.

        Parameters:
        -----------
            date_value : datetime.datetime
                A naive (timezone-unaware) datetime object.

            offset_hours : int or float
                The UTC offset to apply, in hours (e.g., -5 for EST).

        Returns:
        -----------
            datetime.datetime : A timezone-aware datetime object with the specified UTC offset.

        Notes:
        -----------
            If the input datetime already has `tzinfo`, it is returned unchanged.
        """
        if date_value.tzinfo is not None:
            return date_value
        tz = tmz(td(hours=offset_hours))
        return date_value.replace(tzinfo=tz)

    def unix_timestamp(self, date_value, format=None, utc=False, reset_time=False, to_unix=True, assume_utc_if_naive=False):
        """Convert between Unix timestamps and datetime objects or strings.

        Parameters:
        -----------
            date_value : datetime.datetime, int, or str
                - If `to_unix=True`: A datetime object or parseable date string.
                - If `to_unix=False`: An integer Unix timestamp to convert.

            format : str, optional
                If converting from Unix to a string, apply this output format.

            utc : bool, optional
                If True, treat the input/output as UTC-based. Defaults to False.

            reset_time : bool, optional
                If True, zero out the time component (00:00:00). Defaults to False.

            to_unix : bool, optional
                If True, convert datetime to Unix timestamp. If False, convert Unix to datetime.
                Defaults to True.

            assume_utc_if_naive : bool, optional
                If True and `utc=True`, assume naive datetime values are UTC.
                Otherwise, they are treated as local. Defaults to False.

        Returns:
        -----------
            int | datetime.datetime | str :
                - Integer Unix timestamp,
                - Datetime object,
                - Or formatted string depending on parameters.

        Raises:
        -----------
            ValueError : If input types are invalid or conversion fails.
        """
        if not isinstance(date_value, (int, dt)):
            try:
                date_value = self.parse(date_value)
            except Exception:
                raise ValueError("Expected datetime object or integer for Unix timestamp conversion.")

        if to_unix:
            if not isinstance(date_value, dt):
                raise ValueError("Expected datetime object for Unix timestamp conversion.")

            datetime_obj = date_value

            if utc:
                if datetime_obj.tzinfo is None:
                    if assume_utc_if_naive:
                        datetime_obj = datetime_obj.replace(tzinfo=tmz.utc)
                    else:
                        datetime_obj = datetime_obj.astimezone(tmz.utc)
                else:
                    datetime_obj = datetime_obj.astimezone(tmz.utc)

            if reset_time:
                datetime_obj = datetime_obj.replace(hour=0, minute=0, second=0, microsecond=0)

            return int(datetime_obj.timestamp())

        else:
            if not isinstance(date_value, int):
                raise ValueError("Expected integer Unix timestamp for conversion to datetime.")

            datetime_obj = dt.fromtimestamp(date_value, tmz.utc if utc else None)

            if format:
                return datetime_obj.strftime(format)
            return datetime_obj      

    def subtract_months(self, date_str, months):
        """
        Subtract a given number of months from a date string.

        Parameters:
        -----------
            date_str : str
                The input date in '%Y-%m-%d' format.

            months : int
                Number of months to subtract from the date.

        Returns:
        -----------
            str : A new date string in '%Y-%m-01' format, representing the first
                  day of the resulting month.

        Notes:
        -----------
            Automatically adjusts for year rollover and ensures the returned date is valid,
            even if the target month has fewer days than the original.
        """
        date = dt.strptime(date_str, '%Y-%m-%d')
        new_month = date.month - months
        new_year = date.year
        while new_month <= 0:
            new_month += 12
            new_year -= 1        
        new_day = min(date.day, (dt(new_year, new_month + 1, 1) - dt(new_year, new_month, 1)).days)
        new_date = dt(new_year, new_month, new_day)        
        return new_date.strftime('%Y-%m-01')

    def days_in_year(self, year):
        """
        Return the number of days in a given year.

        Parameters:
        -----------
            year : int
                The year to evaluate.

        Returns:
        -----------
            int : 366 if the year is a leap year; otherwise 365.

        Notes:
        -----------
            Leap years follow the Gregorian calendar rule:
            - Every 4 years is a leap year,
            - Except every 100 years is not,
            - Except every 400 years is.
        """
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 366
        else:
            return 365

    def weeks_in_year(self, date=None, mode='passed'):
        """
        Calculate the number of weeks passed or remaining in the year from a given date.

        Parameters:
        -----------
            date : str or datetime.date, optional
                The reference date (as '%Y-%m-%d' string or a `date` object).
                Defaults to today's date.

            mode : str, optional
                Determines the direction of calculation:
                - 'passed' returns weeks elapsed since the start of the year,
                - 'left' returns weeks remaining until year end.
                Defaults to 'passed'.

        Returns:
        -----------
            int : The number of weeks based on the selected mode.

        Raises:
        -----------
            ValueError : If an invalid mode is specified (must be 'passed' or 'left').

        Notes:
        -----------
            Partial weeks are not counted. This method performs integer division of days by 7.
        """
        if date is None:
            date = d.today()
        elif isinstance(date, str):
            date = self.parse(date).date()

        start_of_year = d(date.year, 1, 1)
        end_of_year = d(date.year, 12, 31)

        if mode == 'passed':
            days_passed = (date - start_of_year).days
            return days_passed // 7
        elif mode == 'left':
            days_left = (end_of_year - date).days
            return days_left // 7
        else:
            raise ValueError("Invalid mode. Please choose 'passed' or 'left'.")

    def contains_time(self, obj):
        """
        Determine whether a date/time object contains non-zero time information.

        Parameters:
        -----------
            obj : datetime.datetime, datetime.time, or datetime.date
                The object to evaluate.

        Returns:
        -----------
            bool : True if the object has any non-zero time component (hour, minute, second, or microsecond);
                   False otherwise.

        Raises:
        -----------
            TypeError : If the object is not a recognized datetime-like type.

        Notes:
        -----------
            - For `datetime` and `time`, checks if any time fields are non-zero.
            - For `date`, always returns False (since it has no time component).
        """
        if self._is_datetimeType(obj):
            if isinstance(obj, dt) or isinstance(obj, t):
                return (obj.hour, obj.minute, obj.second, obj.microsecond) != (0, 0, 0, 0)
            elif isinstance(obj, d):
                return False # date objects have no time information, so return False
        return False
       
    def within_delta(self, t1, t2, n, unit = 'hours'):
        """
        Return True if the two date-time inputs are within a given number of hours or minutes.

        Parameters:
        -----------
            t1, t2 : datetime.datetime or str
                The datetime values to compare. May be `datetime` objects or strings in ISO format,
                "%Y-%m-%d %H:%M", or any format supported by `dtparse.parse`.
            
            n : int
                The threshold value for comparison, in the specified time unit.
            
            unit : str, optional
                The unit of time to compare: either 'hours' or 'minutes'. Defaults to 'hours'.

        Returns:
        -----------
            bool : True if the absolute difference between `t1` and `t2` is less than or equal to `n`
            units of time (after sub-unit normalization); otherwise False.

        Raises:
        -----------
            TypeError : If `t1` or `t2` is not a supported type.
            ValueError : If `unit` is not 'hours' or 'minutes'.

        Notes:
        -----------
            Sub-unit fields (e.g., seconds, microseconds) are zeroed out prior to comparison to ensure
            consistent granularity. Useful for threshold-based date grouping and event correlation.
        """
        def _to_dt(val):
            if isinstance(val, dt):
                return val
            if isinstance(val, str):
                return self.parse(val)
            raise TypeError(f"Unsupported type: {type(val)}")

        dt1 = _to_dt(t1)
        dt2 = _to_dt(t2)

        if unit == 'hours':
            dt1 = dt1.replace(minute=0, second=0, microsecond=0)
            dt2 = dt2.replace(minute=0, second=0, microsecond=0)
            threshold = td(hours=n)
        elif unit == 'minutes':
            dt1 = dt1.replace(second=0, microsecond=0)
            dt2 = dt2.replace(second=0, microsecond=0)
            threshold = td(minutes=n)
        else:
            raise ValueError("unit must be 'hours' or 'minutes'")

        return abs(dt1 - dt2) <= threshold
       
    def build(self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tz_offset_hours=None, as_date=False):
        """
        Construct a datetime or date object from individual components.

        Parameters:
        -----------
            year : int
                The year component (e.g., 2025).

            month : int
                The month component (1–12).

            day : int
                The day of the month.

            hour : int, optional
                Hour of the day (0–23). Defaults to 0.

            minute : int, optional
                Minute (0–59). Defaults to 0.

            second : int, optional
                Second (0–59). Defaults to 0.

            microsecond : int, optional
                Microsecond (0–999999). Defaults to 0.

            tz_offset_hours : int or float, optional
                If provided, apply this UTC offset as timezone info.

            as_date : bool, optional
                If True, return a `date` object instead of a `datetime`.

        Returns:
        -----------
            datetime.datetime or datetime.date :
                A constructed datetime or date object based on inputs.

        Notes:
        -----------
            If `tz_offset_hours` is given, a timezone-aware datetime is returned (unless `as_date=True`).
        """
        tzinfo = tmz(td(hours=tz_offset_hours)) if tz_offset_hours is not None else None
        dt_obj = dt(year, month, day, hour, minute, second, microsecond, tzinfo=tzinfo)
        return dt_obj.date() if as_date else dt_obj
       
    def __dir__(self):
        """List public methods for interactive discovery and tab completion."""
        return [
            'parse',
            'now',
            'unix_timestamp',
            'nowCT',
            'subtract_months',
            'days_in_year',
            'weeks_in_year',
            'ET',
            'make_timezone_aware',
            'sub',
            'contains_time',
            'add',
            'flush',
            'within_delta',
            'build',
        ]

dtparse = dt_parse()

def __dir__():
    return __all__
