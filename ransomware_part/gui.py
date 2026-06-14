# gui.py
"""
NOVASPHERE Desktop GUI Launcher
Run this file to open the dashboard as a native desktop window.

    python gui.py

Requirements:
    pip install flask flask-cors pywebview
"""

import threading
import time
import os
import sys
import webview

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_api():
    """Start Flask API in background thread — silently."""
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    from api import app
    app.run(port=5000, debug=False, use_reloader=False)


def wait_for_api(timeout=15):
    """Block until Flask is accepting connections."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://localhost:5000/api/status", timeout=1)
            return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    print("=" * 55)
    print("  NOVASPHERE v1.5 — Starting Desktop Application")
    print("=" * 55)

    print("  Starting API server on port 5000...")
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()

    print("  Waiting for API to be ready...", end="", flush=True)
    if wait_for_api():
        print(" ready!")
    else:
        print(" timeout — opening UI anyway")

    print("  Opening dashboard window...")
    print("=" * 55)

    # Point directly to Flask — no file path issues
    window = webview.create_window(
        title="NOVASPHERE — Security That Thinks Ahead",
        url="http://localhost:5000",
        width=1200,
        height=760,
        min_size=(900, 600),
        background_color="#0a0e1a",
        text_select=False,
    )

    webview.start(debug=False)
    print("\n  NOVASPHERE closed.")


if __name__ == "__main__":
    main()
