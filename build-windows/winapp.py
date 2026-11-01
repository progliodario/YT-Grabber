"""Windows desktop shell of the installed YT Grabber app.

What turns the program into a normal Windows app (no black console window, no browser tab to reopen):
  - single instance: starting it again just brings the existing window to the front
  - its own window: Microsoft Edge (or Chrome) in "app mode", with a private profile, so it looks like a program
  - a notification-area (tray) icon: closing the window does not stop the downloads; the icon reopens the window,
    opens the download folder and quits the program
  - a small splash window on the very first start, while ffmpeg is being downloaded

Only the standard library is used (ctypes for the Windows API, tkinter for the splash).
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from ctypes import wintypes as wt

import winlang
import ytcommon

APP_ID = 'yt-grabber'
MUTEX_NAME = 'YT-Grabber-Running'      # the installer looks for this name to know that the app is running
WINDOW_TITLE_PART = 'YT Grabber'

user32 = ctypes.WinDLL('user32', use_last_error=True)
shell32 = ctypes.WinDLL('shell32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)

WM_DESTROY, WM_CLOSE, WM_NULL, WM_USER = 0x0002, 0x0010, 0x0000, 0x0400
WM_LBUTTONUP, WM_LBUTTONDBLCLK, WM_RBUTTONUP = 0x0202, 0x0203, 0x0205
WM_TRAY = WM_USER + 1
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP, NIF_INFO = 0x1, 0x2, 0x4, 0x10
NIIF_INFO, NIN_BALLOONUSERCLICK = 0x1, 0x405
MF_STRING, MF_SEPARATOR = 0x0, 0x800
TPM_RIGHTBUTTON, TPM_RETURNCMD = 0x2, 0x100
MB_YESNO, MB_ICONQUESTION, MB_ICONERROR, MB_ICONWARNING, IDYES = 0x4, 0x20, 0x10, 0x30, 6
SW_RESTORE = 9
ID_OPEN, ID_FOLDER, ID_QUIT = 1001, 1002, 1003


class WNDCLASSW(ctypes.Structure):
    _fields_ = [('style', wt.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int), ('hInstance', wt.HINSTANCE), ('hIcon', wt.HICON),
                ('hCursor', wt.HANDLE), ('hbrBackground', wt.HBRUSH), ('lpszMenuName', wt.LPCWSTR),
                ('lpszClassName', wt.LPCWSTR)]


class GUID(ctypes.Structure):
    _fields_ = [('Data1', wt.DWORD), ('Data2', wt.WORD), ('Data3', wt.WORD), ('Data4', ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [('cbSize', wt.DWORD), ('hWnd', wt.HWND), ('uID', wt.UINT), ('uFlags', wt.UINT),
                ('uCallbackMessage', wt.UINT), ('hIcon', wt.HICON), ('szTip', wt.WCHAR * 128),
                ('dwState', wt.DWORD), ('dwStateMask', wt.DWORD), ('szInfo', wt.WCHAR * 256),
                ('uTimeout', wt.UINT), ('szInfoTitle', wt.WCHAR * 64), ('dwInfoFlags', wt.DWORD),
                ('guidItem', GUID), ('hBalloonIcon', wt.HICON)]


user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wt.ATOM
user32.CreateWindowExW.argtypes = [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU, wt.HINSTANCE, wt.LPVOID]
user32.CreateWindowExW.restype = wt.HWND
user32.GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT]
user32.GetMessageW.restype = ctypes.c_int
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wt.MSG)]
user32.TranslateMessage.argtypes = [ctypes.POINTER(wt.MSG)]
user32.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
user32.CreatePopupMenu.restype = wt.HMENU
user32.AppendMenuW.argtypes = [wt.HMENU, wt.UINT, ctypes.c_size_t, wt.LPCWSTR]
user32.TrackPopupMenu.argtypes = [wt.HMENU, wt.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, wt.LPVOID]
user32.DestroyMenu.argtypes = [wt.HMENU]
user32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.DestroyWindow.argtypes = [wt.HWND]
user32.MessageBoxW.argtypes = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT]
user32.RegisterWindowMessageW.argtypes = [wt.LPCWSTR]
user32.IsWindowVisible.argtypes = [wt.HWND]
user32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM), wt.LPARAM]
user32.PostQuitMessage.argtypes = [ctypes.c_int]
shell32.Shell_NotifyIconW.argtypes = [wt.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wt.BOOL
shell32.ExtractIconW.argtypes = [wt.HINSTANCE, wt.LPCWSTR, wt.UINT]
shell32.ExtractIconW.restype = wt.HICON
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HINSTANCE

_mutex = None


def _t(key, **values):
    """A text of the Windows shell in the language chosen in the interface."""
    return winlang.text(ytcommon.DATA, key, **values)


def message_box(text, flags=MB_ICONERROR):
    return user32.MessageBoxW(None, text, 'YT Grabber', flags)


# ------------------------------------------------------------------ talking to the local server

def _request(port, path, body=None, timeout=2.0):
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (port, path),
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={'X-YTG': '1', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode() or '{}')


def ping(port):
    try:
        return _request(port, '/api/ping', timeout=0.7).get('app') == APP_ID
    except Exception:
        return False


def find_running(start_port, span=20):
    """The port of an already running YT Grabber server, or None. All the candidate ports are tried at the same
    time: on Windows a closed port can take a good fraction of a second to answer, and one after the other that adds up."""
    from concurrent.futures import ThreadPoolExecutor
    ports = list(range(start_port, start_port + span))
    with ThreadPoolExecutor(max_workers=len(ports)) as pool:
        results = list(pool.map(ping, ports))
    for p, ok in zip(ports, results):
        if ok:
            return p
    return None


def wait_until_stopped(start_port, seconds):
    """After an update restart the previous copy is still shutting down: wait for it to free the port."""
    end = time.time() + seconds
    while time.time() < end and find_running(start_port):
        time.sleep(0.4)


def wait_for_server(start_port, thread, seconds=60):
    end = time.time() + seconds
    while time.time() < end and thread.is_alive():
        p = find_running(start_port)
        if p:
            return p
        time.sleep(0.3)
    return None


def create_mutex():
    global _mutex
    _mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)


# ------------------------------------------------------------------ the application window

def _read_default(hive, key):
    import winreg
    try:
        with winreg.OpenKey(hive, key) as k:
            return winreg.QueryValue(k, None)
    except OSError:
        return None


def find_browser():
    """Microsoft Edge (present on every Windows 10 / 11) or Google Chrome, as a path; None if neither is found."""
    import winreg
    pf = [os.environ.get('ProgramFiles(x86)'), os.environ.get('ProgramFiles'), os.environ.get('LOCALAPPDATA')]
    for exe, rel in (('msedge.exe', r'Microsoft\Edge\Application\msedge.exe'),
                     ('chrome.exe', r'Google\Chrome\Application\chrome.exe')):
        key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\%s' % exe
        paths = [_read_default(winreg.HKEY_LOCAL_MACHINE, key), _read_default(winreg.HKEY_CURRENT_USER, key)]
        paths += [os.path.join(base, rel) for base in pf if base]
        for p in paths:
            if p and os.path.isfile(p):
                return p
    return None


def _find_app_window():
    found = []
    cb_type = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            cls = ctypes.create_unicode_buffer(64)
            user32.GetClassNameW(hwnd, cls, 64)
            if WINDOW_TITLE_PART in buf.value and cls.value == 'Chrome_WidgetWin_1':
                found.append(hwnd)
        return True
    user32.EnumWindows(cb_type(cb), 0)
    return found[0] if found else None


def open_window(port, profile_dir):
    """Shows the app window: brings the existing one to the front, or opens a new one."""
    hwnd = _find_app_window()
    if hwnd:
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        return
    url = 'http://localhost:%d/' % port
    browser = find_browser()
    if not browser:
        os.startfile(url)   # no Edge or Chrome: the default browser, as a normal tab
        return
    os.makedirs(profile_dir, exist_ok=True)
    subprocess.Popen([browser, '--app=' + url, '--user-data-dir=' + profile_dir, '--window-size=1180,860',
                      '--no-first-run', '--no-default-browser-check', '--disable-features=Translate'],
                     creationflags=0x00000008 | 0x00000200, close_fds=True)   # detached: survives this process


# ------------------------------------------------------------------ tray icon

class Tray:
    """The notification-area icon and its message loop (runs in the main thread)."""

    def __init__(self, port, server_thread, profile_dir):
        self.port = port
        self.server_thread = server_thread
        self.profile_dir = profile_dir
        self.hwnd = None
        self.tip = ''
        self._wndproc = WNDPROC(self._proc)   # keep a reference: it must not be garbage collected
        self.taskbar_created = user32.RegisterWindowMessageW('TaskbarCreated')
        self.hicon = shell32.ExtractIconW(None, sys.executable, 0) or None

    # --- window and icon
    def _proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            if lparam in (WM_LBUTTONUP, WM_LBUTTONDBLCLK, NIN_BALLOONUSERCLICK):
                self.open()
            elif lparam == WM_RBUTTONUP:
                self._menu()
            return 0
        if msg == self.taskbar_created:   # Explorer restarted: the icon must be added again
            self._notify(NIM_ADD)
            return 0
        if msg == WM_DESTROY:
            self._notify(NIM_DELETE)
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _notify(self, action, tip=None):
        if tip is not None:
            self.tip = tip
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = self.hicon
        nid.szTip = (self.tip or 'YT Grabber')[:127]
        return shell32.Shell_NotifyIconW(action, ctypes.byref(nid))

    def balloon(self, title, text):
        """A notification bubble from the tray icon (clicking it opens the window)."""
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self.hwnd
        nid.uID = 1
        nid.uFlags = NIF_INFO
        nid.szInfoTitle = title[:63]
        nid.szInfo = text[:255]
        nid.dwInfoFlags = NIIF_INFO
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))

    def on_finished(self, info):
        """Called by the server when a download has finished: tells the user even if the window is closed."""
        key = 'done.err' if info.get('errors') else 'done.ok'
        self.balloon(_t('done.title'), _t(key, title=info.get('title') or 'YT Grabber', n=info.get('done', 0), e=info.get('errors', 0)))

    def _menu(self):
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, MF_STRING, ID_OPEN, _t('tray.open'))
        user32.AppendMenuW(menu, MF_STRING, ID_FOLDER, _t('tray.folder'))
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, ID_QUIT, _t('tray.quit'))
        pt = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self.hwnd)   # without this the menu does not close when clicking elsewhere
        cmd = user32.TrackPopupMenu(menu, TPM_RIGHTBUTTON | TPM_RETURNCMD, pt.x, pt.y, 0, self.hwnd, None)
        user32.PostMessageW(self.hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu)
        if cmd == ID_OPEN:
            self.open()
        elif cmd == ID_FOLDER:
            self.open_folder()
        elif cmd == ID_QUIT:
            self.quit()

    # --- actions
    def open(self):
        try:
            open_window(self.port, self.profile_dir)
        except Exception as e:  # noqa: BLE001
            print('could not open the window:', e)

    def open_folder(self):
        try:
            d = _request(self.port, '/api/state')['settings']['download_dir']
            os.makedirs(d, exist_ok=True)
            os.startfile(d)
        except Exception as e:  # noqa: BLE001
            print('could not open the folder:', e)

    def _activity(self):
        """(downloading, waiting) summed over the jobs that are running."""
        st = _request(self.port, '/api/state')
        active = waiting = 0
        for j in st.get('jobs', []):
            if j.get('status') in ('running', 'enumerating') and not j.get('paused'):
                c = j.get('counts', {})
                active += c.get('a', 0) + c.get('p', 0)
                waiting += c.get('q', 0)
        return active, waiting

    def quit(self):
        try:
            active, waiting = self._activity()
        except Exception:
            active = waiting = 0
        if active or waiting:
            if message_box(_t('quit.confirm'), MB_YESNO | MB_ICONQUESTION) != IDYES:
                return
        self._notify(NIM_DELETE)
        try:
            _request(self.port, '/api/quit', {}, timeout=5)   # saves the list, stops the workers, ends the process
        except Exception:
            pass
        user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)

    # --- background helper: tooltip with the activity, and a watch on the server thread
    def _watch(self):
        last = None
        while True:
            time.sleep(3)
            if not self.server_thread.is_alive():
                message_box(_t('stopped'))
                user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
                return
            try:
                active, waiting = self._activity()
                tip = 'YT Grabber' if not (active or waiting) else _t('tip.busy', a=active, w=waiting)
            except Exception:
                continue
            if tip != last:
                last = tip
                self._notify(NIM_MODIFY, tip)

    def run(self):
        hinst = kernel32.GetModuleHandleW(None)
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinst
        wc.lpszClassName = 'YTGrabberTray'
        user32.RegisterClassW(ctypes.byref(wc))
        self.hwnd = user32.CreateWindowExW(0, 'YTGrabberTray', 'YT Grabber', 0, 0, 0, 0, 0, None, None, hinst, None)
        if not self.hwnd:
            raise OSError('could not create the tray window')
        if not self._notify(NIM_ADD, 'YT Grabber'):
            print('warning: the tray icon could not be added')
        threading.Thread(target=self._watch, daemon=True, name='tray-watch').start()
        srv = sys.modules.get('server')
        if srv is not None and hasattr(srv, 'FINISH_HOOKS'):
            srv.FINISH_HOOKS.append(self.on_finished)   # the web page then leaves the notifications to the tray icon
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


# ------------------------------------------------------------------ first-start splash

def run_with_splash(task, icon_path=None, subtitle='Starting...', first_text='Starting...'):
    """Runs task(report) in a thread while a small window shows what is happening; returns the task's result.
    report(text) updates the text. Without tkinter the task simply runs without a window."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return task(lambda text: None)

    state = {'text': first_text, 'result': None, 'error': None}

    def work():
        try:
            state['result'] = task(lambda text: state.__setitem__('text', text))
        except BaseException as e:  # noqa: BLE001
            state['error'] = e

    root = tk.Tk()
    root.title('YT Grabber')
    root.resizable(False, False)
    root.attributes('-topmost', True)
    if icon_path and os.path.isfile(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass
    root.protocol('WM_DELETE_WINDOW', lambda: None)   # the setup cannot be interrupted halfway
    frame = ttk.Frame(root, padding=24)
    frame.pack()
    ttk.Label(frame, text='YT Grabber', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
    ttk.Label(frame, text=subtitle, justify='left').pack(anchor='w', pady=(6, 14))
    status = ttk.Label(frame, text=state['text'], width=58)
    status.pack(anchor='w')
    bar = ttk.Progressbar(frame, mode='indeterminate', length=420)
    bar.pack(pady=(10, 0))
    bar.start(12)
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    root.geometry('+%d+%d' % ((root.winfo_screenwidth() - w) // 2, (root.winfo_screenheight() - h) // 3))

    t = threading.Thread(target=work, daemon=True)
    t.start()

    def poll():
        status.config(text=state['text'])
        if t.is_alive():
            root.after(150, poll)
        else:
            root.destroy()
    root.after(150, poll)
    root.mainloop()
    if state['error']:
        raise state['error']
    return state['result']
