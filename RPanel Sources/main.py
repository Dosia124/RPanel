# main.py — точка входа: порт, браузер, сервер
import os
import atexit
import socket
import sys
import threading
import time
import webbrowser

# фикс для --windowed: без консоли потоки вывода = None
if sys.stdout is None: sys.stdout = open(os.devnull, "w")
if sys.stderr is None: sys.stderr = open(os.devnull, "w")

import core
from api import app


def find_port():
    for port in range(7777, 7790):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 7777


def main():
    core.start_background()
    atexit.register(core.purge_media_cache)
    port = find_port()
    url = "http://127.0.0.1:%d" % port
    if sys.stdout:
        print("")
        print("  RPanel  ->  %s" % url)
        print("  Keep this window open. Stop: Ctrl+C or the power button in the app.")
        print("")
    threading.Thread(target=lambda: (time.sleep(0.9), webbrowser.open(url)),
                     daemon=True).start()
    app.run(host="127.0.0.1", port=port, debug=False,
            use_reloader=False, threaded=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass