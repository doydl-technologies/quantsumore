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



import json
import os
from pathlib import Path
from shutil import copyfile
from tempfile import NamedTemporaryFile
import re
import csv
from io import StringIO
import sqlite3
import unicodedata
from datetime import datetime, time, timezone
from copy import deepcopy
from functools import wraps
from threading import RLock

from quantsumore import APP_DATA_DIR
from ..sys_utils import Download, Package, FileInspector
from ._filebase import JSON, SQLiteDBHandler
from .._version import __version__
from ..date_parser import dtparse

__all__ = [
    'fxutil',
    'forex_hours',
    'equityquery',
    'CurrencyQuery',
    'ExchangeQuery',
    'CoinQuery',
    'major_forex_currencies',    
]



appdata_local_dir = str(APP_DATA_DIR)

# Stock tickers: file and URL
_STOCK_TICKERS_FILE_PATH = os.path.join(appdata_local_dir, 'stock_tickers.txt')
_STOCK_TICKERS_URL = (
    f"https://raw.githubusercontent.com/"
    f"doydl-technologies/quantsumore/"
    f"main/"
    f"files/stock_tickers.txt"
)
# Crypto config: file, DB, and URL
_CRYPTO_CONFIG_FILE_PATH = os.path.join(appdata_local_dir, 'all_data.json')
_CRYPTO_DATABASE_FILE = 'crypto.db'
_CRYPTO_CONFIG_URL = (
    f"https://raw.githubusercontent.com/"
    f"doydl-technologies/quantsumore/"
    f"main/"
    f"files/crypto/all_data.json"
)

packages = [
    Package(
        id="stocks",
        filename='stock_tickers.txt',
        url=(_STOCK_TICKERS_URL),
        schedule_hour=0,
    ),
    Package(
        id="crypto",
        filename='all_data.json',
        url=(_CRYPTO_CONFIG_URL),
        schedule_hour=1,
    ),
]

def _seed_reference_file(destination, bundled):
    """Publish a complete bundled snapshot without replacing an existing file."""
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, prefix=f".{destination.name}.",
                            suffix=".tmp", delete=False) as staged:
        temporary = Path(staged.name)
    try:
        copyfile(bundled, temporary)
        try:
            # Windows rename refuses an existing target; POSIX rename replaces it.
            if os.name == "nt":
                os.rename(temporary, destination)
            else:
                os.link(temporary, destination)
        except FileExistsError:
            pass
    finally:
        temporary.unlink(missing_ok=True)


for destination, bundled in [
    (Path(_STOCK_TICKERS_FILE_PATH), Path(__file__).resolve().parents[1] / 'files/stock_tickers.txt'),
    (Path(_CRYPTO_CONFIG_FILE_PATH), Path(__file__).resolve().parents[1] / 'files/crypto/all_data.json'),
]:
    _seed_reference_file(destination, bundled)

dl = Download(packages, download_dir=Path(appdata_local_dir))





# Equity lookups.
class equityquery:
    _registry = {}

    def __init__(self, symbol, company, exchange, yahoo_mapping, nasdaq_mapping):
        self.symbol = symbol
        self.company = company
        self.exchange = exchange
        self.yahoo_mapping = yahoo_mapping
        self.nasdaq_mapping = nasdaq_mapping
        equityquery._registry[symbol] = self

    def __repr__(self):
        return (f"equityquery(Symbol={self.symbol}, Company={self.company}, "
                f"Exchange={self.exchange}, yahoo_mapping={self.yahoo_mapping}, "
                f"nasdaq_mapping={self.nasdaq_mapping})")

    @staticmethod
    def initial_symbol_check(symbol):
        """Check if the symbol length is within the allowed range, contains no digits, and is not None."""
        if symbol is None:
            return False
        if not isinstance(symbol, str):
            return False
        if len(symbol) > 0 and len(symbol) <= 6:
            return not any(char.isdigit() for char in symbol)
        return False

    @classmethod
    def search_symbol(cls, symbol):
        """Search for a symbol in a case-insensitive manner."""
        if not cls.initial_symbol_check(symbol):
            return False
        search_symbol_lower = symbol.lower()
        return any(stock.symbol.lower() == search_symbol_lower for stock in cls._registry.values())

    @classmethod
    def search_yahoo_symbol(cls, symbol):
        """Search for a symbol specifically in yahoo_mapping in a case-insensitive manner."""
        if not cls.initial_symbol_check(symbol):
            return False
        search_symbol_lower = symbol.lower()
        return any(stock.yahoo_mapping.lower() == search_symbol_lower for stock in cls._registry.values())

    @classmethod
    def search_nasdaq_symbol(cls, symbol):
        """Search for a symbol specifically in nasdaq_mapping in a case-insensitive manner."""
        if not cls.initial_symbol_check(symbol):
            return False
        search_symbol_lower = symbol.lower()
        return any(stock.nasdaq_mapping.lower() == search_symbol_lower for stock in cls._registry.values())
    
    @classmethod
    def load_data(cls, file_path):
        """
        Load equity definitions from a local CSV file.
        First row is assumed to be the header.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"No such file: {file_path!r}")

        with path.open(newline='') as f:
            reader = csv.reader(f)
            next(reader)          # skip header
            for row in reader:
                if row:
                    cls(*row)    

    @classmethod
    def initialize_from_file(cls, data):
        f = StringIO(data)
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                cls(*row)

equityquery.load_data(file_path=_STOCK_TICKERS_FILE_PATH)




# Cryptocurrency metadata.
def _crypto_locked(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return locked


class CryptoConfig:
    """Refresh metadata atomically and expose isolated, coherent snapshots.

    SQLite serializes writers across instances/processes. Each read uses one
    database transaction. An instance lock protects staged input and publication
    of its cache. Use snapshot() to read all three collections from one generation;
    separate property accesses may span a refresh. Returned data is copied.
    """

    def __init__(self, config_file_path=_CRYPTO_CONFIG_FILE_PATH,
                 db_filename=_CRYPTO_DATABASE_FILE, db_directory=None):
        self.file_path = Path(config_file_path)
        self.db_filename = db_filename
        self.db_directory = Path(db_directory) if db_directory is not None else None
        self._lock = RLock()
        self._saved_json_content = {}
        self._snapshot = {"cryptos": [], "exchanges": [], "pairs": []}

    @property
    @_crypto_locked
    def saved_json_content(self):
        """Return an isolated copy of the staged input, not committed metadata."""
        return deepcopy(self._saved_json_content)

    @saved_json_content.setter
    @_crypto_locked
    def saved_json_content(self, value):
        self._saved_json_content = deepcopy(value)

    @property
    def cryptos(self):
        return self.snapshot()["cryptos"]

    @property
    def exchanges(self):
        return self.snapshot()["exchanges"]

    @property
    def pairs(self):
        return self.snapshot()["pairs"]

    @_crypto_locked
    def to_json(self):
        """Stage JSON input without changing the committed database or cache."""
        with self.file_path.open("r", encoding="utf-8") as source:
            self._saved_json_content = json.load(source)

    @_crypto_locked
    def to_sqlite(self):
        """Replace all tables in one transaction and reload the committed cache.

        Validation and database errors propagate. Failed writes preserve the
        previous database and cache; staged input remains available for correction.
        """
        if not self._saved_json_content:
            raise RuntimeError("Load metadata before writing the database.")
        handler = SQLiteDBHandler(
            filename=self.db_filename, directory=self.db_directory,
            json_data=deepcopy(self._saved_json_content)
        )
        handler.save(replace=True)
        self.parse_db()

    @_crypto_locked
    def parse_db(self):
        """Publish all collections together after a successful snapshot read."""
        handler = SQLiteDBHandler(filename=self.db_filename, directory=self.db_directory)
        if not handler.file_exists():
            raise RuntimeError(f"{handler.db_path} not found – run the full pipeline first.")
        snapshot = {}
        queries = (
            ("cryptos", "id, name, symbol, slug, is_active, status, rank", "rank"),
            ("exchanges", "exchangeId, exchangeName, exchangeSlug", "exchangeName"),
            ("pairs", "currencyId, currencySymbol, currency", "currency"),
        )
        with handler:
            # Explicit BEGIN pins one generation across all three SELECTs.
            handler.cursor.execute("BEGIN")
            try:
                handler.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {row[0] for row in handler.cursor.fetchall()}
                if not tables:
                    snapshot = {"cryptos": [], "exchanges": [], "pairs": []}
                for table, columns, order in queries if tables else ():
                    handler.cursor.execute(f"SELECT {columns} FROM {table} ORDER BY {order}")
                    keys = [column.strip() for column in columns.split(",")]
                    snapshot[table] = [dict(zip(keys, row)) for row in handler.cursor.fetchall()]
                handler.conn.commit()
            except Exception:
                handler.conn.rollback()
                raise
        self._snapshot = snapshot

    @_crypto_locked
    def snapshot(self):
        """Return one copied generation, reloading commits by other instances.

        Before first initialization a missing database yields empty collections.
        During first-time initialization readers see empty collections until
        the initial transaction commits. No partial snapshot is published.
        """
        handler = SQLiteDBHandler(filename=self.db_filename, directory=self.db_directory)
        if handler.file_exists():
            self.parse_db()
        return deepcopy(self._snapshot)

    @_crypto_locked
    def auto_run(self, application_data_directory, threshold_minutes=3, update_hour=1, verbose=False):
        """Reload or rebuild metadata according to the stored timestamps.

        Parameters
        ----------
        application_data_directory : str or Path
            Database directory and directory inspected for the JSON filename.
            The JSON read itself uses file_path.
        threshold_minutes : int, default 3
            Maximum absolute timestamp difference accepted by within_delta().
            If the JSON file's creation time and the stored database timestamp
            fall within this tolerance, reload without rebuilding.
        update_hour : int, default 1
            Scheduled hour passed to the file inspector's update-threshold calculation.
        verbose : bool, default False
            Print the selected refresh path and timestamp details.

        A missing database or creation timestamp triggers run(). Otherwise, run()
        rebuilds whenever the timestamp-tolerance test fails, even if the database
        timestamp is newer than the JSON file. Errors propagate to the caller.
        """
        self.db_directory = Path(application_data_directory)
        vprint = print if verbose else (lambda *a, **k: None)

        handler_kwargs = {
            "filename": self.db_filename,
            "directory": application_data_directory
        }

        temp = SQLiteDBHandler(**handler_kwargs)
        if not temp.file_exists():
            vprint("No existing database found. Creating new DB from JSON…")
            return self.run()

        with SQLiteDBHandler(**handler_kwargs) as dbh:
            created_iso = dbh.get_creation_time()
        if created_iso is None:
            return self.run()
        last_db_dt = dtparse.parse(created_iso)
        vprint(f"Database found. Created at: {created_iso}")

        inspector    = FileInspector(application_data_directory)
        threshold_dt = inspector.last_scheduled_update(hour=update_hour)
        info_map     = inspector.inspect(self.file_path.name, threshold_dt=threshold_dt)
        file_info    = info_map[self.file_path.name]
        vprint(f"JSON file inspected. Exists: {file_info.exists}. "
               f"Created at: {getattr(file_info, 'creation_time', None)}. "
               f"Scheduled threshold: {threshold_dt}")

        if file_info.exists and dtparse.within_delta(
                file_info.creation_time,
                last_db_dt,
                threshold_minutes,
                "minutes"
        ):
            vprint("Database is fresh. Loading from DB only (no re-creation needed).")
            return self.run_from_db()
        else:
            if file_info.exists:
                vprint("Database is stale or JSON updated. Rebuilding database from JSON.")
            else:
                vprint("JSON file missing or too old. Rebuilding database from JSON.")
            return self.run()
            
    @_crypto_locked
    def run(self):
        """Stage the input, atomically replace the database, and reload the cache."""
        self.to_json()
        self.to_sqlite()

    @_crypto_locked
    def run_from_db(self):
        """Reload one committed database generation without modifying it."""
        self.parse_db()


# auto_run selects JSON rebuilding or database loading based on freshness checks.
config = CryptoConfig(
    config_file_path=_CRYPTO_CONFIG_FILE_PATH,
    db_filename=_CRYPTO_DATABASE_FILE
)

config.auto_run(application_data_directory=appdata_local_dir)


class Query:
    """Group lookups for currency pairs, exchanges and cryptocurrencies.

    Currency and Exchange use the JSON data supplied at construction.
    Coin reads SQLite metadata and caches query results. These query objects
    are independent of CryptoConfig's live snapshots; recreating or explicitly
    refreshing a CryptoConfig does not update data already held by a Query.
    """
    def __init__(self, json_data=None):
        self.json_data = json_data

    class Currency:
        def __init__(self, json_data):
            self.handler = JSON(json_data=json_data)                   
            self._data = None

        @property
        def data(self):
            if self._data is None:
                json_data = self.handler.load()
                self._data = json_data
            return self._data

        def ID(self, qID):
            return [ccy for ccy in self.data if str(ccy['currencyId']) == str(qID)]

        def Symbol(self, symbol):
            symbol = symbol.lower()
            return [ccy for ccy in self.data if ccy['currencySymbol'].lower() == symbol]

        def SymbolreturnID(self, symbol):
            symbol = symbol.lower()
            for ccy in self.data:
                if ccy['currencySymbol'].lower() == symbol:
                    return ccy['currencyId']
            return None
           
        def __dir__(self):
            return ['ID', 'Symbol', 'SymbolreturnID', 'data']  

    class Exchange:
        def __init__(self, json_data):
            self.handler = JSON(json_data=json_data)
            self._data = None

        @property
        def data(self):
            if self._data is None:
                json_data = self.handler.load()
                self._data = json_data
            return self._data        

        def ID(self, exchange_id):
            exch = str(exchange_id)
            return [exchange for exchange in self.data if exchange['exchangeId'] == exch]

        def Name(self, exchange_name):
            exchange_name = exchange_name.lower()
            return [exchange for exchange in self.data if exchange['exchangeName'].lower() == exchange_name]

        def Slug(self, exchange_slug):
            exchange_slug = exchange_slug.lower()
            return [exchange for exchange in self.data if exchange['exchangeSlug'].lower() == exchange_slug]

        def FindID(self, identifier):
            identifier = identifier.lower()
            for exchange in self.data:
                if exchange['exchangeName'].lower() == identifier or exchange['exchangeSlug'].lower() == identifier:
                    return int(exchange['exchangeId'])
            return None

        def __dir__(self):
            return ['ID', 'Name', 'Slug', 'FindID', 'data']        

    class Coin:
        def __init__(self, file):
            self.db_path = SQLiteDBHandler(file).path  
            self.cache = {
                'ID': {},
                'Name': {},
                'Slug': {},
                'ListSlugs': None
            }
        def append_active_condition(self, query):
            """Append an is_active = 1 condition to the WHERE clause in a query."""
            if 'WHERE' in query:
                return query + ' AND is_active = 1'
            else:
                return query + ' WHERE is_active = 1'

        def case_sensitive_search(self, word_to_find, word_to_check):
            return word_to_find == word_to_check
           
        def execute_query(self, query, params):
            query = self.append_active_condition(query)
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
            except sqlite3.Error as e:
                return []

        @staticmethod
        def normalize_string(input_string):
            """Normalize a string by removing special characters and accents but keep the case intact."""
            nfkd_form = unicodedata.normalize('NFKD', input_string)
            ascii_string = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
            return re.sub(r'[^\w\s]', '', ascii_string)

        def ID(self, crypto_id):
            if crypto_id in self.cache['ID']:
                return self.cache['ID'][crypto_id]
            query = 'SELECT * FROM cryptos WHERE id = ?'
            result = self.execute_query(query, (crypto_id,))
            self.cache['ID'][crypto_id] = result
            return result

        def Name(self, name):
            if name in self.cache['Name']:
                return self.cache['Name'][name]
            normalized_name = self.normalize_string(name)
            query = 'SELECT * FROM cryptos WHERE name LIKE ?'
            data = self.execute_query(query, (f'%{normalized_name}%',))
            filtered_data = [item for item in data if self.case_sensitive_search(name, item['name'])]
            self.cache['Name'][name] = filtered_data
            return filtered_data

        def Slug(self, slug):
            slug = slug.lower()
            if slug in self.cache['Slug']:
                return self.cache['Slug'][slug]
            query = 'SELECT * FROM cryptos WHERE slug = ?'
            result = self.execute_query(query, (slug,))
            self.cache['Slug'][slug] = result
            return result

        def ListSlugs(self):
            if self.cache['ListSlugs'] is not None:
                return self.cache['ListSlugs']
            query = 'SELECT name, symbol, slug FROM cryptos'
            result = self.execute_query(query, ())
            self.cache['ListSlugs'] = result
            return result

        def __dir__(self):
            return ['ID', 'Name', 'Slug', 'ListSlugs']




query = Query()
CurrencyQuery = query.Currency(json_data=config.pairs)
ExchangeQuery = query.Exchange(json_data=config.exchanges)
CoinQuery = query.Coin(file=_CRYPTO_DATABASE_FILE)




# Forex lookups.
major_forex_currencies = {
    'AUD': 'Australian Dollar', 'CAD': 'Canadian Dollar', 'CHF': 'Swiss Franc', 'CNY': 'Chinese Yuan Renminbi', 'CZK': 'Czech Koruna',
    'DKK': 'Danish Kroner', 'EUR': 'Euro', 'GBP': 'Pound Sterling', 'HKD': 'Hong Kong Dollar', 'HRK': 'Croatia Kuna',
    'HUF': 'Hungary Forint', 'ILS': 'Israel Shekel', 'INR': 'Indian Rupee', 'JPY': 'Japanese Yen', 'MXN': 'Mexican Peso',
    'NZD': 'New Zealand Dollar', 'PLN': 'Polish Zloty', 'SEK': 'Swedish Kroner', 'USD': 'US Dollar', 'ZAR': 'South African Rand',
    'AED': 'United Arab Emirates Dirham',
}
all_currency_names = {
    'AFN': 'Afghan Afghanis', 'DZD': 'Algerian Dinar', 'ARS': 'Argentine Peso', 'AMD': 'Armenia Drams', 'AWG': 'Aruba Guilder',
    'AUD': 'Australian Dollar', 'BSD': 'Bahamian Dollar', 'BHD': 'Bahrain Dinar', 'BDT': 'Bangladesh Taka', 'BBD': 'Barbados Dollars',
    'LSL': 'Basotho Loti', 'BYR': 'Belarus Rubles', 'BZD': 'Belize Dollars', 'BMD': 'Bermudian Dollar', 'BTN': 'Bhutanese Ngultrum',
    'BOB': 'Bolivia Bolivianos', 'BAM': 'Bosnian Marka', 'BWP': 'Botswana Pula', 'BRL': 'Brazilian Real', 'GBP': 'British Pound',
    'BND': 'Brunei Darussalam Dollars', 'BGN': 'Bulgarian Lev', 'BIF': 'Burundi Francs', 'KHR': 'Cambodia Riels', 'CAD': 'Canadian Dollar',
    'CVE': 'Cape Verde Escudos', 'KYD': 'Caymanian Dollar', 'XAF': 'Central African Cfa Franc Beac', 'XOF': 'Cfa Franc', 'XPF': 'Cfp Franc',
    'CLP': 'Chilean Peso', 'CNH': 'Chinese Offshore Spot', 'CNY': 'Chinese Yuan', 'COP': 'Colombian Peso', 'KMF': 'Comorian Franc',
    'CDF': 'Congolese Franc', 'CRC': 'Costa Rica Colones', 'HRK': 'Croatian Kuna', 'CUP': 'Cuba Pesos', 'CYP': 'Cyprus Pound',
    'CZK': 'Czech Koruna', 'DKK': 'Danish Krone', 'DJF': 'Djibouti Francs', 'DOP': 'Dominican Peso', 'XCD': 'East Caribbean Dollar',
    'EGP': 'Egyptian Pound', 'SVC': 'El Salvador Colones', 'EEK': 'Estonian Kroon', 'ETB': 'Ethiopia Birr', 'EUR': 'Euro',
    'FJD': 'Fiji Dollar', 'GMD': 'Gambia Dalasi', 'GEL': 'Georgian Lari', 'GHS': 'Ghanaian Cedi', 'XAU': 'Gold',
    'GTQ': 'Guatemala Quetzal', 'GNF': 'Guinean Franc', 'GYD': 'Guyanese Dollar', 'HTG': 'Haiti Gourdes', 'HNL': 'Honduras Lempira',
    'HKD': 'Hong Kong Dollar', 'HUF': 'Hungarian Forint', 'ISK': 'Icelandic Krona', 'XDR': 'Imf Drawing Rights', 'INR': 'Indian Rupee',
    'IDR': 'Indonesian Rupiah', 'IRR': 'Iran Rials', 'IQD': 'Iraq Dinars', 'ILS': 'Israeli Shekel', 'JMD': 'Jamaican Dollar',
    'JPY': 'Japanese Yen', 'JOD': 'Jordanian Dinar', 'KZT': 'Kazakhstan Tenge', 'KES': 'Kenyan Shilling', 'LFX': 'Khazanah Sukuk',
    'KRW': 'Korean Won', 'KWD': 'Kuwaiti Dinar', 'KGS': 'Kyrgyzstani Som', 'LAK': 'Laos Kips', 'LVL': 'Latvian Lats',
    'LBP': 'Lebanese Pound', 'LRD': 'Liberia Dollar', 'LYD': 'Libya Dinars', 'LTL': 'Lithuanian Litas', 'MOP': 'Macau Patacas',
    'MKD': 'Macedonian Denar', 'MGA': 'Madagascar Ariary', 'MWK': 'Malawian Kwacha', 'MYR': 'Malaysian Ringgit', 'MVR': 'Maldives Rufiyaa',
    'MRO': 'Mauritania Ouguiyas', 'MUR': 'Mauritian Rupee', 'MXN': 'Mexican Peso', 'MDL': 'Moldova Lei', 'MAD': 'Moroccan Dirham',
    'MZN': 'Mozambique Metical', 'MMK': 'Myanmar Burma Kyats', 'NAD': 'Namibian Dollar', 'NPR': 'Nepal Nepal Rupees', 'NZD': 'New Zealand Dollar',
    'NIO': 'Nicaraguan Cordoba', 'NGN': 'Nigerian Naira', 'NOK': 'Norwegian Krone', 'OMR': 'Omani Rial', 'PKR': 'Pakistan Rupee',
    'XPD': 'Palladium', 'PAB': 'Panama Balboa', 'PGK': 'Papua New Guinea Kina', 'PYG': 'Paraguayan Guarani', 'PEN': 'Peruvian Sol',
    'PHP': 'Philippine Peso', 'XPT': 'Platinum', 'PLN': 'Polish Zloty', 'QAR': 'Qatari Riyal', 'RON': 'Romanian Lei',
    'RUB': 'Russian Ruble', 'RWF': 'Rwandan Franc', 'STD': 'Sao Tome Dobra', 'SAR': 'Saudi Riyal', 'RSD': 'Serbian Dinar',
    'SCR': 'Seychelles Rupee', 'SLL': 'Sierra Leonean', 'XAG': 'Silver', 'SGD': 'Singapore Dollar', 'SKK': 'Slovak Koruna',
    'SOS': 'Somali Shillings', 'ZAR': 'South African Rand', 'SDR': 'Special Drawing Rights', 'LKR': 'Sri Lankan Rupee', 'SHP': 'St Helena Pound',
    'SDG': 'Sudan Pounds', 'SDD': 'Sudanese Dinars', 'SZL': 'Swazi Lilangeni', 'SEK': 'Swedish Krone', 'CHF': 'Swiss Franc',
    'SYP': 'Syria Pounds', 'TWD': 'Taiwan Dollar', 'TJS': 'Tajikistani Somoni', 'TZS': 'Tanzania Shillings', 'THB': 'Thai Baht',
    'TTD': 'Trinidadian Dollar', 'TND': 'Tunisian Dinar', 'TRY': 'Turkish New Lira', 'TMT': 'Turkmenistan Manat', 'AED': 'U.A.E. Dirham',
    'USD': 'U.S. Dollar', 'UGX': 'Ugandan Shillings', 'UAH': 'Ukraine Hryvnia', 'UYU': 'Uruguayan Peso', 'UZS': 'Uzbekistani Som',
    'VEF': 'Venezuelan Bolivars', 'VND': 'Vietnam Dong', 'YER': 'Yemeni Rials', 'ZMK': 'Zambia Kwacha', 'ZMW': 'Zambian Kwacha'
}
forex_major_pairs = {# Nasdaq symbol mappings.
    "EURUSD": "EURO US DOLLAR", "GBPUSD": "BRITISH POUND US DOLLAR", "USDJPY": "US DOLLAR JAPANESE YEN",
    "USDCHF": "US DOLLAR SWISS FRANC", "USDCAD": "US DOLLAR CANADIAN DOLLAR", "AUDUSD": "AUSTRALIAN DOLLAR US DOLLAR",
    "USDMXN": "US DOLLAR MEXICAN PESO", "USDINR": "US DOLLAR INDIAN RUPEE", "USDRUB": "US DOLLAR RUSSIAN RUBLE",
    "USDBRL": "US DOLLAR BRAZILIAN REAL"
}

class fxutil:
    """Normalize, tokenize and look up fiat currency codes and pairs.

    Static methods use the module's major and broader currency registries.
    which lists available codes; query selects code, name, pair or existence
    results. Validation and missing-value behavior depend on the operation.
    """
    class which:
        """List codes from the major or broader fiat-currency registry."""
        @staticmethod
        def major(currencies=major_forex_currencies):
            """
            Returns a list of all 3-letter ISO currency codes classified as 'major' currencies.

            Parameters:
            -----------
            currencies : dict, optional
                Dictionary of major currencies to use. Defaults to the internal `major_forex_currencies` dictionary.

            Returns
            -----------
            list of str
                List of currency codes (e.g., ['USD', 'EUR', 'JPY']).

            Example
            -----------
            >>> which.major()
            ['AUD', 'CAD', 'CHF', ...]
            """        	
            return list(currencies.keys())
           
        @staticmethod
        def quote(currencies=all_currency_names):
            """
            Returns a list of all available 3-letter ISO currency codes from a broader set,
            including major, minor, and exotic currencies.

            Parameters:
            -----------
            currencies : dict, optional
                Dictionary of currencies to use. Defaults to the internal `all_currency_names` dictionary.

            Returns
            -----------
            list of str
                List of currency codes (e.g., ['USD', 'EUR', 'JPY', ..., 'UZS', 'ZMW']).

            Example
            -----------
            >>> which.quote()
            ['AFN', 'DZD', 'ARS', ...]
            """        	
            return list(currencies.keys())

    @staticmethod  
    def _join_currency(currency):
        """
        Joins a list of one or two 3-letter currency codes into a single string representation.

        Parameters:
        -----------
        currency : list or str
            A list containing one or two currency codes as strings (each 3 characters), or a single string.

        Returns
        -----------
        str
            Concatenated currency code string if input is a valid list, otherwise returns the input unchanged.

        Examples
        -----------
        >>> _join_currency(['USD', 'JPY'])
        'USDJPY'
        >>> _join_currency(['EUR'])
        'EUR'
        >>> _join_currency('USD')
        'USD'
        """
        if isinstance(currency, list) and len(currency) == 2:
            if all(isinstance(item, str) and len(item) == 3 for item in currency):
                return ''.join(currency)
        if isinstance(currency, list) and len(currency) == 1:
            return currency[0]
        return currency
       
    @staticmethod  
    def redact(s: str) -> str:
        # split() with no args breaks on any whitespace, so joining back drops them all.
        return "".join(s.split())
       
    @staticmethod   
    def tokenize(currency):
        """
        Parses and tokenizes a currency code or currency pair into individual 3-letter codes.

        Parameters:
        -----------
        currency : str or list of str
            Currency pair string (e.g., 'USDJPY', 'usd/jpy', 'eur_usd') or a list of such strings.

        Returns
        -----------
        list or tuple or None
            List or tuple of extracted currency codes (e.g., ['USD', 'JPY']), a single code (e.g., ['USD']),
            or None if no valid code is found.

        Examples
        -----------
        >>> tokenize('USDJPY')
        ['USD', 'JPY']
        >>> tokenize(['eur/usd', 'jpy'])
        ['EUR', 'USD', 'JPY']
        >>> tokenize('usd', as_tuple=True)
        ('USD',)
        """
        if isinstance(currency, str):
            parts = [currency]
        elif isinstance(currency, list):
            if not all(isinstance(x, str) for x in currency):
                raise TypeError("All elements in list must be strings")
            parts = currency.copy()
        else:
            raise TypeError("Expression only supports str or list of str")
        
        chunks = []
        for part in parts:
            cleaned = fxutil.redact(part)
            for piece in cleaned.split(','):
                if piece:
                    chunks.append(piece)
        
        codes = []
        for chunk in chunks:
            up = chunk.upper()
            # match a pair like USDJPY, USD-JPY, USD/JPY, USD_JPY
            m = re.fullmatch(r'([A-Z]{3})(?:[-_/]?([A-Z]{3}))?', up)
            if not m:
                continue
            c1, c2 = m.groups()
            codes.append(c1)
            if c2 and c2 != c1:
                codes.append(c2)
        
        if not codes:
            return None

        seen = set()
        unique = []
        for c in codes:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        return unique
       
    @staticmethod
    def query(query, query_type="major", ret_type=None):
        """
        Looks up a currency code or currency name and returns the code, name, both, or existence as a bool.

        Parameters
        -----------
        query : str
            The currency code (e.g., 'USD') or currency name (e.g., 'US Dollar') to look up.
        query_type : str, optional
            Which currency set to search in: 'major' (default), 'major_pairs', or 'quote'.
        ret_type : str or None, optional
            What to return:
              - 'code' → 3‑letter code (e.g. 'USD')
              - 'name' → full currency name (e.g. 'US Dollar')
              - 'bool' → True if found, False otherwise
              - None    → both as a `(code, name)` tuple

        Returns
        -----------
        str or tuple or bool or None
            Depending on `ret_type`: the code, name, tuple, boolean, or None if not found.

        Examples
        -----------
        >>> query('usd', ret_type='name')
        'US Dollar'
        >>> query('Japanese Yen', query_type='quote', ret_type='code')
        'JPY'
        >>> query('CAD')
        ('CAD', 'Canadian Dollar')
        >>> query('EURUSD', query_type='major_pairs', ret_type='name')
        'Euro/US Dollar'
        >>> query('XYZ', ret_type='bool')
        False
        """
        if isinstance(query, str):
            query = fxutil.redact(query)

        if query_type == "major":
            currency_dict = major_forex_currencies
        elif query_type == "major_pairs":
            currency_dict = forex_major_pairs
        else:
            currency_dict = all_currency_names

        ql = query.lower()
        for code, name in currency_dict.items():
            if ql == code.lower() or ql == name.lower():
                if ret_type is not None:
                    rt = ret_type.lower()
                    if rt == "code":
                        return code
                    if rt == "name":
                        return name
                    if rt == "bool":
                        return True
                return (code, name)

        if ret_type is not None and ret_type.lower() == "bool":
            return False
        return None



def _timezone_info():
    """Return ZoneInfo, falling back to pytz when the standard-library import is unavailable."""
    try:
        # Prefer the standard-library timezone database when available.
        from zoneinfo import ZoneInfo
        return ZoneInfo
    except ImportError:
        from pytz import timezone as ZoneInfo  # Fall back to the optional pytz timezone implementation.
        return ZoneInfo
       
class ForexMarketHours:
    """Check configured UTC trading-session windows and report local time.

    Session windows may cross midnight. Local-time conversion uses the
    configured timezone, including its DST rules. Session checks use the
    configured daily hours; they do not consult a holiday calendar.
    """
    # Define the four Forex sessions in UTC
    _SESSIONS_UTC = {
        'sydney':   {'start': time(22, 0), 'end': time( 6, 0)},
        'tokyo':    {'start': time( 0, 0), 'end': time( 8, 0)},
        'london':   {'start': time( 8, 0), 'end': time(16, 0)},
        'new_york': {'start': time(13, 0), 'end': time(21, 0)},
    }

    def __init__(self, timezone: str = "US/Central"):
        """
        Initialize the ForexMarketHours instance with a specified local timezone.
        The timezone is used for converting UTC time to local time when reporting
        market open status. Defaults to "US/Central".
        """    	
        ZoneInfo = _timezone_info()
        self.local_tz = ZoneInfo(timezone)  

    @staticmethod
    def _in_time_window(t: time, start: time, end: time) -> bool:
        """
        Determine if a given time falls within a specified window.
        Handles time windows that may wrap past midnight (e.g., 22:00 to 06:00).
        Returns True if 't' is in the interval [start, end), otherwise False.
        Static method.
        """    	
        # Handles windows that wrap past midnight
        if start < end:
            return start <= t < end
        return t >= start or t < end

    def is_forex_market_open(self) -> bool:
        """
        Check if any major Forex session (Sydney, Tokyo, London, New York) is currently open.
        Returns True if at least one session is active based on the current UTC time,
        otherwise returns False.
        """
        now_utc = datetime.now(timezone.utc).time()
        for win in self._SESSIONS_UTC.values():
            if self._in_time_window(now_utc, win['start'], win['end']):
                return True
        return False

    @property
    def time(self):
        """
        If the Forex market is open, return the current local time (as a string in
        "YYYY-MM-DD HH:MM:SS" format) for the configured timezone.
        If the market is closed, return None.
        """
        if not self.is_forex_market_open():
            return None
        # Convert UTC to the configured local timezone, including DST.
        now_utc = datetime.now(timezone.utc)
        now_central = now_utc.astimezone(self.local_tz)
        return now_central.strftime("%Y-%m-%d %H:%M:%S")

forex_hours = ForexMarketHours()

def __dir__():
    return __all__


