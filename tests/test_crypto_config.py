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


import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event, get_ident
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import unittest
from unittest.mock import patch

from tests.runtime import prepare_runtime


def metadata(generation):
    return {
        "cryptos": {"coin": {"id": 1, "name": generation, "symbol": "COIN",
                    "slug": "coin", "is_active": 1, "status": 1, "rank": 1}},
        "crypto_exchanges": {"exchange": {"exchangeId": 1,
                    "exchangeName": generation, "exchangeSlug": "exchange"}},
        "pairs": {generation: {"currencyId": 1, "currencySymbol": "USD"}},
    }


class CryptoConfigTests(unittest.TestCase):
    def setUp(self):
        from quantsumore.api.market_utils import CryptoConfig
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "metadata.json"
        self.config = CryptoConfig(self.source, "test.db", self.directory.name)
        self.source.write_text(json.dumps(metadata("old")), encoding="utf-8")
        self.config.run()

    def assert_generation(self, snapshot, generation):
        self.assertEqual(snapshot["cryptos"][0]["name"], generation)
        self.assertEqual(snapshot["exchanges"][0]["exchangeName"], generation)
        self.assertEqual(snapshot["pairs"][0]["currency"], generation)

    def test_write_reloads_cache_and_other_instances_observe_commit(self):
        from quantsumore.api.market_utils import CryptoConfig
        observer = CryptoConfig(self.source, "test.db", self.directory.name)
        self.assert_generation(observer.snapshot(), "old")
        self.config.saved_json_content = metadata("new")
        self.config.to_sqlite()
        self.assert_generation(self.config.snapshot(), "new")
        self.assert_generation(observer.snapshot(), "new")

    def test_dotted_database_directories_support_initialization_and_refresh(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        for name in ("cache.v1", "metadata.db"):
            for existing in (False, True):
                with self.subTest(directory=name, existing=existing):
                    directory = Path(self.directory.name) / str(existing) / name
                    if existing:
                        directory.mkdir(parents=True)
                    config = CryptoConfig(self.source, "test.db", directory)
                    config.run()
                    expected = directory / "test.db"
                    self.assertTrue(expected.is_file())
                    self.assertEqual(Path(SQLiteDBHandler("test.db", directory).db_path), expected)
                    self.assert_generation(config.snapshot(), "old")
                    config.saved_json_content = metadata("new")
                    config.to_sqlite()
                    self.assert_generation(config.snapshot(), "new")

    def test_explicit_database_filename_paths_remain_supported(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        database = Path(self.directory.name) / "explicit.sqlite3"
        config = CryptoConfig(self.source, database, self.directory.name)
        config.run()
        self.assertTrue(database.is_file())
        self.assert_generation(config.snapshot(), "old")
        handler = SQLiteDBHandler("ignored.db", database)
        self.assertEqual(Path(handler.db_path), database)

    def test_returned_collections_and_staged_input_are_isolated(self):
        staged = metadata("new")
        self.config.saved_json_content = staged
        staged["cryptos"]["coin"]["name"] = "mutated"
        self.config.saved_json_content["cryptos"]["coin"]["name"] = "mutated"
        self.config.cryptos[0]["name"] = "mutated"
        self.config.snapshot()["pairs"].clear()
        self.assert_generation(self.config.snapshot(), "old")
        self.config.to_sqlite()
        self.assert_generation(self.config.snapshot(), "new")

    def test_reader_observes_old_generation_until_refresh_commits(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        written, release = Event(), Event()
        original = SQLiteDBHandler.insert_data

        def pause_after_crypto_write(handler, data):
            original(handler, data)
            written.set()
            if not release.wait(10):
                raise TimeoutError("Reader did not release the writer")

        self.config.saved_json_content = metadata("new")
        with patch.object(SQLiteDBHandler, "insert_data", pause_after_crypto_write):
            with ThreadPoolExecutor(max_workers=1) as executor:
                writer = executor.submit(self.config.to_sqlite)
                try:
                    self.assertTrue(written.wait(10))
                    reader = CryptoConfig(self.source, "test.db", self.directory.name)
                    self.assert_generation(reader.snapshot(), "old")
                finally:
                    release.set()
                writer.result(timeout=10)
        self.assert_generation(reader.snapshot(), "new")

    def test_initialization_publishes_empty_or_complete_snapshot(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        written, release = Event(), Event()
        original = SQLiteDBHandler.insert_data
        writer_config = CryptoConfig(self.source, "first.db", self.directory.name)
        writer_config.saved_json_content = metadata("first")
        reader = CryptoConfig(self.source, "first.db", self.directory.name)

        def pause(handler, data):
            original(handler, data)
            written.set()
            if not release.wait(10):
                raise TimeoutError("Reader did not release the writer")

        with patch.object(SQLiteDBHandler, "insert_data", pause):
            with ThreadPoolExecutor(max_workers=1) as executor:
                writer = executor.submit(writer_config.to_sqlite)
                try:
                    self.assertTrue(written.wait(10))
                    self.assertEqual(reader.snapshot(), {"cryptos": [], "exchanges": [], "pairs": []})
                finally:
                    release.set()
                writer.result(timeout=10)
        self.assert_generation(reader.snapshot(), "first")

    def test_sql_failure_rolls_back_all_tables_and_preserves_cache(self):
        from quantsumore.api.market_utils import SQLiteDBHandler
        self.config.saved_json_content = metadata("new")
        with patch.object(SQLiteDBHandler, "insert_pairs", side_effect=sqlite3.OperationalError("injected failure")):
            with self.assertRaisesRegex(sqlite3.OperationalError, "injected failure"):
                self.config.to_sqlite()
        self.assert_generation(self.config.snapshot(), "old")
        self.config.to_sqlite()
        self.assert_generation(self.config.snapshot(), "new")

    def test_invalid_input_does_not_replace_committed_database(self):
        broken = metadata("new")
        del broken["crypto_exchanges"]["exchange"]["exchangeName"]
        self.config.saved_json_content = broken
        with self.assertRaises(KeyError):
            self.config.to_sqlite()
        self.assert_generation(self.config.snapshot(), "old")

    def test_competing_writers_publish_whole_generations(self):
        from quantsumore.api.market_utils import CryptoConfig
        def write(generation):
            writer = CryptoConfig(self.source, "test.db", self.directory.name)
            writer.saved_json_content = metadata(generation)
            writer.to_sqlite()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write, str(i)) for i in range(12)]
            for _ in range(12):
                snapshot = self.config.snapshot()
                self.assert_generation(snapshot, snapshot["cryptos"][0]["name"])
            for future in futures:
                future.result(timeout=15)
        final = self.config.snapshot()
        self.assert_generation(final, final["cryptos"][0]["name"])

    def test_one_snapshot_cannot_mix_tables_during_a_concurrent_write(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        start, written = Event(), Event()
        reader_ident = get_ident()
        original_connect = SQLiteDBHandler.connect
        original_pairs = SQLiteDBHandler.insert_pairs

        class Cursor:
            def __init__(self, cursor):
                self.cursor, self.sql = cursor, ""
            def execute(self, sql, *args):
                self.sql = sql
                return self.cursor.execute(sql, *args)
            def fetchall(self):
                rows = self.cursor.fetchall()
                if "FROM cryptos" in self.sql and not start.is_set():
                    start.set()
                    if not written.wait(10):
                        raise TimeoutError("Writer did not reach the final table")
                return rows

        def connect(handler):
            original_connect(handler)
            if get_ident() == reader_ident:
                handler.cursor = Cursor(handler.cursor)

        def insert_pairs(handler, data):
            original_pairs(handler, data)
            written.set()

        def write():
            if not start.wait(10):
                raise TimeoutError("Reader did not start")
            writer = CryptoConfig(self.source, "test.db", self.directory.name)
            writer.saved_json_content = metadata("new")
            writer.to_sqlite()

        with patch.object(SQLiteDBHandler, "connect", connect), patch.object(SQLiteDBHandler, "insert_pairs", insert_pairs):
            with ThreadPoolExecutor(max_workers=1) as executor:
                writer = executor.submit(write)
                self.assert_generation(self.config.snapshot(), "old")
                writer.result(timeout=10)
        self.assert_generation(self.config.snapshot(), "new")

    def test_failed_read_does_not_publish_partial_cache(self):
        from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
        writer = CryptoConfig(self.source, "test.db", self.directory.name)
        writer.saved_json_content = metadata("new")
        writer.to_sqlite()
        original_connect = SQLiteDBHandler.connect

        class Cursor:
            def __init__(self, cursor):
                self.cursor = cursor
            def execute(self, sql, *args):
                if "FROM pairs" in sql:
                    raise sqlite3.OperationalError("injected read failure")
                return self.cursor.execute(sql, *args)
            def fetchall(self):
                return self.cursor.fetchall()

        def connect(handler):
            original_connect(handler)
            handler.cursor = Cursor(handler.cursor)

        with patch.object(SQLiteDBHandler, "connect", connect):
            with self.assertRaisesRegex(sqlite3.OperationalError, "injected read failure"):
                self.config.snapshot()
        self.assert_generation(self.config._snapshot, "old")
        self.assert_generation(self.config.snapshot(), "new")

    def test_reader_is_safe_while_another_process_refreshes(self):
        program = """
from pathlib import Path
import sys, time
from tests.test_crypto_config import metadata
from quantsumore.api.market_utils import CryptoConfig, SQLiteDBHandler
directory = Path(sys.argv[1])
original = SQLiteDBHandler.insert_data
def pause(handler, data):
    original(handler, data)
    (directory / "ready").touch()
    deadline = time.monotonic() + 15
    while not (directory / "continue").exists():
        if time.monotonic() > deadline:
            raise TimeoutError("Parent did not release writer")
        time.sleep(0.01)
SQLiteDBHandler.insert_data = pause
config = CryptoConfig(directory / "metadata.json", "test.db", directory)
config.saved_json_content = metadata("child")
config.to_sqlite()
"""
        child = subprocess.Popen([sys.executable, "-W", "ignore", "-c", program, self.directory.name],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        directory = Path(self.directory.name)
        try:
            deadline = time.monotonic() + 15
            while not (directory / "ready").exists():
                if child.poll() is not None or time.monotonic() > deadline:
                    self.fail("Child did not begin its write transaction")
                time.sleep(0.01)
            self.assert_generation(self.config.snapshot(), "old")
            (directory / "continue").touch()
            stdout, stderr = child.communicate(timeout=15)
            self.assertEqual(child.returncode, 0, stdout + stderr)
            self.assert_generation(self.config.snapshot(), "child")
        finally:
            (directory / "continue").touch()
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)
