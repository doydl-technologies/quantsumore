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



import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import sys


__all__ = ['InflationCalculatorApp']



def get_assets_dir():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, '..', 'assets')
    assets_dir = os.path.abspath(assets_dir)
    return assets_dir

assets_path = get_assets_dir()


class InflationCalculatorApp(tk.Tk):
    def __init__(self, calculator):
        if sys.platform == 'win32':
            # Keep the standalone calculator separate from Python's taskbar group.
            import ctypes
            set_app_id = ctypes.WinDLL('shell32').SetCurrentProcessExplicitAppUserModelID
            set_app_id.argtypes = [ctypes.c_wchar_p]
            set_app_id.restype = ctypes.c_long
            result = set_app_id('DOYDL.Quantsumore.InflationCalculator')
            if result < 0:
                raise OSError(result, 'Unable to set the calculator application ID')
        super().__init__()
        self.calculator = calculator
        self.withdraw()
        self.running = True
        self._resolution_after_id = None
        self._icon_handles = []
        self._icon_user32 = None
        self.previous_screen_width = None
        self.previous_screen_height = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.monitor_resolution()

    def monitor_resolution(self):
        # Screen-size queries are Tk calls too: keep them on the GUI thread.
        self._resolution_after_id = None
        if not self.running:
            return
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        if (screen_width != self.previous_screen_width or
                screen_height != self.previous_screen_height):
            self.set_window_center(screen_width, screen_height)
            self.previous_screen_width = screen_width
            self.previous_screen_height = screen_height
        self._resolution_after_id = self.after(1000, self.monitor_resolution)

    def _configure_icons(self):
        from PIL import Image, ImageTk

        titlebar_path = os.path.join(assets_path, 'quantsumore-mark-titlebar.ico')
        taskbar_path = os.path.join(assets_path, 'quantsumore-mark-taskbar.ico')
        window_system = self.tk.call('tk', 'windowingsystem')
        # Pillow decodes ICO into Tk photos; Unix iconbitmap cannot load ICO files.
        with Image.open(taskbar_path) as image:
            self._taskbar_photo = ImageTk.PhotoImage(image.convert('RGBA'), master=self)
        with Image.open(titlebar_path) as image:
            small = image.ico.getimage((16, 16)).convert('RGBA')
            self._titlebar_photo = ImageTk.PhotoImage(small, master=self)
        if window_system == 'aqua':
            # macOS has an application/Dock icon, without a standard titlebar icon.
            self.iconphoto(True, self._taskbar_photo)
        else:
            self.iconphoto(True, self._taskbar_photo, self._titlebar_photo)
        if window_system == 'win32':
            self._set_windows_icons(titlebar_path, taskbar_path)

    def _set_windows_icons(self, titlebar_path, taskbar_path):
        """Assign independent small (caption) and large (taskbar/Alt+Tab) icons."""
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
        user32.GetAncestor.restype = wintypes.HWND
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR,
                                     wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                     wintypes.UINT]
        user32.LoadImageW.restype = wintypes.HANDLE
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT,
                                       ctypes.c_size_t, ctypes.c_ssize_t]
        user32.SendMessageW.restype = ctypes.c_ssize_t
        user32.DestroyIcon.argtypes = [wintypes.HANDLE]
        user32.DestroyIcon.restype = wintypes.BOOL
        self._icon_user32 = user32
        self.update_idletasks()
        hwnd = user32.GetAncestor(self.winfo_id(), 2)  # GA_ROOT: Tk's native wrapper.
        if not hwnd:
            raise ctypes.WinError(ctypes.get_last_error())
        loaded = []
        try:
            # ICON_SMALL=0 and ICON_BIG=1; system metrics select the matching size.
            for path, width_metric, height_metric in (
                    (titlebar_path, 49, 50), (taskbar_path, 11, 12)):
                handle = user32.LoadImageW(None, path, 1,
                                          user32.GetSystemMetrics(width_metric),
                                          user32.GetSystemMetrics(height_metric),
                                          0x0010)  # IMAGE_ICON, LR_LOADFROMFILE.
                if not handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                loaded.append(handle)
        except Exception:
            for handle in loaded:
                user32.DestroyIcon(handle)
            raise
        for kind, handle in enumerate(loaded):
            user32.SendMessageW(hwnd, 0x0080, kind, handle)  # WM_SETICON.
        for handle in self._icon_handles:
            user32.DestroyIcon(handle)
        self._icon_handles = loaded

    def set_window_center(self, screen_width, screen_height):
        window_width = 600
        window_height = 500
        center_x = int((screen_width - window_width) / 2)
        center_y = int((screen_height - window_height) / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

    def initialize(self):
        from PIL import Image, ImageTk
        
        self.title("Inflation Calculator")
        self._configure_icons()

        self.geometry("600x500")
        self.minsize(600, 500)
        self.resizable(False, False)

        logo_path = os.path.join(assets_path, 'quantsumore-endorsed-lockup-dark.png')
        with Image.open(logo_path) as image:
            self.logo_image = image.copy()

        new_width = 420
        original_width, original_height = self.logo_image.size
        aspect_ratio = original_height / original_width
        new_height = int(new_width * aspect_ratio)

        self.logo_image = self.logo_image.resize((new_width, new_height), Image.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(self.logo_image, master=self)

        self.logo_label = tk.Label(self, image=self.logo_photo)
        self.logo_label.pack(pady=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, expand=True)

        self.create_adjustment_tab()
        self.create_current_year_tab()
        self.create_comparison_tab()

        self.notebook.bind("<<NotebookTabChanged>>", self.clear_other_tabs)
        self.deiconify()

    def create_adjustment_tab(self):
        self.adjustment_frame = ttk.Frame(self.notebook, width=400, height=300)
        self.adjustment_frame.pack(fill='both', expand=True)

        ttk.Label(self.adjustment_frame, text="Dollar Amount:").grid(row=0, column=0, padx=10, pady=10)
        self.amount_entry = ttk.Entry(self.adjustment_frame)
        self.amount_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.adjustment_frame, text="Original Year:").grid(row=1, column=0, padx=10, pady=10)
        self.original_year_entry = ttk.Entry(self.adjustment_frame)
        self.original_year_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.adjustment_frame, text="Target Year:").grid(row=2, column=0, padx=10, pady=10)
        self.target_year_entry = ttk.Entry(self.adjustment_frame)
        self.target_year_entry.grid(row=2, column=1, padx=10, pady=10)

        self.calculate_button = ttk.Button(self.adjustment_frame, text="Calculate", command=self.calculate_inflation)
        self.calculate_button.grid(row=3, columnspan=2, pady=10)

        self.result_label = ttk.Label(self.adjustment_frame, text="")
        self.result_label.grid(row=4, columnspan=2, pady=10)
        
        self.notebook.add(self.adjustment_frame, text='Adjusted Value')

    def create_current_year_tab(self):
        self.current_year_frame = ttk.Frame(self.notebook, width=400, height=300)
        self.current_year_frame.pack(fill='both', expand=True)

        ttk.Label(self.current_year_frame, text="Dollar Amount:").grid(row=0, column=0, padx=10, pady=10)
        self.amount_current_entry = ttk.Entry(self.current_year_frame)
        self.amount_current_entry.grid(row=0, column=1, padx=10, pady=10)

        self.current_year_button = ttk.Button(self.current_year_frame, text="Calculate", command=self.current_year_change)
        self.current_year_button.grid(row=1, columnspan=2, pady=10)

        self.current_year_result_label = ttk.Label(self.current_year_frame, text="")
        self.current_year_result_label.grid(row=2, columnspan=2, pady=10)
        
        self.notebook.add(self.current_year_frame, text='Current Year Change')

    def create_comparison_tab(self):
        self.comparison_frame = ttk.Frame(self.notebook, width=400, height=300)
        self.comparison_frame.pack(fill='both', expand=True)

        ttk.Label(self.comparison_frame, text="Dollar Amount:").grid(row=0, column=0, padx=10, pady=10)
        self.amount_comparison_entry = ttk.Entry(self.comparison_frame)
        self.amount_comparison_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.comparison_frame, text="Number of Years:").grid(row=1, column=0, padx=10, pady=10)
        self.n_years_entry = ttk.Entry(self.comparison_frame)
        self.n_years_entry.grid(row=1, column=1, padx=10, pady=10)

        self.comparison_button = ttk.Button(self.comparison_frame, text="Calculate", command=self.comparison)
        self.comparison_button.grid(row=2, columnspan=2, pady=10)

        self.comparison_result_label = ttk.Label(self.comparison_frame, text="")
        self.comparison_result_label.grid(row=3, columnspan=2, pady=10)
        
        self.notebook.add(self.comparison_frame, text='Year-by-Year Change')

    def clear_other_tabs(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        if selected_tab != 0:
            self.amount_entry.delete(0, tk.END)
            self.original_year_entry.delete(0, tk.END)
            self.target_year_entry.delete(0, tk.END)
            self.result_label.config(text="")
        if selected_tab != 1:
            self.amount_current_entry.delete(0, tk.END)
            self.current_year_result_label.config(text="")
        if selected_tab != 2:
            self.amount_comparison_entry.delete(0, tk.END)
            self.n_years_entry.delete(0, tk.END)
            self.comparison_result_label.config(text="")

    def calculate_inflation(self):
        try:
            current_month = datetime.now().strftime("%B")
            amount = float(self.amount_entry.get())
            original_year = int(self.original_year_entry.get())
            target_year = int(self.target_year_entry.get())

            adjusted_value = self.calculator.select(amount, original_year, target_year, month_input=current_month)

            if adjusted_value is not None:
                result_text = f"${amount:.2f} from {original_year} is equivalent to ${adjusted_value:.2f} in {target_year}."
                self.result_label.config(text=result_text)
            else:
                self.result_label.config(text="Calculation failed. Check the input values.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amount, original year, and target year.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def current_year_change(self):
        try:
            amount = float(self.amount_current_entry.get())

            results = self.calculator.month_by_month(amount)

            if results:
                result_text = "\n".join([f"{month}: ${value:.2f}" for month, value in results.items()])
                self.current_year_result_label.config(text=result_text)
            else:
                self.current_year_result_label.config(text="Calculation failed. Check the input values.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for amount.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def comparison(self):
        try:
            amount = float(self.amount_comparison_entry.get())
            n_years = int(self.n_years_entry.get())

            results = self.calculator.year_by_year(amount, n_years)

            if results:
                result_text = "\n".join([f"{year}: ${value:.2f}" for year, value in results.items()])
                self.comparison_result_label.config(text=result_text)
            else:
                self.comparison_result_label.config(text="Calculation failed. Check the input values.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for amount and number of years.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            
    def on_closing(self):
        self.destroy()

    def destroy(self):
        self.running = False
        if self._resolution_after_id is not None:
            self.after_cancel(self._resolution_after_id)
            self._resolution_after_id = None
        try:
            super().destroy()
        finally:
            # LoadImageW handles must remain valid until the native window is destroyed.
            for handle in self._icon_handles:
                self._icon_user32.DestroyIcon(handle)
            self._icon_handles.clear()

    def run(self):
        self.initialize()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()

    def __dir__(self):
        return ['run']


def __dir__():
    return __all__
