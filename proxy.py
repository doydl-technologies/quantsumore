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

"""Defer module imports and attribute resolution until first use.

Proxy caches its imported target and forwards calls and attribute access.
This avoids loading expensive or optional dependencies at startup. First
access is not synchronized across threads."""
import importlib
from typing import Any, TypeVar, Generic, Optional


__all__ = ['Proxy']





_T = TypeVar("_T")

class Proxy(Generic[_T]):
    """Defer importing a module or attribute until its first use.

    module_name identifies the module; optional attr_name selects an attribute
    within it. None proxies the whole module. The resolved target is cached
    and receives calls and attribute access.

    Import failures propagate as ImportError; missing target attributes raise
    AttributeError. Initial resolution is not synchronized across threads.
    """
    def __init__(self, module_name: str, attr_name: Optional[str] = None) -> None:    
        """Store the target module name and optional attribute name without importing them."""
        self._module_name = module_name
        self._attr_name = attr_name
        self._wrapped: Any = None

    def _load(self) -> _T:
        """Resolve and cache the module or attribute on first access.

        ImportError and AttributeError propagate from module import and attribute
        lookup respectively. Concurrent first access is not synchronized.
        """
        if self._wrapped is None:
            module = importlib.import_module(self._module_name)
            if self._attr_name is not None:
                self._wrapped = getattr(module, self._attr_name)
            else:
                self._wrapped = module
        return self._wrapped  # type: ignore        

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Resolve the target and forward positional and keyword arguments to it.

        Return the target's result. Calling a non-callable target raises TypeError.
        """
        return self._load()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Resolve the target and delegate attribute lookup, propagating AttributeError."""
        return getattr(self._load(), name)

    def __repr__(self):
        """Describe the target module, optional attribute and current loading state."""
        if self._wrapped is not None:
            return f"<Proxy for {self._module_name}.{self._attr_name} (loaded: {self._wrapped!r})>"
        return f"<Proxy for {self._module_name}.{self._attr_name} (not loaded)>"

def __dir__():
    return __all__
