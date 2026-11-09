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
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

from tests.runtime import prepare_runtime


class InstallationTests(unittest.TestCase):
    def test_installed_metadata_and_bundled_resources(self):
        import importlib.metadata as metadata
        from importlib.resources import files
        import quantsumore
        self.assertEqual(metadata.version('quantsumore'), '3.0.0b4')
        self.assertEqual(quantsumore.__version__, metadata.version('quantsumore'))
        self.assertIn('site-packages', Path(quantsumore.__file__).parts)
        for name in ('files/stock_tickers.txt', 'files/crypto/all_data.json'):
            self.assertTrue(files('quantsumore').joinpath(name).is_file(), name)
        requirements = metadata.requires('quantsumore')
        self.assertTrue(any(value.lower().startswith('pandas') for value in requirements))
        self.assertTrue(all('extra ==' in value for value in requirements if 'ta-lib' in value.lower()))

    def test_cold_import_from_external_directory_without_network(self):
        program = '''
import json
from pathlib import Path
from unittest.mock import patch
import requests
with patch.object(requests.sessions.Session, "request", side_effect=AssertionError("Network during import")):
    import quantsumore
    from quantsumore.api import equity, forex, crypto, treasury, cpi
    from quantsumore.analysis import tAnalysis, fAnalysis
    assert (quantsumore.APP_DATA_DIR / "stock_tickers.txt").is_file()
    assert (quantsumore.APP_DATA_DIR / "all_data.json").is_file()
    print(json.dumps({"version": quantsumore.__version__, "installed": "site-packages" in Path(quantsumore.__file__).parts}))
'''
        with TemporaryDirectory(prefix='quantsumore-cold-import-') as directory:
            env = {**os.environ, 'LOCALAPPDATA': directory, 'XDG_DATA_HOME': directory, 'MPLBACKEND': 'Agg'}
            result = subprocess.run([sys.executable, '-I', '-c', program], cwd=directory,
                                    env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report, {'version': '3.0.0b4', 'installed': True})

    def test_concurrent_cold_imports_never_read_partial_reference_files(self):
        program = '''
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
from unittest.mock import patch
import requests

control = Path(sys.argv[1])
original_copy = shutil.copyfile

def paused_copy(source, destination, *args, **kwargs):
    if Path(source).name != "all_data.json":
        return original_copy(source, destination, *args, **kwargs)
    with open(source, "rb") as incoming, open(destination, "wb") as outgoing:
        outgoing.write(incoming.read(1))
        outgoing.flush()
        (control / "ready").write_text("ready")
        deadline = time.monotonic() + 45
        while not (control / "release").exists():
            if time.monotonic() > deadline:
                raise TimeoutError("Concurrent importer did not release the copy")
            time.sleep(0.01)
        outgoing.write(incoming.read())
    return destination

if sys.argv[2] == "paused":
    shutil.copyfile = paused_copy
with patch.object(requests.sessions.Session, "request", side_effect=AssertionError("Network during import")):
    import quantsumore
    from quantsumore.api.market_utils import config
    from importlib.resources import files
    for local, bundled in (("all_data.json", "files/crypto/all_data.json"),
                           ("stock_tickers.txt", "files/stock_tickers.txt")):
        data = (quantsumore.APP_DATA_DIR / local).read_bytes()
        assert data == files("quantsumore").joinpath(bundled).read_bytes()
    snapshot = config.snapshot()
    assert all(snapshot.values())
    print(json.dumps({"sha256": hashlib.sha256(data).hexdigest(),
                      "collections": {key: len(rows) for key, rows in snapshot.items()}}))
'''
        with TemporaryDirectory(prefix="quantsumore-concurrent-import-") as directory:
            control = Path(directory)
            env = {**os.environ, "LOCALAPPDATA": directory, "XDG_DATA_HOME": directory,
                   "MPLBACKEND": "Agg"}
            first = subprocess.Popen([sys.executable, "-I", "-c", program, directory, "paused"],
                                     cwd=directory, env=env, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 30
                while not (control / "ready").exists():
                    if first.poll() is not None or time.monotonic() > deadline:
                        self.fail("First importer did not reach the paused copy")
                    time.sleep(0.01)
                second = subprocess.run([sys.executable, "-I", "-c", program, directory, "normal"],
                                        cwd=directory, env=env, capture_output=True, text=True, timeout=40)
            finally:
                (control / "release").write_text("release")
                try:
                    stdout, stderr = first.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    first.kill()
                    stdout, stderr = first.communicate()
                    self.fail("First importer did not finish after release: " + stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout), json.loads(second.stdout))
            self.assertEqual(list(control.rglob("*.tmp")), [])


class ReferenceSeedingTests(unittest.TestCase):
    def test_existing_reference_file_is_preserved(self):
        from quantsumore.api.market_utils import _seed_reference_file
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "bundled", root / "local"
            source.write_bytes(b"bundled")
            destination.write_bytes(b"user data")
            _seed_reference_file(destination, source)
            self.assertEqual(destination.read_bytes(), b"user data")
            self.assertEqual({p.name for p in root.iterdir()}, {"bundled", "local"})

    def test_failed_copy_leaves_no_destination_or_temporary_file(self):
        from quantsumore.api import market_utils
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "bundled", root / "local"
            source.write_bytes(b"complete snapshot")

            def fail_copy(source, temporary):
                Path(temporary).write_bytes(b"partial")
                raise OSError("injected copy failure")

            with patch.object(market_utils, "copyfile", side_effect=fail_copy):
                with self.assertRaisesRegex(OSError, "injected copy failure"):
                    market_utils._seed_reference_file(destination, source)
            self.assertFalse(destination.exists())
            self.assertEqual(list(root.iterdir()), [source])
            market_utils._seed_reference_file(destination, source)
            self.assertEqual(destination.read_bytes(), source.read_bytes())

    def test_file_created_during_publication_is_not_overwritten(self):
        from quantsumore.api import market_utils
        operation = "rename" if os.name == "nt" else "link"
        publish = getattr(os, operation)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, destination = root / "bundled", root / "local"
            source.write_bytes(b"bundled")

            def create_before_publish(temporary, target):
                target.write_bytes(b"user data")
                publish(temporary, target)

            with patch.object(market_utils.os, operation, side_effect=create_before_publish):
                market_utils._seed_reference_file(destination, source)
            self.assertEqual(destination.read_bytes(), b"user data")
            self.assertEqual({p.name for p in root.iterdir()}, {"bundled", "local"})
