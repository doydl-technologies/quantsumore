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

"""GUI portability and native icon regression checks without provider requests."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
import threading
import unittest
from unittest.mock import Mock, patch

from PIL import Image


SOURCE = Path(__file__).resolve().parents[1] / 'gui/cpi/calculateGUI.py'
SPEC = importlib.util.spec_from_file_location('quantsumore_gui_under_test', SOURCE)
gui = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(gui)
except ModuleNotFoundError as error:
    if error.name in ('tkinter', '_tkinter'):
        raise unittest.SkipTest('Python was built without Tkinter') from error
    raise


class PortableIconTests(unittest.TestCase):
    def configure(self, window_system):
        app = SimpleNamespace(tk=Mock(), iconphoto=Mock(),
                              _set_windows_icons=Mock(side_effect=AssertionError(
                                  'Native Windows calls on a portable Tk backend')))
        app.tk.call.return_value = window_system
        # Real Pillow decoding, without requiring an X server or macOS display.
        with patch('PIL.ImageTk.PhotoImage', side_effect=lambda image, **kw: image.copy()):
            gui.InflationCalculatorApp._configure_icons(app)
        return app

    def test_linux_offers_large_taskbar_and_small_titlebar_images(self):
        app = self.configure('x11')
        app.iconphoto.assert_called_once_with(True, app._taskbar_photo,
                                             app._titlebar_photo)
        self.assertEqual(app._titlebar_photo.size, (16, 16))
        self.assertEqual(app._taskbar_photo.size, (256, 256))
        with Image.open(Path(gui.assets_path) / 'quantsumore-mark-taskbar.ico') as image:
            self.assertEqual(app._taskbar_photo.tobytes(), image.convert('RGBA').tobytes())
        with Image.open(Path(gui.assets_path) / 'quantsumore-mark-titlebar.ico') as image:
            self.assertEqual(app._titlebar_photo.tobytes(),
                             image.ico.getimage((16, 16)).convert('RGBA').tobytes())

    def test_macos_offers_only_the_large_application_dock_icon(self):
        app = self.configure('aqua')
        app.iconphoto.assert_called_once_with(True, app._taskbar_photo)
        self.assertEqual(app._taskbar_photo.size, (256, 256))


class GuiLifecycleTests(unittest.TestCase):
    def setUp(self):
        try:
            self.app = gui.InflationCalculatorApp(Mock())
        except gui.tk.TclError as error:
            self.skipTest(f'Tk display unavailable: {error}')
        self.addCleanup(self.close_app)

    def close_app(self):
        if self.app.running:
            self.app.destroy()

    def test_startup_tabs_and_calculation(self):
        self.app.calculator.select.return_value = 125.0
        self.app.initialize()
        self.app.update()
        self.assertEqual(len(self.app.notebook.tabs()), 3)
        self.app.amount_entry.insert(0, '100')
        self.app.original_year_entry.insert(0, '2000')
        self.app.target_year_entry.insert(0, '2024')
        self.app.calculate_inflation()
        self.assertIn('$125.00', self.app.result_label.cget('text'))

    def test_resolution_poll_runs_on_main_thread_and_is_cancelled_on_close(self):
        calls = []
        original = self.app.winfo_screenwidth

        def screen_width():
            calls.append(threading.get_ident())
            return original()

        with patch.object(self.app, 'winfo_screenwidth', side_effect=screen_width):
            self.app.after(1100, self.app.quit)
            self.app.mainloop()
        self.assertEqual(calls, [threading.get_ident()])
        self.app.on_closing()
        self.assertFalse(self.app.running)
        self.assertIsNone(self.app._resolution_after_id)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native icons')
    def test_native_icons_survive_mapping_and_are_released_on_close(self):
        from ctypes import wintypes

        self.app.initialize()
        self.app.update()
        user32 = self.app._icon_user32
        hwnd = user32.GetAncestor(self.app.winfo_id(), 2)
        handles = list(self.app._icon_handles)
        self.assertEqual(len(set(handles)), 2)
        for kind, handle in enumerate(handles):
            self.assertEqual(user32.SendMessageW(hwnd, 0x007f, kind, 0), handle)
        # Verify destruction with CopyIcon: a destroyed HICON cannot be copied.
        user32.CopyIcon.argtypes = [wintypes.HANDLE]
        user32.CopyIcon.restype = wintypes.HANDLE
        for handle in handles:
            copy = user32.CopyIcon(handle)
            self.assertTrue(copy)
            user32.DestroyIcon(copy)
        self.app.on_closing()
        self.assertEqual(self.app._icon_handles, [])
        for handle in handles:
            copy = user32.CopyIcon(handle)
            if copy:
                user32.DestroyIcon(copy)
            self.assertFalse(copy)


if __name__ == '__main__':
    unittest.main()
