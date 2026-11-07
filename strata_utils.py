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



import re

from .markup import url_encode_decode

__all__ = [
    'IterDict',
    ]      




# Transform copies rather than mutating the raw provider response.
class IterDict:
    """Search, filter and normalize nested provider response structures.

The helpers handle nested dictionaries and collections, locate keys and
responses, and remove empty or irrelevant entries."""
    @staticmethod
    def _is_effectively_empty(item):
        """
        Recursively determines if a nested structure is effectively empty.

        An object is considered "effectively empty" if it is:
        - An empty list, tuple, set, or dict,
        - A list, tuple, or set where all elements are themselves empty structures,
        - A dict where all values are empty structures.

        Parameters:
        ----------
        item : Any
            The object to check. Can be a list, tuple, set, dict, or other type.

        Returns:
        -------
        bool
            True if the structure is effectively empty, otherwise False.
        """
        if isinstance(item, (list, tuple, set)):
            return all(IterDict._is_effectively_empty(i) for i in item)
        elif isinstance(item, dict):
            return all(IterDict._is_effectively_empty(v) for v in item.values())
        return False    
    
    @staticmethod    
    def top_key(d, top_1=True, exclusion=None, exclusion_sensitive=False):
        """Return keys from a dictionary or the first dictionary in a list.

        top_1 selects the first remaining key; otherwise return the key list.
        exclusion removes a matching key, case-insensitively unless
        exclusion_sensitive is True. Empty key results return an empty list.
        Unsupported inputs return the string "Invalid or unsupported structure".
        """
        keys = []
        if isinstance(d, dict):
            keys = list(d.keys())
        elif isinstance(d, list) and d and isinstance(d[0], dict):
            keys = list(d[0]. keys())
        else:
            return "Invalid or unsupported structure"
           
        if exclusion:
            if exclusion_sensitive:
                keys = [key for key in keys if key != exclusion]
            else:
                keys = [key for key in keys if key.lower() != exclusion.lower()]
        if top_1 and keys:
            return keys[0]
        return keys   

    @staticmethod    
    def search_keys(d, target_keys, value_only=True, first_only=True, return_all=False, include_key_in_results=False):
        """
        Search nested data for multiple keys and return the matching results.

        Parameters:
        ----------
        d : Any
            The nested structure to search (dict, list, tuple, set, etc.).
        target_keys : str or list of str
            Single key or list of keys to search for.
        value_only : bool, optional
            If True, return only the values associated with each key. Default is True.
        first_only : bool, optional
            If True, return only the first match for each key. Default is True.
        return_all : bool, optional
            If True, return the entire sub-structure where the target key is found. Default is False.
        include_key_in_results : bool, optional
            If True, results are returned as a dict of key → value. If False, results are returned as a list.

        Returns:
        -------
        dict or list or None
            Dictionary or list of found values/sub-structures, or None if no matches found.
        """        
        def all_values_none(output):
            if isinstance(output, dict):
                return all(all_values_none(value) for value in output.values())
            elif isinstance(output, list):
                return all(all_values_none(item) for item in output)
            else:
                return output is None
        
        def recurse(d, target_key, value_only=True, first_only=True, return_all=False):
            results = []
            if d is None:
                return None
            if isinstance(d, dict):
                for key, value in d.items():
                    if key == target_key:
                        result = (value if value_only else {key: value}) if not return_all else d
                        if first_only:
                            return result
                        else:
                            results.append(result)
                    sub_result = recurse(value, target_key, value_only, first_only, return_all)
                    if sub_result is not None:
                        if first_only:
                            return sub_result
                        else:
                            results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
            elif isinstance(d, (list, tuple, set)):
                for item in d:
                    sub_result = recurse(item, target_key, value_only, first_only, return_all)
                    if sub_result is not None:
                        if first_only:
                            return sub_result
                        else:
                            results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
            elif isinstance(d, (str, bytes)):
                return None if first_only else results
            else:
                try:
                    iterator = iter(d)
                    for item in iterator:
                        sub_result = recurse(item, target_key, value_only, first_only, return_all)
                        if sub_result is not None:
                            if first_only:
                                return sub_result
                            else:
                                results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
                except TypeError:
                    return None if first_only else results
            if results:
                results = [res for res in results if res is not None]
                if not results: 
                    return None
            if IterDict._is_effectively_empty(results):
                return None
            return results if not first_only else None

        if isinstance(target_keys, str):
            target_keys = [target_keys]
            
        if include_key_in_results:
            results = {key: recurse(d, target_key=key, value_only=value_only, first_only=first_only, return_all=return_all) for key in target_keys}
            
            if all_values_none(results):
                results = None
                
        else:
            results = [recurse(d, target_key=key, value_only=value_only, first_only=first_only, return_all=return_all) for key in target_keys]
            if all_values_none(results):
                results = None            
            if results is not None and len(results) == 1:
                results = results[0]
        return results

    @staticmethod    
    def search_keys_in(d, target_keys, value_only=True, first_only=True, return_all=False):
        """
        Recursively search nested structures and return matching values, the key-value pairs, or the entire sub-structure,
        optionally returning all matches instead of just the first.

        Parameters:
        ----------
        d : Any
            The nested structure to search (dict, list, tuple, set, or iterable).
        target_keys : list of str
            The keys to search for.
        value_only : bool, optional
            If True, return only the values. If False, return key-value pairs. Default is True.
        first_only : bool, optional
            If True, return only the first match. Default is True.
        return_all : bool, optional
            If True, return the full sub-structure where the key is found.

        Returns:
        -------
        Any, dict, None, or list
            Depending on options: a single value, a key-value pair, a sub-structure,
            or a list of results, or None if no matches.
        """
        def remove_duplicates(dicts):
            seen = []
            unique_dicts = []
            for d in dicts:
                if d not in seen:
                    unique_dicts.append(d)
                    seen.append(d)
            return unique_dicts  
           
        results = []       
        if d is None:
            return None
        if isinstance(d, dict):
            for key, value in d.items():
                if key in target_keys:
                    result = (value if value_only else {key: value}) if not return_all else d
                    if first_only:
                        return result
                    else:
                        results.append(result)
                sub_result = IterDict.search_keys_in(value, target_keys, value_only, first_only, return_all)
                if sub_result is not None:
                    if first_only:
                        return sub_result
                    else:
                        results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
        elif isinstance(d, (list, tuple, set)):
            for item in d:
                sub_result = IterDict.search_keys_in(item, target_keys, value_only, first_only, return_all)
                if sub_result is not None:
                    if first_only:
                        return sub_result
                    else:
                        results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
        elif isinstance(d, (str, bytes)):
            return None if first_only else results
        else:
            try:
                iterator = iter(d)
                for item in iterator:
                    sub_result = IterDict.search_keys_in(item, target_keys, value_only, first_only, return_all)
                    if sub_result is not None:
                        if first_only:
                            return sub_result
                        else:
                            results.extend(sub_result if isinstance(sub_result, list) else [sub_result])
            except TypeError:
                return None if first_only else results
        if results:
            results = [res for res in results if res is not None] 
            if not results:
                return None
        return remove_duplicates(results) if not first_only else None

    @staticmethod 
    def filter(d, filter_key, filter_value, regex=False):
        """
        Filters a complex data structure, recursively checking dictionaries and lists for the presence
        of a specified key-value pair or a key with a value matching a regex pattern.

        Parameters:
        ----------
        d : dict or list
            The data to be filtered.
        filter_key : str
            The key to look for.
        filter_value : Any
            The value (or regex pattern) that must match.
        regex : bool, optional
            If True, interpret filter_value as a regex pattern.

        Returns:
        -------
        dict, list, or None
            Filtered structure containing only matches. None if no matches found.
        """
        if regex:
            pattern = re.compile(filter_value)
            
        def recursive_filter(data):
            if isinstance(data, dict):
                filtered_dict = {}
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        filtered_value = recursive_filter(value)
                        if filtered_value:
                            filtered_dict[key] = filtered_value
                    elif key == filter_key:
                        if (regex and pattern.search(str(value))) or (not regex and value == filter_value):
                            return data
                return filtered_dict if filtered_dict else None
            elif isinstance(data, list):
                filtered_list = []
                for item in data:
                    filtered_item = recursive_filter(item)
                    if filtered_item:
                        filtered_list.append(filtered_item)
                return filtered_list if filtered_list else None
            return None
        return recursive_filter(d)

    @staticmethod 
    def find(d, first_only=True, target_key=None, key_path=None, wrap=False):
        """
        Locate data within a structure.

        This method searches for a specified target key or follows a specific key path
        to locate data within a nested dictionary or list structure. Optionally, it can
        wrap the found data within a dictionary under the target key.

        Parameters:
        ----------
        d : dict or list
            The data structure to search.
        first_only : bool, optional
            If True, return only the first match. Default is True.
        target_key : str, optional
            The key to search for (ignored if key_path is provided).
        key_path : list of str, optional
            List of keys representing a direct path to the target data.
        wrap : bool, optional
            If True, wraps found data in a dict under target_key.

        Returns:
        -------
        Any or None
            The matched data or None if not found.
        """
        def recursive_search(data_input, target_key, first_only=True, matches=None):
            if matches is None:
                matches = []
            if isinstance(data_input, dict):
                for key, value in data_input.items():
                    if key == target_key:
                        matches.append(value)
                        if first_only:
                            return value
                    else:
                        result = recursive_search(value, target_key, first_only, matches)
                        if result is not None and first_only:
                            return result
            elif isinstance(data_input, list):
                for item in data_input:
                    result = recursive_search(item, target_key, first_only, matches)
                    if result is not None and first_only:
                        return result
            return matches if not first_only else None

        if key_path:
            current_data = d
            try:
                for key in key_path:
                    if isinstance(current_data, list):
                        current_data = [item[key] for item in current_data if isinstance(item, dict) and key in item][0]
                    else:
                        current_data = current_data[key]
                result = current_data
            except (IndexError, KeyError):
                result = None
        else:
            result = recursive_search(d, target_key, first_only)
        if wrap and result is not None:
            return {target_key: result}
        return result

    @staticmethod         
    def isNested(d):
        """Ensures that a given dictionary is nested within a list.

        If the input data is not already a list, it encloses the data in a new list.
        If the input is a list and contains any items that are not dictionaries,
        it nests the entire list within another list to ensure uniformity.
        If all items in the list are dictionaries, it returns the list unchanged.

        Parameters:
        ----------
        d : dict or list
            The data to check.

        Returns:
        -------
        list
            The data wrapped in a list if needed, or unchanged if already a uniform list of dicts.
        """
        if not isinstance(d, list):
            return [d]
        else:
            if any(not isinstance(item, dict) for item in d):
                return [d]
        return d    

    @staticmethod 
    def search_keys_re(d, pattern):
        """
        Recursively search for a dictionary with any key that matches the specified regex pattern
        in a nested structure that may include dictionaries nested within lists.

        Parameters:
        ----------
        d : dict or list
            The nested data structure to search.
        pattern : str
            Regex pattern to match keys against.

        Returns:
        -------
        list or None
            List of matching dictionaries, or None if none found.
        """
        compiled_pattern = re.compile(pattern)
        def remove_none(lst):
            """ Remove all None values from a list. """
            filtered_list = [item for item in lst if item is not None]
            if not filtered_list:
                return None
            return filtered_list

        def recursive_search(data):
            if isinstance(data, dict):
                for key in data.keys():
                    if compiled_pattern.search(key):
                        return data
                for value in data.values():
                    result = recursive_search(value)
                    if result is not None:
                        return result
            elif isinstance(data, list):
                for item in data:
                    result = recursive_search(item)
                    if result is not None:
                        return result
            return None
           
        d = IterDict.isNested(d)
        results = [recursive_search(f) for f in d]        
        return remove_none(results)

    @staticmethod 
    def extract_from(data, target_keys=None):
        """
        Extracts dictionary entries from a nested data structure (dictionaries and lists) 
        based on a specified set of keys or the most extensive set of keys found in the data.

        This function navigates through nested dictionaries and lists to find dictionaries that:
        - Contain all the keys specified in `target_keys` if it is provided.
        - Contain all the keys from the dictionary with the most extensive set of keys, 
          if `target_keys` is not provided.

        Parameters:
        ----------
        data : dict or list
            The nested structure to search.
        target_keys : iterable, optional
            The set of keys a dictionary must have to be included. If None, uses the largest found set.

        Returns:
        -------
        list
            List of dictionaries that match the required keys.
        """
        entries = []

        def find_max_keys(d, max_keys):
            if isinstance(d, dict):
                if len(d.keys()) > len(max_keys):
                    max_keys.clear()
                    max_keys.update(d.keys())
                for value in d.values():
                    find_max_keys(value, max_keys)
            elif isinstance(d, list):
                for item in d:
                    find_max_keys(item, max_keys)
            return max_keys

        def recurse(d, key_check):
            if isinstance(d, dict):
                if key_check(d):
                    entries.append(d)
                for value in d.values():
                    recurse(value, key_check)
            elif isinstance(d, list):
                for item in d:
                    recurse(item, key_check)

        if target_keys:
            key_check = lambda d: all(key in d for key in target_keys)
        else:
            max_keys = find_max_keys(data, set())
            key_check = lambda d: max_keys.issubset(d.keys())

        recurse(data, key_check)
        return entries       
    
    # Skip malformed response entries without raising an error.
    @staticmethod 
    def clean_initial_content(d):
        """
        Cleans a list of dictionaries by extracting the 'response' value from entries with URL keys.

        For each dictionary in the input list:
        - If a key is a valid URL (as determined by `is_valid_url`), and the corresponding value contains a
          'response' key, the content under 'response' is extracted and added to the cleaned output.
        - If a key is not a valid URL, the key-value pair is retained in the output as a dictionary.

        Parameters:
        ----------
        d : list of dict
            A list of dictionaries to be cleaned. Dictionary keys may be URLs.

        Returns:
        -------
        list
            A list of cleaned dictionaries or extracted responses. If a URL key with a 'response' sub-key is found,
            only the value of 'response' is retained; otherwise, the original key-value pair is kept.
        """
        cleaned_content = []
        for entry in d:
            for key, value in entry.items():
                if url_encode_decode.is_valid_url(key):
                    if 'response' in value: 
                        cleaned_content.append(value['response'])
                else:
                    cleaned_content.append({key: value})
        return cleaned_content    

    @staticmethod 
    def key_from_mapping(s, mappings, invert=False):
        """
        Looks up a key or synonym in a mapping dictionary and returns the canonical key or value.

        The function supports case-insensitive matching and recognizes both dictionary keys and
        synonyms (values or values in a list) as valid input. By default, it returns the canonical
        mapping key. If `invert` is True, it returns the value(s) for the matching key.

        Parameters:
        ----------
        s : str
            The input string to look up. Can be a mapping key or synonym (value).
        mappings : dict
            A dictionary of canonical keys mapped to either a single synonym (str) or a list of synonyms.
        invert : bool, optional
            If True, returns the value (or synonyms) for a given key instead of the key itself. Default is False.

        Returns:
        -------
        str or list or None
            The canonical key (default), or value(s) for the matched key (if `invert`), or None if no match found.

        Examples:
        --------
        >>> key_from_mapping('qtr', {'Quarterly': ['Q', 'Quarter', 'Qtr'], 'Annually': ['A', 'Annual']})
        'Quarterly'
        >>> key_from_mapping('quarterly', {'Quarterly': ['Q', 'Quarter', 'Qtr']}, invert=True)
        ['Q', 'Quarter', 'Qtr']
        """
        s = s.strip().lower()
        lower_case_mappings = {key.lower(): key for key in mappings}    
        inverse_mappings = {}
        for key, value in mappings.items():
            if isinstance(value, list):
                for synonym in value:
                    inverse_mappings[synonym.lower()] = key
            else:
                inverse_mappings[value.lower()] = key
        if s in lower_case_mappings.keys():
            if invert:
                return mappings[lower_case_mappings[s]] 
            return lower_case_mappings[s]
        if s in inverse_mappings:
            return inverse_mappings[s]
        return None

def __dir__():
    return __all__
