#!/usr/bin/env python3
"""表格文件合并 Web 交互页面（无第三方 Web 框架依赖）。"""

from __future__ import annotations

import cgi
import html
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List

from merge_tables import MergeError, merge_tables


PAGE_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>表格文件合并工具</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background: #f6f8fa; margin: 0; }
    .wrap { max-width: 760px; margin: 48px auto; background: #fff; border-radius: 12px; padding: 28px; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    h1 { margin-top: 0; font-size: 24px; }
    .hint { color: #57606a; margin-top: 6px; }
    .field { margin: 18px 0; }
    label { display: block; font-weight: 600; margin-bottom: 8px; }
    input[type=file], select, button { font-size: 15px; }
    select, button { padding: 8px 12px; border-radius: 8px; border: 1px solid #d0d7de; }
    button { background: #0969da; color: white; border: none; cursor: pointer; }
    button:hover { background: #0856b8; }
    .error { margin-top: 14px; color: #d1242f; font-weight: 600; white-space: pre-wrap; }
  </style>
</head>
<body>
  <main class="wrap">
    <h1>表格文件合并工具（Mac 友好）</h1>
    <p class="hint">上传多个结构相同的 CSV / XLSX / XLSM 文件，一键合并并下载。</p>

    <form method="post" action="/merge" enctype="multipart/form-data">
      <div class="field">
        <label for="files">选择输入文件（至少 2 个）</label>
        <input id="files" type="file" name="files" multiple required accept=".csv,.xlsx,.xlsm" />
      </div>

      <div class="field">
        <label for="output_format">输出格式</label>
        <select id="output_format" name="output_format">
          <option value="csv">CSV</option>
          <option value="xlsx">XLSX</option>
        </select>
      </div>

      <button type="submit">开始合并并下载</button>
    </form>

    {error_block}
  </main>
</body>
</html>
"""


class MergeHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return
        self._send_page()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/merge":
            self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self._send_page("请求格式错误：必须使用 multipart/form-data。", HTTPStatus.BAD_REQUEST)
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
            },
        )

        output_format = str(form.getvalue("output_format", "csv")).lower()
        files_field = form["files"] if "files" in form else []
        if not isinstance(files_field, list):
            files_field = [files_field] if files_field else []

        if len(files_field) < 2:
            self._send_page("请至少上传 2 个文件。", HTTPStatus.BAD_REQUEST)
            return

        if output_format not in {"csv", "xlsx"}:
            self._send_page("输出格式仅支持 csv 或 xlsx。", HTTPStatus.BAD_REQUEST)
            return

        with tempfile.TemporaryDirectory(prefix="merge-tables-") as tmpdir:
            tmp_path = Path(tmpdir)
            input_paths: List[Path] = []

            for i, item in enumerate(files_field, start=1):
                if not getattr(item, "filename", None):
                    self._send_page("上传文件缺少文件名。", HTTPStatus.BAD_REQUEST)
                    return

                original_name = Path(item.filename).name
                suffix = Path(original_name).suffix.lower()
                if suffix not in {".csv", ".xlsx", ".xlsm"}:
                    self._send_page(f"不支持的输入文件: {original_name}", HTTPStatus.BAD_REQUEST)
                    return

                if item.file is None:
                    self._send_page(f"读取文件失败: {original_name}", HTTPStatus.BAD_REQUEST)
                    return

                content = item.file.read()
                path = tmp_path / f"input_{i}{suffix}"
                path.write_bytes(content)
                input_paths.append(path)

            output_path = tmp_path / f"merged.{output_format}"
            try:
                merge_tables(input_paths, output_path)
            except MergeError as exc:
                self._send_page(str(exc), HTTPStatus.BAD_REQUEST)
                return

            data = output_path.read_bytes()
            filename = f"merged.{output_format}"
            mimetype = (
                "text/csv; charset=utf-8"
                if output_format == "csv"
                else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetype)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _send_page(self, error: str | None = None, status: HTTPStatus = HTTPStatus.OK) -> None:
        error_block = ""
        if error:
            error_block = f'<div class="error">{html.escape(error)}</div>'
        content = PAGE_HTML.format(error_block=error_block).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), MergeHandler)
    print(f"服务已启动: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
