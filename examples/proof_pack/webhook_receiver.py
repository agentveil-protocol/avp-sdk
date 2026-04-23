"""
Local AVP webhook receiver for the Proof Pack demo.

Accepts POSTs from the AVP alert dispatcher (app/core/alerts/dispatcher.py)
and writes the exact payload to `artifacts/07_webhook_alert.json`.

    python webhook_receiver.py
    python webhook_receiver.py --port 8765 --out artifacts/07_webhook_alert.json

Transport is real HTTP. Semantics (payload shape, triggering, timing) are
produced by the real AVP dispatcher — this file is only a sink.

Ctrl-C to stop.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class _Handler(BaseHTTPRequestHandler):
    out_path: str = "artifacts/07_webhook_alert.json"
    received: list[dict[str, Any]] = []

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter default logging
        sys.stderr.write("[receiver] " + (fmt % args) + "\n")

    def do_POST(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler convention
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw.decode()) if raw else {}
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        envelope = {
            "path": self.path,
            "headers": {k: v for k, v in self.headers.items()},
            "payload": payload,
        }
        _Handler.received.append(envelope)
        os.makedirs(os.path.dirname(_Handler.out_path) or ".", exist_ok=True)
        with open(_Handler.out_path, "w") as f:
            json.dump(envelope, f, indent=2)
        sys.stderr.write(f"[receiver] wrote {_Handler.out_path}\n")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_GET(self) -> None:  # noqa: N802 — used only for health probe
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()


def main() -> int:
    ap = argparse.ArgumentParser(description="Local webhook sink for the AVP Proof Pack demo.")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--out", default="artifacts/07_webhook_alert.json")
    args = ap.parse_args()

    _Handler.out_path = args.out
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    sys.stderr.write(f"[receiver] listening on http://{args.host}:{args.port}/hook\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[receiver] shutting down\n")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
