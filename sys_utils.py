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

import os
from datetime import datetime, timedelta
import re
import platform
from pathlib import Path
from functools import lru_cache
from typing import Union, List, Dict, Optional, Literal
from dataclasses import dataclass


__all__ = ['Device', 'Download', 'FileInspector', 'Package']



# Platform application-data directories.
"""
Locate and manage the current system's application data directories.

- Windows:
    • Local data:   %LOCALAPPDATA%
    • Roaming data: %APPDATA%
    • Common data:  %PROGRAMDATA%
- macOS (Darwin):
    • Local data:   ~/Library/Application Support
    • Config data:  ~/Library/Preferences
    • Common data:  /Library/Application Support
- Linux/Unix:
    • Local data:   $XDG_DATA_HOME or ~/.local/share
    • Config data:  $XDG_CONFIG_HOME or ~/.config
    • Common data:  /usr/local/share
"""
class classproperty:
    def __init__(self, func): self.func = func
    def __get__(self, instance, owner): return self.func(owner)

class Device:
    APP_NAME = "quantsu_data"
    @classmethod
    @lru_cache(maxsize=None)
    def get_dir(cls, kind: Literal["local", "roaming", "common", "config"]) -> Path:
        s = platform.system()
        if s == "Windows": return cls._windows_dir(kind)
        if s == "Darwin": return cls._macos_dir(kind)
        return cls._linux_dir(kind)
    @staticmethod
    def _windows_dir(kind: str) -> Path:
        env_map = {"local":"LOCALAPPDATA","roaming":"APPDATA","common":"PROGRAMDATA","config":"APPDATA"}
        try: var = env_map[kind]
        except KeyError: raise ValueError(f"Unknown kind '{kind}' for Windows")
        val = os.getenv(var)
        if not val: raise EnvironmentError(f"Environment variable {var!r} is not set on Windows")
        return Path(val)
    @staticmethod
    def _macos_dir(kind: str) -> Path:
        home = Path.home()
        if kind in ("local","roaming"): return home/"Library"/"Application Support"
        if kind=="common": return Path("/Library")/"Application Support"
        if kind=="config": return home/"Library"/"Preferences"
        raise ValueError(f"Unknown kind '{kind}' for macOS")
    @staticmethod
    def _linux_dir(kind: str) -> Path:
        home = Path.home()
        if kind=="local":
            xdg = os.getenv("XDG_DATA_HOME")
            return Path(xdg) if xdg else home/".local"/"share"
        if kind=="config":
            xdg = os.getenv("XDG_CONFIG_HOME")
            return Path(xdg) if xdg else home/".config"
        if kind=="roaming":
            xdg = os.getenv("XDG_CONFIG_HOME")
            return Path(xdg) if xdg else home/".config"
        if kind=="common": return Path("/usr")/"local"/"share"
        raise ValueError(f"Unknown kind '{kind}' for Linux/Unix")
    @classmethod
    def get_local_appdata(cls): return cls.get_dir("local")
    @classmethod
    def get_roaming_appdata(cls): return cls.get_dir("roaming")
    @classmethod
    def get_common_appdata(cls): return cls.get_dir("common")
    @classmethod
    def get_config_appdata(cls): return cls.get_dir("config")
    @classmethod
    def get_subdir(cls, kind: Literal["local", "roaming", "common", "config"], *subpath: str, create: bool = False) -> Path:
        base = cls.get_dir(kind); target = base.joinpath(*subpath)
        if create: target.mkdir(parents=True, exist_ok=True)
        return target
    @classmethod
    def find_app_folder(cls, folder_name: str, recursive: bool = False) -> Optional[Path]:
        roots = {"local":cls.get_local_appdata(),"roaming":cls.get_roaming_appdata(),"common":cls.get_common_appdata(),"config":cls.get_config_appdata()}
        for kind, base in roots.items():
            if recursive:
                for dirpath, dirnames, _ in os.walk(base):
                    if folder_name in dirnames: return Path(dirpath)/folder_name
            else:
                candidate = base/folder_name
                if candidate.is_dir(): return candidate
        return None
    @classproperty
    def quantsumore_default(cls) -> Path:
        local_root = cls.get_dir("local"); data_dir = local_root/cls.APP_NAME
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir


# File timestamps and scheduled-update checks.
_USE_CREATION_DATE = True # When True, use the file’s creation timestamp; otherwise use its modified timestamp.
_DEFAULT_DATE_FIELD = "created" if _USE_CREATION_DATE else "modified"

@dataclass
class FileInfo:
    path: Path; exists: bool; creation_time: Optional[datetime]; modification_time: Optional[datetime]
    checked_time: Optional[datetime]; age: Optional[timedelta]
    is_older_than: Optional[bool]=None; is_younger_than: Optional[bool]=None

# Inspect file timestamps relative to an age or absolute-date threshold.
# Shortcuts may be included, and either creation or modification times can be compared.
class FileInspector:
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path)
        if not self.base_path.exists() or not self.base_path.is_dir():
            raise ValueError(f"{self.base_path!r} is not a valid directory")
    def inspect(self, filenames: Union[str, List[str]], *, date_field: str = _DEFAULT_DATE_FIELD,
                threshold_n: Optional[float] = None, threshold_unit: str = "days",
                threshold_dt: Optional[datetime] = None, include_shortcuts: bool = True) -> Dict[str, FileInfo]:
        if date_field not in {"created","modified"}: raise ValueError("date_field must be 'created' or 'modified'")
        if threshold_n is not None and threshold_dt is not None: raise ValueError("Specify either threshold_n or threshold_dt, not both")
        td_threshold = None
        if threshold_n is not None:
            if threshold_unit not in {"days","hours","minutes","seconds"}:
                raise ValueError("threshold_unit must be one of days, hours, minutes, seconds")
            td_threshold = timedelta(**{threshold_unit: threshold_n})
        now = datetime.now(); suffix = " - Shortcut.lnk"; results = {}
        if isinstance(filenames, str): filenames = [filenames]
        for orig in filenames:
            if include_shortcuts: candidates = [self.base_path/orig]
            else:
                raw = orig[:-len(suffix)] if orig.endswith(suffix) else orig
                candidates = [self.base_path/raw, self.base_path/(raw+suffix)]
            chosen = next((p for p in candidates if p.exists()), candidates[0])
            exists = chosen.exists()
            ctime = mtime = checked = age = None
            if exists:
                stat = chosen.stat()
                ctime = datetime.fromtimestamp(getattr(stat,"st_birthtime",stat.st_ctime))
                mtime = datetime.fromtimestamp(stat.st_mtime)
                checked = ctime if date_field=='created' else mtime
                age = now - checked
            is_older = is_younger = None
            if checked and threshold_dt:
                is_older = checked < threshold_dt; is_younger = checked > threshold_dt
            elif age and td_threshold:
                is_older = age > td_threshold; is_younger = age < td_threshold
            results[orig] = FileInfo(path=chosen, exists=exists, creation_time=ctime, modification_time=mtime,
                                    checked_time=checked, age=age, is_older_than=is_older, is_younger_than=is_younger)
        return results
    def Date(self, year: int, month: int, day: int, hour: int=0, minute: int=0, second: int=0, microsecond: int=0) -> datetime:
        return datetime(year, month, day, hour, minute, second, microsecond)
    def last_scheduled_update(self, hour: int = 0, minute: int = 0, now: Optional[datetime] = None) -> datetime:
        now = now or datetime.now(); weekday = now.weekday()
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if weekday >= 5: last = (now-timedelta(days=weekday-4)).replace(hour=hour,minute=minute,second=0,microsecond=0)
        elif now < scheduled:
            last = (now-timedelta(days=3)).replace(hour=hour,minute=minute,second=0,microsecond=0) if weekday==0 \
                else (now-timedelta(days=1)).replace(hour=hour,minute=minute,second=0,microsecond=0)
        else: last = scheduled
        return last         


# Download configuration and status messages.
@dataclass
class Package:
    id: str; filename: str; url: str; schedule_hour: int = 0; schedule_minute: int = 0

class DownloaderMessage: pass
class StartDownloadMessage(DownloaderMessage):
    def __init__(self, pkg: Package): self.package = pkg
class UpToDateMessage(DownloaderMessage):
    def __init__(self, pkg: Package): self.package = pkg
class StaleMessage(DownloaderMessage):
    def __init__(self, pkg: Package): self.package = pkg
class FinishDownloadMessage(DownloaderMessage):
    def __init__(self, pkg: Package): self.package = pkg
class ErrorMessage(DownloaderMessage):
    def __init__(self, pkg: Package, message: str): self.package = pkg; self.message = message


# Scheduled downloads.
"""
Manages a collection of Package entries and only downloads
those whose local copy is missing or stale (per schedule).
"""
class Download:
    def __init__(self, packages: List[Package], download_dir=Device.quantsumore_default):
        self.packages = {p.id: p for p in packages}; self.download_dir = download_dir
        self.inspector = FileInspector(self.download_dir)
    def incr_download(self, pkg_or_id: Union[str,Package], force: bool = False, replace: bool = False):
        import requests
        pkg = pkg_or_id if isinstance(pkg_or_id, Package) else self.packages[pkg_or_id]
        yield StartDownloadMessage(pkg)
        try:
            threshold = self.inspector.last_scheduled_update(pkg.schedule_hour, pkg.schedule_minute)
            info = self.inspector.inspect(pkg.filename, threshold_dt=threshold)[pkg.filename]
            if not force and info.exists and not info.is_older_than:
                yield UpToDateMessage(pkg); yield FinishDownloadMessage(pkg); return
            if info.exists: yield StaleMessage(pkg)
            resp = requests.get(pkg.url); resp.raise_for_status()
            dest = self.download_dir / pkg.filename; dest.parent.mkdir(parents=True, exist_ok=True)
            if replace:
                tmp = dest.with_suffix(dest.suffix + ".tmp")
                if tmp.exists(): tmp.unlink()
                with open(tmp, "wb") as f: f.write(resp.content)
                os.replace(tmp, dest)
            else:
                with open(dest, "wb") as f: f.write(resp.content)
            yield FinishDownloadMessage(pkg)
        except Exception as e:
            yield ErrorMessage(pkg, str(e))
    def download(self, pkg_or_id: Union[str,Package], force: bool = False, quiet: bool = False, replace: bool = False):
        for msg in self.incr_download(pkg_or_id, force, replace):
            if quiet: continue
            if isinstance(msg, UpToDateMessage): print(f"`{msg.package.id}` is up-to-date.")
            elif isinstance(msg, StaleMessage):
                print(f"Downloading `{msg.package.id}` …")
                print(f"`{msg.package.id}` is stale. Refreshing…")
            elif isinstance(msg, FinishDownloadMessage): print(f"Finished `{msg.package.id}` at {datetime.now()}.")
            elif isinstance(msg, ErrorMessage):
                print(f"Error downloading `{msg.package.id}`: {msg.message}"); break
    def update(self, quiet: bool = False, replace: bool = False):
        for pkg_id in self.packages:
            self.download(pkg_id, force=False, quiet=quiet, replace=replace)
            
def __dir__():
    return __all__
