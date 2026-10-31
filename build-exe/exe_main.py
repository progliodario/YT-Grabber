"""Entry point of YT-Grabber.exe (packaged with PyInstaller).

    YT-Grabber.exe                  starts the server and opens the browser
    YT-Grabber.exe --worker         download process (started by the server, not meant to be used by hand)
    YT-Grabber.exe --choose-dir X   folder picker window (started by the server)

It can also be tried without packaging:  python build-exe\\exe_main.py
"""
import os
import sys

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'program'))


def prepare_console():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW('YT Grabber')
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
    """Closing the exe abruptly (e.g. the black window) leaves the _MEI... folder with its files (~35 MB) in TEMP.
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


def run():
    argv = sys.argv[1:]
    if '--worker' in argv:               # download process: no output other than the protocol on stdout
        import_ytdlp()
        import ytworker
        ytworker.main()
        return 0
    if '--diag' in argv:                 # diagnostics: where yt-dlp and the data are imported from
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

    prepare_console()
    clean_stale_temp()
    import ytcommon
    import setup_tools
    print('YT Grabber: checking the required tools...')
    setup_tools.ensure_frozen_tools()    # ffmpeg and JavaScript runtime: downloaded only the first time
    import importlib
    importlib.reload(ytcommon)           # recompute what has just been installed
    import_ytdlp()
    import server
    server.main()
    return 0


if __name__ == '__main__':
    try:
        code = run()
    except SystemExit:
        raise
    except BaseException:   # noqa: BLE001
        import traceback
        traceback.print_exc()
        if '--worker' not in sys.argv and '--choose-dir' not in sys.argv:
            print('\nAn error occurred. Press Enter to close.')
            try:
                input()
            except Exception:
                pass
        code = 1
    sys.exit(code)
