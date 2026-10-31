"""Entry point of YT-Grabber.exe (packaged with PyInstaller as a windowed app: no console window).

    YT-Grabber.exe                  opens the app: its window and a tray icon, the program keeps running in the tray
    YT-Grabber.exe --background     same, but without opening the window (used when it starts with Windows)
    YT-Grabber.exe --worker         download process (started by the server, not meant to be used by hand)
    YT-Grabber.exe --choose-dir X   folder picker window (started by the server)
    YT-Grabber.exe --diag           prints where yt-dlp and the data are loaded from (run it from a terminal)

Other options (--port, --dir, --host, --no-browser) are passed to the server.
It can also be tried without packaging:  python build-windows\\exe_main.py
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'program'))
    sys.path.insert(0, HERE)


def prepare_console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def route_output_to_log():
    """A windowed program has no console: print() would fail. Everything goes to a log file instead."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    import ytcommon
    logs = os.path.join(ytcommon.DATA, 'logs')
    os.makedirs(logs, exist_ok=True)
    path = os.path.join(logs, 'app.log')
    try:
        if os.path.getsize(path) > 1024 * 1024:
            os.replace(path, path + '.old')
    except OSError:
        pass
    log = open(path, 'a', buffering=1, encoding='utf-8', errors='replace')
    if sys.stdout is None:
        sys.stdout = log
    if sys.stderr is None:
        sys.stderr = log


def attach_parent_console():
    """For --diag: when started from a terminal, write there (a windowed program has no console of its own)."""
    if sys.stdout is not None or os.name != 'nt':
        return
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open('CONOUT$', 'w', encoding='utf-8', errors='replace')
            sys.stderr = sys.stdout
    except Exception:
        pass


def import_ytdlp():
    """Imports yt-dlp; if the downloaded updated version is broken, discards it and uses the one bundled in the exe."""
    import importlib
    import ytcommon
    try:
        importlib.import_module('yt_dlp')
    except Exception as e:  # noqa: BLE001
        print('Updated yt-dlp not usable (%s): going back to the bundled version.' % e, file=sys.stderr)
        if not ytcommon.disable_ytdlp_update():
            raise
        importlib.import_module('yt_dlp')


def clean_stale_temp():
    """Closing the exe abruptly leaves the _MEI... folder with its files (~35 MB) in TEMP.
    Here the ones no longer in use are deleted: a folder is in use if its Python DLL is locked (cannot be renamed)."""
    import glob
    import shutil
    import tempfile
    if os.name != 'nt' or not getattr(sys, 'frozen', False):
        return
    mine = os.path.normcase(os.path.abspath(getattr(sys, '_MEIPASS', '')))
    for d in glob.glob(os.path.join(tempfile.gettempdir(), '_MEI*')):
        try:
            if os.path.normcase(os.path.abspath(d)) == mine or not os.path.isdir(d):
                continue
            dlls = glob.glob(os.path.join(d, 'python*.dll'))
            in_use = not dlls   # without the DLL it is not a complete folder: better not to touch it
            for dll in dlls:
                try:
                    os.rename(dll, dll + '.chk')   # on Windows a loaded DLL cannot be renamed
                    os.rename(dll + '.chk', dll)
                except OSError:
                    in_use = True
                    break
            if not in_use:
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass


def option_value(args, name, default):
    if name in args:
        i = args.index(name)
        if i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                pass
    return default


def start_server(args, start_port, report, ytcommon, setup_tools, first_start):
    """Everything that takes time at startup, run while the splash window is shown: on the very first start the
    download of ffmpeg, then the program itself. Returns (server thread, port, tools ok)."""
    import importlib
    import winapp
    tools_ok = True
    if first_start:
        original_say = setup_tools.say
        shown = {'base': ''}

        def say(msg):
            original_say(msg)
            text = msg.strip()
            if text.endswith('%') and shown['base']:
                text = '%s  %s' % (shown['base'], text)
            else:
                shown['base'] = text
            report(text)
        setup_tools.say = say
        try:
            tools_ok = setup_tools.ensure_frozen_tools()
        finally:
            setup_tools.say = original_say
    elif not os.path.exists(ytcommon.DENO):
        threading.Thread(target=setup_tools.install_deno, daemon=True, name='deno').start()   # optional, silent
    report('Starting YT Grabber...')
    importlib.reload(ytcommon)       # recompute what has just been installed
    import_ytdlp()
    import server
    sys.argv = [sys.argv[0], '--no-browser'] + [a for a in args if a != '--no-browser']
    thread = threading.Thread(target=server.main, daemon=True, name='server')
    thread.start()
    return thread, winapp.wait_for_server(start_port, thread), tools_ok


def run_app(args):
    import ytcommon
    route_output_to_log()
    prepare_console()
    background = '--background' in args
    args = [a for a in args if a != '--background']
    no_window = background or '--no-browser' in args
    start_port = option_value(args, '--port', 8765)

    if os.name != 'nt':   # not Windows: plain server, as before
        import setup_tools
        setup_tools.ensure_frozen_tools()
        import_ytdlp()
        import server
        sys.argv = [sys.argv[0]] + args
        server.main()
        return 0

    import winapp
    restarted = bool(os.environ.get('YTG_RESTARTED'))
    if restarted:
        winapp.wait_until_stopped(start_port, 30)
    profile = os.path.join(ytcommon.DATA_ROOT, 'window')

    running = winapp.find_running(start_port)
    if running:                      # already running (in the tray): just show its window
        if not no_window:
            winapp.open_window(running, profile)
        return 0

    clean_stale_temp()
    winapp.create_mutex()
    import setup_tools
    first_start = not setup_tools.ffmpeg_ok()
    icon = os.path.join(getattr(sys, '_MEIPASS', HERE), 'icon.ico')
    if first_start:
        subtitle = 'First start: downloading the tools needed for conversions.\nThis happens only once.'
        text = 'Preparing YT Grabber for the first time...'
    else:
        subtitle, text = 'Starting the program...', 'Starting YT Grabber...'
    thread, port, tools_ok = winapp.run_with_splash(
        lambda report: start_server(args, start_port, report, ytcommon, setup_tools, first_start),
        icon, subtitle, text)
    if not port:
        winapp.message_box('YT Grabber could not start. Details are in the log file in\n'
                           '%LOCALAPPDATA%\\YT-Grabber\\data\\logs\\app.log')
        return 1
    if not tools_ok:
        winapp.message_box('YT Grabber could not download ffmpeg, which it needs to convert audio and video.\n\n'
                           'Check your Internet connection. The program works, but conversions will fail until '
                           'ffmpeg is installed: quit it from the tray icon and open it again to retry.',
                           winapp.MB_ICONWARNING)
    if not no_window and not restarted:   # after an update restart the open window reloads itself
        winapp.open_window(port, profile)
    winapp.Tray(port, thread, profile).run()
    return 0


def run():
    argv = sys.argv[1:]
    if '--worker' in argv:               # download process: no output other than the protocol on stdout
        import_ytdlp()
        import ytworker
        ytworker.main()
        return 0
    if '--diag' in argv:                 # diagnostics: where yt-dlp and the data are imported from
        attach_parent_console()
        prepare_console()
        import ytcommon
        import_ytdlp()
        import yt_dlp
        print('yt-dlp version   :', yt_dlp.version.__version__)
        print('yt-dlp loaded from:', getattr(yt_dlp, '__file__', '?'))
        print('updated copy     :', ytcommon.YTDLP_UPDATE, '(present)' if os.path.isfile(ytcommon.YTDLP_UPDATE) else '(absent)')
        print('data             :', ytcommon.DATA_ROOT)
        print('meta_path        :', [type(f).__name__ for f in sys.meta_path])
        print('path_hooks       :', [getattr(h, '__name__', str(h)) for h in sys.path_hooks])
        return 0
    if '--choose-dir' in argv:
        import ytcommon
        i = argv.index('--choose-dir')
        start = argv[i + 1] if i + 1 < len(argv) else ''
        print(ytcommon.ask_directory(start))
        return 0
    return run_app(argv)


if __name__ == '__main__':
    try:
        code = run()
    except SystemExit:
        raise
    except BaseException:   # noqa: BLE001
        import traceback
        text = traceback.format_exc()
        try:
            traceback.print_exc()
        except Exception:
            pass
        if '--worker' not in sys.argv and '--choose-dir' not in sys.argv and os.name == 'nt':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, 'YT Grabber hit an error and has to close.\n\n' + text[-900:],
                                                 'YT Grabber', 0x10)
            except Exception:
                pass
        code = 1
    sys.exit(code)
