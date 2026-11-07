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


import sqlite3
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

from quantsumore import APP_DATA_DIR


__all__ = ['JSON', 'SQLiteDBHandler']





_APP_DATA_DIR = str(APP_DATA_DIR)

# JSON

class JSON:
    def __init__(self, filename=None, directory=None, json_data=None):
        self.json_data = json_data
        self._batch = False
        directory = directory or _APP_DATA_DIR
        if json_data is None:
            if filename is None:
                raise ValueError("Either filename or json_data must be provided.")
            self.filename = filename
            self.json_dir = directory
            if self.json_dir is None:
                raise FileNotFoundError(f"Directory '{directory}' not found in the expected paths.")
            self.json_path = os.path.join(self.json_dir, self.filename)
        else:
            self.filename = filename if filename else "data.json"
            self.json_path = None

    def save(self, data, force_save_to_file=False):
        if force_save_to_file or self.json_path:
            if self.json_path is None:
                raise ValueError("File path not set. Provide a filename and directory for file operations.")
            try:
                with open(self.json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4) if isinstance(data, dict) else f.write(data)
            except Exception as e:
                print(f"Error saving data to {self.json_path}: {e}")
        else: self.json_data = data

    def load(self, from_file=False, key=None):
        if from_file and self.json_path:
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data = data.get(key, None) if key else data
                    self.json_data = data
                    return data
            except FileNotFoundError:
                print(f"No such file: '{self.json_path}'")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from the file: '{self.json_path}'")
            except Exception as e:
                print(f"Error loading data from {self.json_path}: {e}")
        elif self.json_data:
            data = self.json_data
            return data.get(key, None) if key else data
        else: raise ValueError("No data available to load. Provide json_data or enable file loading.")

    def flatten(self, initial_path, keys, data=None):
        data = data if data is not None else self.json_data
        try:
            for part in initial_path.split('.'):
                data = data[int(part)] if part.isdigit() else data[part]
        except KeyError as e:
            raise KeyError(f"Path error: {e}")
        flattened = {}
        for key in keys:
            try:
                ref = data
                for part in key.split('.'):
                    ref = ref[int(part)] if part.isdigit() else ref[part]
                flattened[key.replace('.', '_')] = ref
            except KeyError as e:
                print(f"Flattening error on key {key}: {e}")
                flattened[key.replace('.', '_')] = None
        self.flattened_json_data = flattened
        return flattened

    def dataframe(self, data=None, rename_columns=None, column_order=None, data_types=None):
        import pandas as pd
        data = data if data is not None else self.flattened_json_data
        if isinstance(data, dict) and all(not isinstance(v, (list, tuple, set, dict)) for v in data.values()):
            data = {k: [v] for k, v in data.items()}
        df = pd.DataFrame(data)
        if rename_columns: df.rename(columns=rename_columns, inplace=True, errors='ignore')
        if column_order:
            df = df[[col for col in column_order if col in df.columns]]
        if data_types:
            valid_types = {k: v for k, v in data_types.items() if k in df.columns}
            df = df.astype(valid_types, errors='ignore')
        self.dataframe_json_data = df
        return df

    def clear_json(self):
        self.json_data = self.flattened_json_data = self.dataframe_json_data = None
        print("All data has been cleared.")

    def file_exists(self): return os.path.exists(self.json_path)
    def last_modified(self, as_string=False):
        if self.file_exists():
            ts = os.path.getmtime(self.json_path)
            return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if as_string else datetime.fromtimestamp(ts)
        return None

    def is_outdated(self):
        if self.file_exists():
            dt = datetime.fromtimestamp(os.path.getmtime(self.json_path))
            return (datetime.now() - dt) > timedelta(days=30)
        return True

       
       
# SQLite metadata storage.

class SQLiteDBHandler:
    def __init__(self, filename, directory=None, json_data=None):
        directory = directory or _APP_DATA_DIR
        filename_path, directory_path = Path(filename), Path(directory)
        if directory_path.is_file():
            filename_path, directory_path = directory_path, directory_path.parent
        if filename_path.is_absolute() or filename_path.parent != Path('.'):
            self.db_path, self.db_dir, self.filename = str(filename_path), str(filename_path.parent), filename_path.name
        else:
            self.db_dir, self.filename = str(directory_path), filename_path.name
            self.db_path = os.path.join(self.db_dir, self.filename)
        self.path = self.Path()
        self.conn = self.cursor = None
        self.json_data = json_data
        self._batch = False

    def connect(self):
        if not self.conn:
            Path(self.db_dir).mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, timeout=30)
            self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = self.cursor = None

    def __enter__(self): self.connect(); return self
    def __exit__(self, exc_type, exc_val, exc_tb): self.close()

    def reset_database(self):
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path): os.remove(self.db_path)

    def ensure_database(self):
        self.connect()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cryptos (
                id INTEGER PRIMARY KEY, name TEXT, symbol TEXT, slug TEXT,
                is_active INTEGER, status INTEGER, rank INTEGER)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY, value TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exchanges (
                exchangeId INTEGER PRIMARY KEY, exchangeName TEXT, exchangeSlug TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pairs (
                currencyId INTEGER PRIMARY KEY, currencySymbol TEXT, currency TEXT)
        ''')
        self.cursor.execute("SELECT value FROM metadata WHERE key='created_at'")
        if self.cursor.fetchone() is None:
            now = datetime.now().isoformat()
            self.cursor.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)", ("created_at", now)
            )
        if not self._batch:
            self.conn.commit()

    def parse_json(self):
        return [
            (item['id'], item['name'], item['symbol'], item['slug'],
             item['is_active'], item['status'], item['rank'])
            for item in self.json_data["cryptos"].values()
        ]

    def parse_exchanges(self):
        return [
            (int(item["exchangeId"]), item["exchangeName"], item["exchangeSlug"])
            for item in self.json_data.get("crypto_exchanges", {}).values()
        ]

    def parse_pairs(self):
        return [
            (item["currencyId"], item["currencySymbol"], name)
            for name, item in self.json_data.get("pairs", {}).items()
        ]
        
    def insert_data(self, transformed_data):
        for item in transformed_data:
            self.cursor.execute('''
                INSERT INTO cryptos (id, name, symbol, slug, is_active, status, rank)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, symbol=excluded.symbol, slug=excluded.slug,
                is_active=excluded.is_active, status=excluded.status, rank=excluded.rank;
            ''', item)
        if not self._batch:
            self.conn.commit()

    def insert_exchanges(self, exchanges):
        for item in exchanges:
            self.cursor.execute('''
                INSERT INTO exchanges (exchangeId, exchangeName, exchangeSlug)
                VALUES (?, ?, ?)
                ON CONFLICT(exchangeId) DO UPDATE SET
                exchangeName=excluded.exchangeName, exchangeSlug=excluded.exchangeSlug;
            ''', item)
        if not self._batch:
            self.conn.commit()

    def insert_pairs(self, pairs):
        for item in pairs:
            self.cursor.execute('''
                INSERT INTO pairs (currencyId, currencySymbol, currency)
                VALUES (?, ?, ?)
                ON CONFLICT(currencyId) DO UPDATE SET
                currencySymbol=excluded.currencySymbol, currency=excluded.currency;
            ''', item)
        if not self._batch:
            self.conn.commit()

    def file_exists(self): return os.path.exists(self.db_path)
    def get_creation_time(self):
        self.connect()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata'")
        if self.cursor.fetchone() is None:
            return None
        self.cursor.execute("SELECT value FROM metadata WHERE key='created_at'")
        result = self.cursor.fetchone()
        return result[0] if result else None

    def Path(self):
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path):
            return self.db_path
        return None
           
    def save(self, replace=False):
        """Commit all metadata tables together; retain existing data on failure."""
        # Validate every collection before opening a write transaction.
        cryptos = self.parse_json()
        exchanges = self.parse_exchanges()
        pairs = self.parse_pairs()
        try:
            self.connect()
            self.cursor.execute("BEGIN IMMEDIATE")
            self._batch = True
            self.ensure_database()
            if replace:
                for table in ("cryptos", "exchanges", "pairs"):
                    self.cursor.execute(f"DELETE FROM {table}")
                self.cursor.execute(
                    "UPDATE metadata SET value=? WHERE key='created_at'",
                    (datetime.now().isoformat(),)
                )
            self.insert_data(cryptos)
            self.insert_exchanges(exchanges)
            self.insert_pairs(pairs)
            self.conn.commit()
        except Exception:
            if self.conn is not None:
                self.conn.rollback()
            raise
        finally:
            self._batch = False
            self.close()


def __dir__():
    return __all__
