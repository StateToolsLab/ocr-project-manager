#!/usr/bin/env python3
"""OCR Project Manager v2 - 拡張版起動スクリプト"""

import os
os.environ["PDF_ENABLED"] = "true"

from app import app
import app_extensions

if __name__ == "__main__":
    import threading, webbrowser
    print("OCR Project Manager v2 起動中...")
    print("拡張機能: PDF変換 有効")
    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5050")).start()
    app.run(host="127.0.0.1", port=5050, debug=False)
