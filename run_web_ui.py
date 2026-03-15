#!/usr/bin/env python3
"""启动本地 Web UI，并自动打开浏览器。"""

from __future__ import annotations

import webbrowser

from merge_tables_web import run


if __name__ == "__main__":
    url = "http://127.0.0.1:8000"
    webbrowser.open(url)
    run(host="127.0.0.1", port=8000)
