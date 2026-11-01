"""Shared set-up of the tests: the paths, a data folder of their own, and the modules of the program.

Run all the tests with:   python -m unittest discover -s tests -v
(yt-dlp must be importable: pip install "yt-dlp[default]", or run `python program/setup_tools.py` once.)
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, 'program', 'web')
sys.path.insert(0, os.path.join(ROOT, 'program'))
os.environ['YTG_DATA_ROOT'] = tempfile.mkdtemp(prefix='ytg_test_')   # keep the tests away from the real data folder
# when yt-dlp is installed in the project's own vendor folder (setup_tools.py), use it
VENDOR = os.path.join(ROOT, 'generated', 'vendor')
if os.path.isdir(VENDOR):
    sys.path.insert(0, VENDOR)

import server  # noqa: E402
import ytsettings as settings  # noqa: E402,F401
import ytupdates as updates  # noqa: E402,F401
import ytcommon  # noqa: E402,F401

__all__ = ["ROOT", "WEB", "server", "settings", "updates", "ytcommon"]

server.log = lambda *args, **kwargs: None   # the server's progress messages are noise in the test output
updates.hooks.log = server.log
