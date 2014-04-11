# This code was initially taken from https://github.com/mitsuhiko/werkzeug

from itertools import chain
import sys
import subprocess
import os
import os.path
import asyncio
import time
import _thread as thread

MARKER = "MAIN_FUNC_RUNNING_MARKER"

def _iter_module_files():
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename:
            old = None
            while not os.path.isfile(filename):
                old = filename
                filename = os.path.dirname(filename)
                if filename == old:
                    break
            else:
                if filename[-4:] in ('.pyc', '.pyo'):
                    filename = filename[:-1]
                yield filename

@asyncio.coroutine
def reloader_loop(extra_files=None, interval=1):
    mtimes = {}
    while 1:
        for filename in chain(_iter_module_files(), extra_files or ()):
            try:
                mtime = os.stat(filename).st_mtime
            except OSError:
                continue

            old_time = mtimes.get(filename)
            if old_time is None:
                mtimes[filename] = mtime
                continue
            elif mtime > old_time:
                loop = asyncio.get_event_loop()
                loop.stop()
                break
        yield from asyncio.sleep(interval)


def restart_with_reloader():
    while 1:
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ[MARKER] = 'true'

        exit_code = subprocess.call(args, env=new_environ)
        if exit_code != 3:
            return exit_code

def run_with_reloader(main_func, extra_files=None, interval=1):
    if os.environ.get(MARKER) == 'true':
        asyncio.async(reloader_loop(extra_files, interval))
        main_func()
    try:
        sys.exit(restart_with_reloader())
    except KeyboardInterrupt:
        print("Interrupted by user.")
