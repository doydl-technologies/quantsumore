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
from copy import deepcopy
from html import unescape as html_unescape
from collections.abc import Mapping

from ....proxy import Proxy
from ....exceptions import (
    CompanyProfileError,
    CompanyProfileValidationError,
    CompanyProfileNoDataError,
)


__all__ = ['profile']





# Defer dependency imports until first use.
pd = Proxy("pandas", None)



"""
Expected Input: Company Profile Data API Response (Index/Node-Mapped Format)

This class expects as input the parsed JSON response for a company profile endpoint
where structured company, executive, and filing information is packed into arrays and
referenced via positional indices mapped by metadata keys. The format is optimized for compactness
rather than human readability.

Example Input Structure:
[
  {
    "<string-key>": {   # Usually a URL-encoded request/endpoint signature
      "response": {
        "type": "data",
        "nodes": [
          { "type": "skip" },
          { "type": "skip" },
          {
            "type": "data",
            "data": [
              # 0: Profile fields (mapping field names to array indices)
              {
                "profile": int,      # Index to company info
                "logo": int,         # Index to company logo id
                "logoURL": int,      # Index to company logo url
                "description": int,  # Index to business description
                "contact": int,      # Index to contact info
                "details": int,      # Index to security details
                "executives": int,   # Index to executives section
                "filings": int       # Index to SEC filings section
              },
              # 1: Company info fields (name, industry, ceo, etc; mapped by index)
              {
                "name": int,
                "country": int,
                "founded": int,
                "ipoDate": int,
                "industry": int,
                "sector": int,
                "employees": int,
                "ceo": int
              },
              # 2+: Data fields, in positional order, e.g.:
              <company_name: str>,               # e.g., "NVIDIA Corporation"
              <country: str>,                    # e.g., "United States"
              <founded: int>,                    # e.g., 1993
              <ipoDate: str>,                    # e.g., "1999-01-22"
              {
                "value": str, "url": str         # Industry value & link
              },
              <industry: str>,                   # e.g., "Semiconductors"
              <industry_url: str>,               # e.g., "stocks/industry/semiconductors"
              {
                "value": str, "url": str         # Sector value & link
              },
              <sector: str>,                     # e.g., "Technology"
              <sector_url: str>,                 # e.g., "stocks/sector/technology"
              {
                "value": str, "url": str         # Employees value & link
              },
              <employees: int>,                  # e.g., 36000
              <employees_url: str>,              # e.g., "stocks/nvda/employees"
              <ceo: str>,                        # e.g., "Jen-Hsun Huang"
              # ...other basic info fields ...
              <logo: bool>,                      # True/False if logo available
              <logo_url: str>,                   # e.g., https://img.stockanalysis.com/...
              <description: str>,                # HTML/escaped description
              {
                "address": int,                  # Index to address
                "phone": int,                    # Index to phone
                "website": int,                  # Index to website
                "domain": int                    # Index to domain
              },
              <address: str>,
              <phone: str>,
              <website: str>,
              <domain: str>,
              {
                "symbol": int,
                "exchange": int,
                "fiscalYear": int,
                "currency": int,
                "cik": int,
                "cusip": int,
                "isin": int,
                "eid": int,
                "sic": int,
                "stockType": int,
                "shareClass": int,
                "securityName": int
              },
              <symbol: str>,
              <exchange: str>,
              <fiscalYear: str>,
              <currency: str>,
              <cik: str>,
              <cusip: str>,
              <isin: str>,
              <eid: str>,
              <sic: str>,
              <stockType: str>,
              <shareClass: str or None>,
              # ...more details, as indexed...
              [<executive_index_list: int>],
              # Executives: repeated pattern of { "Name": int, "Title": int }, <name: str>, <title: str>
              {
                "Name": int,
                "Title": int
              },
              <exec_name: str>,
              <exec_title: str>,
              # ...repeat for each executive...
              [<filing_index_list: int>],
              # Filings: repeated pattern of { "date": int, "path": int, "type": int, "title": int }, <date: str>, <path: str>, <type: str>, <title: str>
              {
                "date": int,
                "path": int,
                "type": int,
                "title": int
              },
              <filing_date: str>,
              <filing_path: str>,
              <filing_type: str>,
              <filing_title: str>,
              # ...repeat for each filing...
            ],
            "uses": {
              "search_params": [str],  # E.g., ["cache-bust"]
              "params": [str]          # E.g., ["symbol"]
            }
          }
        ]
      }
    }
  }
  # ...more results if batch queries...
]


Alternative Response Format
============================
The API response can also appear as a more complex nested JSON structure containing multiple `nodes` with various data segments, for example:

```json
[
  {
    "<string-key>": {
      "response": {
        "type": "data",
        "nodes": [
          {
            "type": "data",
            "data": [
              {
                "session": -1,
                "cookies": 1,
                "loc": 50,
                "theme": -1,
                "chartTheme": -1,
                "hideNewsSources": 52,
                "ab": 53
              },
              [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47],
              ...
            ],
            "uses": {
              "search_params": ["network"]
            },
            "slash": "always"
          },
          {
            "type": "data",
            "data": [
              {
                "info": 1
              },
              {
                "type": 2,
                "subtype": 3,
                "symbol": 4,
                ...
              },
              "stocks",
              "stock",
              "aapl",
              "AAPL",
              "Apple",
              "Apple Inc.",
              "NASDAQ",
              ...
            ],
            "uses": {
              "params": ["symbol"]
            }
          },
          {
            "type": "data",
            "data": [
              {
                "profile": 1,
                "logo": 16,
                "logoURL": 17,
                "description": 18,
                "contact": 19,
                "details": 24,
                "executives": 36,
                "filings": 67
              },
              {
                "name": 2,
                "country": 3,
                ...
              },
              "Apple Inc.",
              "United States",
              1977,
              ...
            ],
            "uses": {
              "search_params": ["cache-bust"],
              "params": ["symbol"]
            }
          }
        ]
      }
    }
  }
]

• This structure contains multiple `nodes` that serve different purposes such as session metadata, stock summary data, and the detailed company profile.
• The company profile node follows the same index-mapped format as the primary example.
• It is essential to locate the relevant nodes by their `"type"` field and parse them using their respective index mappings.
• The presence of session, cookie, and other metadata nodes may require filtering or ignoring, depending on your use case.
• Always use the included field-to-index mappings to correctly extract the data.

Notes:
	• All content is index-mapped for compactness; use the first two "data" dicts as field-to-index guides.
	• Executives and filings are represented as a list of index blocks, each followed by the corresponding field values.
	• Company info, contact, and security details may have nested dicts with their own index mapping.
	• All string values may be HTML-escaped (e.g., `\u003Cbr\u003E` or `\u003Cp\u003E`).
	• Always check index existence and type before dereferencing—structure may vary by company or API version.

This structure is highly compact but non-intuitive—**always use the provided index mapping** for extraction.
"""
class _SessionPrefsCleaner:
    SESSION_SIGNATURE_KEYS = {"session", "cookies", "loc", "theme", "chartTheme", "hideNewsSources", "ab"}
    def __init__(self, preserve_positions: bool = True):
        self.preserve_positions = preserve_positions

    @staticmethod
    def looks_like_session_prefs(d: any) -> bool:
        if not isinstance(d, dict): return False
        keys = set(d.keys())
        required = {"session", "cookies", "loc"}
        if not required.issubset(keys): return False
        if not keys.issubset(_SessionPrefsCleaner.SESSION_SIGNATURE_KEYS): return False
        if not isinstance(d.get("cookies"), list): return False
        loc = d.get("loc")
        if not (isinstance(loc, dict) and "co" in loc and isinstance(loc["co"], str)): return False
        if not re.fullmatch(r"[A-Z]{2,3}", loc["co"].upper()): return False
        ab = d.get("ab")
        if ab is not None and not (isinstance(ab, dict) and "network" in ab): return False
        return True

    @staticmethod
    def is_raw_session_node(node: any) -> bool:
        if not (isinstance(node, dict) and node.get("type") == "data" and isinstance(node.get("data"), list)): return False
        data_arr = node["data"]
        if not data_arr or not isinstance(data_arr[0], dict): return False
        root_keys = set(data_arr[0].keys())
        has_session_signature = {"session", "cookies", "loc"}.issubset(root_keys)
        not_profile = "profile" not in root_keys
        not_info = "info" not in root_keys
        return has_session_signature and not_profile and not_info

    def drop_session_from_raw(self, struct: dict) -> dict:
        if not (isinstance(struct, dict) and isinstance(struct.get("nodes"), list)):
            raise TypeError("Expected a raw structure with a 'nodes' list.")
        new_nodes = []
        for node in struct["nodes"]:
            if _SessionPrefsCleaner.is_raw_session_node(node):
                if self.preserve_positions: new_nodes.append({"type": "skip"})
            else:
                new_nodes.append(deepcopy(node))
        out = deepcopy(struct)
        out["nodes"] = new_nodes
        return out

    def drop_session_from_parsed(self, mapping: dict) -> dict:
        if not (isinstance(mapping, dict) and all(isinstance(k, (str, int)) for k in mapping.keys())):
            raise TypeError("Expected a mapping dict of nodes.")
        cleaned = {}
        for k, v in mapping.items():
            if not _SessionPrefsCleaner.looks_like_session_prefs(v):
                cleaned[k] = deepcopy(v)
        return cleaned

    def drop_session_anywhere(self, obj: any) -> any:
        if isinstance(obj, dict) and "nodes" in obj and isinstance(obj["nodes"], list):
            return self.drop_session_from_raw(obj)
        if isinstance(obj, dict) and all(isinstance(k, (str, int)) for k in obj.keys()):
            if _SessionPrefsCleaner.looks_like_session_prefs(obj): return None
            out = {}
            for k, v in obj.items():
                cleaned_v = self.drop_session_anywhere(v)
                if cleaned_v is not None: out[k] = cleaned_v
            return out
        if isinstance(obj, list):
            new_list = []
            for item in obj:
                if _SessionPrefsCleaner.looks_like_session_prefs(item):
                    if self.preserve_positions: new_list.append({"type": "skip"})
                else:
                    cleaned_item = self.drop_session_anywhere(item)
                    if cleaned_item is not None: new_list.append(cleaned_item)
            return new_list
        return deepcopy(obj)

    def clean(self, struct: any) -> any:
        return self.drop_session_anywhere(struct)


class _ParsedDataSquasher:
    @staticmethod
    def _remove_outer_key(d):
        if 0 in d: inner = d.pop(0)
        elif '0' in d: inner = d.pop('0')
        else: return d
        d.clear(); d.update(inner); return d
    @staticmethod
    def deep_merge(a: Mapping, b: Mapping, prefer: str = "right"):
        out = dict(a)
        for k, v in b.items():
            if k in out and isinstance(out[k], Mapping) and isinstance(v, Mapping):
                out[k] = _ParsedDataSquasher.deep_merge(out[k], v, prefer=prefer)
            elif not (prefer == "left" and k in out):
                out[k] = v
        return out
    @staticmethod
    def squash_parsed_data(parsed_data: dict, *, target_key=0, prefer: str = "right", drop_rest: bool = True) -> dict:
        out = dict(parsed_data)
        keys = [k for k in out if k != target_key]
        merged = out.get(target_key, {})
        for k in keys: merged = _ParsedDataSquasher.deep_merge(merged, out[k], prefer=prefer)
        out[target_key] = merged
        if drop_rest:
            for k in keys: out.pop(k, None)
        return _ParsedDataSquasher._remove_outer_key(out)
   
   
class _profileParse:
    _QUOTE_KEYS = {
        "c":"change","e":"market_open","h":"high","l":"low","o":"open","p":"previous_close",
        "u":"last_update","v":"volume","cl":"close","cp":"percent_change","ec":"extended_change",
        "ep":"extended_price","es":"extended_session","eu":"extended_update","ex":"exchange",
        "ms":"market_status","pd":"previous_day_price","td":"trade_date","ts":"timestamp",
        "cdr":"change_direction","ecp":"extended_change_percent","epd":"extended_previous_day_price",
        "etd":"extended_trade_date","ets":"extended_timestamp","exp":"expiry_timestamp",
        "fms":"full_market_status","h52":"fifty_two_week_high","l52":"fifty_two_week_low",
        "uid":"symbol","days":"days_since_event","epv":"extended_previous_value"
    }
    def __init__(self, preserve_positions=True): self.cleaner = _SessionPrefsCleaner(preserve_positions=preserve_positions)
    def parse(self, struct, normalize=True, none_replace=None):
        struct = self.cleaner.clean(struct)
        content = self._response_status(struct, normalize=normalize)
        data = deepcopy(content)
        all_parsed = self.parse_all_nodes(data)
        if isinstance(none_replace, str):
            na_token = none_replace if none_replace.lower() in ("n/a", "na") else None
            parsedata = self._replace_none_with_na(all_parsed, na_type=na_token)
            parsedata = self._rename_quote_keys(parsedata, _profileParse._QUOTE_KEYS)
            return self._remove_keys(parsedata)
        else: return all_parsed
    def parse_by_key(self, struct, key, missing_value=None):
        idx = self.find_node_for_key(struct, key)
        if idx is None: return None
        return self.parse_indexed_data(struct, node_index=idx, missing_value=missing_value)
    def parse_profile(self, struct, missing_value=None):
        return self.parse_by_key(struct, "profile", missing_value=missing_value)
    def _response_status(self, json_content, return_struct=True, normalize=False):
        payload = deepcopy(json_content)
        if isinstance(payload, list):
            if not payload: raise CompanyProfileError("Response not a non-empty list")
            node = payload[0]
        elif isinstance(payload, dict): node = payload
        else: raise CompanyProfileError(f"Unsupported response type: {type(payload)}")
        if isinstance(node, dict) and len(node) == 1:
            k = next(iter(node))
            if isinstance(k, str) and k.startswith(('https://', 'http://')): node = node[k]
        if isinstance(node, dict) and "response" in node: node = node["response"]
        if not isinstance(node, dict): raise CompanyProfileError("Unexpected structure after unwrapping URL/response")
        if node.get("type") == "data" and isinstance(node.get("nodes"), list):
            if return_struct: return self._normalize_input_data(node) if normalize else node
            else: return True
        raise CompanyProfileNoDataError("No valid data")
    def _normalize_input_data(self, input_data):
        raw_nodes = input_data.get("nodes", [])
        profile_node = next((n for n in raw_nodes if n.get("type") == "data" and "data" in n and isinstance(n["data"], list) and n["data"] and isinstance(n["data"][0], dict) and "profile" in n["data"][0]), None)
        if profile_node is None: raise ValueError("No profile node found")
        first_two = deepcopy(raw_nodes[:2])
        while len(first_two) < 2: first_two.append({"type": "skip"})
        return {"type": "data", "nodes": first_two + [deepcopy(profile_node)]}
    def _replace_none_with_na(self, obj, na_type="N/A"):
        if obj is None or obj == "" or (isinstance(obj, dict) and not obj): return na_type
        if isinstance(obj, dict): return {k: self._replace_none_with_na(v, na_type) for k, v in obj.items()}
        if isinstance(obj, list): return [self._replace_none_with_na(v, na_type) for v in obj]
        if isinstance(obj, tuple): return tuple(self._replace_none_with_na(v, na_type) for v in obj)
        if isinstance(obj, set): return {self._replace_none_with_na(v, na_type) for v in obj}
        return obj
    def _rename_quote_keys(self, parsed_data, key_map):
        new_data = deepcopy(parsed_data)
        node0 = new_data.get(0)
        if not isinstance(node0, dict): return new_data
        info = node0.get('info')
        if not isinstance(info, dict): return new_data
        quote = info.get('quote')
        if not isinstance(quote, dict): return new_data
        for old_key, new_key in key_map.items():
            if old_key in quote: quote[new_key] = quote.pop(old_key)
        return new_data
    def _remove_keys(self, obj, keys_to_remove=None):
        if keys_to_remove is None:
            keys_to_remove = {'baseurl','market_open','state','archived','notice','stream','template','interval','features','meta','logo','logoURL', 'quote'}
        if isinstance(obj, dict):
            return {k: self._remove_keys(v, keys_to_remove) for k, v in obj.items() if k not in keys_to_remove}
        elif isinstance(obj, list): return [self._remove_keys(item, keys_to_remove) for item in obj]
        elif isinstance(obj, tuple): return tuple(self._remove_keys(item, keys_to_remove) for item in obj)
        else: return obj
    def get_data_nodes(self, struct):
        return [n for n in struct.get("nodes", []) if n.get("type") == "data" and isinstance(n.get("data"), list)]
    def find_node_for_key(self, struct, key):
        for i, node in enumerate(self.get_data_nodes(struct)):
            root = node["data"][0] if node["data"] else None
            if isinstance(root, dict) and key in root: return i
        return None
    def parse_indexed_data(self, struct, node_index=0, missing_value=None):
        data_nodes = self.get_data_nodes(struct)
        if not (0 <= node_index < len(data_nodes)):
            raise IndexError(f"node_index {node_index} out of range (0..{len(data_nodes)-1})")
        data_array = data_nodes[node_index]["data"]
        def resolve(idx):
            if not isinstance(idx, int): return idx
            if idx < 0 or idx >= len(data_array): return missing_value
            val = data_array[idx]
            if isinstance(val, dict):
                out = {}
                for k, v in val.items():
                    if isinstance(v, int): out[k] = resolve(v)
                    elif isinstance(v, list): out[k] = [resolve(it) if isinstance(it, int) else it for it in v]
                    else: out[k] = v
                return out
            if isinstance(val, list): return [resolve(it) if isinstance(it, int) else it for it in val]
            return val
        root = data_array[0]
        if not isinstance(root, dict): raise ValueError("Expected a mapping dict at data_array[0].")
        return {k: resolve(idx) for k, idx in root.items()}
    def parse_all_nodes(self, struct, missing_value=None):
        result = {}
        for i, _node in enumerate(self.get_data_nodes(struct)):
            result[i] = self.parse_indexed_data(struct, node_index=i, missing_value=missing_value)
        return result

class profile:
    def __init__(self, json_content=None, preserve_positions=True, collapse_wrappers=True, prefer_value_only=False):
        if json_content is None: raise CompanyProfileNoDataError("No JSON content provided")    	
        pd = _profileParse(preserve_positions).parse(json_content, normalize=True, none_replace="N/A")
        pd = _ParsedDataSquasher.squash_parsed_data(pd)
        pd = self._normalize_info_keys(pd)
        if collapse_wrappers: pd = self._collapse_value_wrappers(pd, prefer_value_only=prefer_value_only)
        if not (pd and 'profile' in pd): raise CompanyProfileValidationError("No profile data loaded")     
        self._parsed = pd or {}
        self._info, self._profile = self._parsed.get('info', {}) or {}, self._parsed.get('profile', {}) or {}
        c = self._parsed.get('contact'); self._contact = c if isinstance(c, dict) else None
        self._data = None
    @staticmethod
    def _normalize_info_keys(d):
        i = d.get('info')
        if isinstance(i, dict):
            if 'curr' in i: i['currency'] = i.pop('curr')
            if 'ble' in i: i['share_class_label'] = i.pop('ble')
        return d
    @staticmethod
    def _collapse_value_wrappers(o, *, prefer_value_only=False):
        if isinstance(o, Mapping):
            t = {k: profile._collapse_value_wrappers(v, prefer_value_only=prefer_value_only) for k, v in o.items()}
            if prefer_value_only and 'value' in t and len(t) > 1: return t['value']
            if not prefer_value_only and set(t.keys()) == {'value','url'}: return t['value']
            return t
        if isinstance(o, list):  return [profile._collapse_value_wrappers(x, prefer_value_only=prefer_value_only) for x in o]
        if isinstance(o, tuple): return tuple(profile._collapse_value_wrappers(x, prefer_value_only=prefer_value_only) for x in o)
        return o

    @property
    def basic_info(self):
        i, p = self._info, self._profile
        return {
            "name": i.get("name","N/A"), "full_name": i.get("nameFull","N/A"), "ticker": i.get("ticker","N/A"),
            "exchange": i.get("exchange","N/A"), "type": i.get("type","N/A"), "subtype": i.get("subtype","N/A"),
            "ipo_date": i.get("ipoDate","N/A"), "cik": i.get("cik","N/A"), "uid": i.get("uid","N/A"),
            "share_class_label": i.get("share_class_label","N/A"), "country": p.get("country","N/A"),
            "ceo": p.get("ceo","N/A"), "employees": p.get("employees","N/A"), "currency": i.get("currency","N/A")
        }
    @property
    def industry_sector(self):
        p = self._profile
        return {"industry": p.get("industry","N/A"), "sector": p.get("sector","N/A")}
    @property
    def contact_details(self):
        if not self._contact: return "N/A"
        cd = dict(self._contact); a = cd.get('address')
        if isinstance(a, str) and a.strip() and a != "N/A":
            t = html_unescape(a)
            t = re.sub(r"(?i)<br\s*/?>", ", ", t)
            t = re.sub(r"<[^>]+>", "", t)
            t = re.sub(r"\s+", " ", t).strip()
            cd['address'] = t
        return cd
    @property
    def executives(self):         return self._parsed.get('executives', "N/A")
    @property
    def security_details(self):  return self._parsed.get('details', "N/A")
    @property
    def company_description(self):
        d = self._parsed.get('description', "")
        if isinstance(d, str) and d.strip() and d != "N/A":
            t = re.sub(r'</p>\s*<p>', '</p> <p>', d)
            t = re.sub(r'<[^>]+>', '', t)
            return re.sub(r'\.(?=[A-Z])', '. ', t)
        return "N/A"
    @property
    def company_filings(self):
        return "N/A" if self._parsed.get('filings', "N/A") == "N/A" else [
            {**f, 'path': f['path'] if f['path'].startswith("https://www.sec.gov/Archives/") else "https://www.sec.gov/Archives/" + f['path']} 
            for f in self._parsed['filings']
        ]    

    def as_dict(self):
        if self._data is None:
            self._data = {
                "basic_info": self.basic_info,
                "industry_sector": self.industry_sector,
                "contact_details": self.contact_details,
                "executives": self.executives,
                "security_details": self.security_details,
                "company_description": self.company_description,
                "company_filings": self.company_filings,
            }
        return self._data
    DATA = as_dict
    def __dir__(self): return ["DATA"]


def __dir__():
    return __all__
