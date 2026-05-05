from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .api import ApiApp
from .db import apply_migrations, connect, seed_minimal_reference_data
from .service import ClaimService


class HcfsaHandler(BaseHTTPRequestHandler):
    app: ApiApp

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        self._handle()

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        self._handle()

    def _handle(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else None
        response = self.app.handle(self.command, self.path, dict(self.headers), body)
        encoded = json.dumps(response.body).encode("utf-8")
        self.send_response(response.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run(host: str = "127.0.0.1", port: int = 8000, database_url: str = "hcfsa.sqlite3") -> None:
    conn = connect(database_url)
    apply_migrations(conn)
    seed_minimal_reference_data(conn)
    HcfsaHandler.app = ApiApp(ClaimService(conn))
    HTTPServer((host, port), HcfsaHandler).serve_forever()


if __name__ == "__main__":
    run()
