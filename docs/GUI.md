# Inflation calculator GUI

Run the GUI on the main Python thread with a working Tk display and Pillow installed.
Tkinter is supplied by the Python distribution or operating system, rather than pip.
`python -m tkinter` opens a test window to check that Tk is available.

## Icons

- Windows: `gui/assets/quantsumore-mark-titlebar.ico` supplies the small caption
  icon; `gui/assets/quantsumore-mark-taskbar.ico` supplies the large taskbar and
  Alt+Tab icon. Native icon sizes follow Windows system metrics. A dedicated
  application ID keeps the calculator separate from Python's taskbar group.
  Pinned shortcuts can still supply their own icons.
- macOS: the taskbar artwork supplies Tk's application/Dock icon. Standard macOS
  windows do not have the Windows-style titlebar icon. The available artwork is
  256 pixels square; Tk recommends larger artwork for high-resolution Dock use.
- Linux: Pillow decodes the ICO assets into Tk images. The large taskbar artwork
  and small titlebar artwork are offered through `iconphoto`; the window manager
  chooses which image to display. Independent placement is not guaranteed.

`gui/assets/quantsumore-endorsed-lockup-dark.png` is the logo inside the calculator window.
Both new ICO files are included by the existing packaging wildcard rules.
Screen-size polling uses Tk's event loop, and closing cancels the pending poll
and releases native Windows icon handles.

References: [Tk icon handling](https://www.tcl-lang.org/man/tcl8.6/TkCmd/wm.htm#M49),
[Windows window icons](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-seticon),
[Windows application identity](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-setcurrentprocessexplicitappusermodelid).
