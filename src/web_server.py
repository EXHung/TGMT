"""Local web interface for the existing document scanner and OCR pipeline."""

from __future__ import annotations

import argparse
import base64
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
from threading import BoundedSemaphore
from urllib.parse import parse_qs, urlsplit
import webbrowser

import cv2

from .image_io import load_image
from .ocr_engine import recognize_text
from .pipeline import scan_document


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MAX_UPLOAD_BYTES = 25_000_000
_WORKERS = BoundedSemaphore(2)
_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}
_SUFFIX = {"image/jpeg": ".jpg", "image/png": ".png"}


class WebHandler(BaseHTTPRequestHandler):
    server_version = "TGMT-Web/1.0"

    def log_message(self, format: str, *args: object) -> None:
        print("[web] " + format % args)

    def _headers(self, status: HTTPStatus, mime: str, size: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'")
        self.end_headers()

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._headers(status, "application/json; charset=utf-8", len(data))
        self.wfile.write(data)

    def _allowed_host(self) -> bool:
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        return host in {"127.0.0.1", "localhost"}

    def _allowed_origin(self) -> bool:
        origin = self.headers.get("Origin", "")
        if not origin:
            return True
        target = urlsplit(origin)
        return target.scheme == "http" and target.hostname in {"127.0.0.1", "localhost"} and target.port == self.server.server_port

    def do_GET(self) -> None:
        if not self._allowed_host():
            self._json(HTTPStatus.FORBIDDEN, {"message": "Địa chỉ truy cập không hợp lệ."})
            return
        path = urlsplit(self.path).path
        if path == "/api/health":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return
        item = _FILES.get(path)
        if item is None:
            self._json(HTTPStatus.NOT_FOUND, {"message": "Không tìm thấy trang."})
            return
        name, mime = item
        data = (WEB / name).read_bytes()
        self._headers(HTTPStatus.OK, mime, len(data))
        self.wfile.write(data)

    def do_POST(self) -> None:
        if not self._allowed_host() or not self._allowed_origin():
            self._json(HTTPStatus.FORBIDDEN, {"message": "Yêu cầu không hợp lệ."})
            return
        url = urlsplit(self.path)
        if url.path not in {"/api/scan", "/api/ocr"}:
            self._json(HTTPStatus.NOT_FOUND, {"message": "Không tìm thấy chức năng."})
            return
        mime = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if mime not in _SUFFIX:
            self._json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"message": "Chỉ nhận ảnh JPG hoặc PNG."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        if size <= 0 or size > MAX_UPLOAD_BYTES:
            self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"message": "Ảnh phải nhỏ hơn 25 MB."})
            return
        if not _WORKERS.acquire(blocking=False):
            self._json(HTTPStatus.TOO_MANY_REQUESTS, {"message": "Máy đang xử lý ảnh khác. Hãy thử lại sau."})
            return
        try:
            body = self.rfile.read(size)
            if len(body) != size:
                self._json(HTTPStatus.BAD_REQUEST, {"message": "Ảnh tải lên chưa đầy đủ."})
                return
            with tempfile.TemporaryDirectory(prefix="tgmt-web-") as folder:
                source = Path(folder) / ("input" + _SUFFIX[mime])
                source.write_bytes(body)
                if url.path == "/api/scan":
                    self._scan(source, parse_qs(url.query))
                else:
                    self._ocr(source, parse_qs(url.query))
        except (OSError, ValueError, cv2.error) as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"message": str(exc) or "Không đọc được ảnh."})
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"message": "Xử lý chưa hoàn tất. Hãy thử lại."})
        finally:
            _WORKERS.release()

    def _scan(self, source: Path, query: dict[str, list[str]]) -> None:
        mode = query.get("mode", ["color"])[0]
        if mode not in {"color", "gray", "bw"}:
            self._json(HTTPStatus.BAD_REQUEST, {"message": "Chế độ ảnh không hợp lệ."})
            return
        corners = None
        if "corners" in query:
            try:
                corners = json.loads(query["corners"][0])
            except (ValueError, IndexError):
                self._json(HTTPStatus.BAD_REQUEST, {"message": "Bốn góc chưa hợp lệ."})
                return
        result = scan_document(source, manual_corners=corners, mode=mode)
        if result.status != "ok" or result.enhanced is None:
            status = HTTPStatus.UNPROCESSABLE_ENTITY if result.status == "manual_required" else HTTPStatus.BAD_REQUEST
            self._json(status, {"status": result.status, "message": result.message})
            return
        ok, encoded = cv2.imencode(".png", result.enhanced)
        if not ok:
            raise ValueError("Không tạo được ảnh quét.")
        original_height, original_width = result.original.shape[:2]
        self._json(HTTPStatus.OK, {
            "status": "ok", "message": result.message, "method": result.method,
            "score": round(float(result.score), 3),
            "width": original_width, "height": original_height,
            "corners": result.corners.tolist() if result.corners is not None else None,
            "image": "data:image/png;base64," + base64.b64encode(encoded).decode("ascii"),
        })

    def _ocr(self, source: Path, query: dict[str, list[str]]) -> None:
        language = query.get("lang", ["vie+eng"])[0]
        if language not in {"vie", "eng", "vie+eng"}:
            self._json(HTTPStatus.BAD_REQUEST, {"message": "Ngôn ngữ nhận dạng không hợp lệ."})
            return
        result = recognize_text(load_image(source), language)
        self._json(HTTPStatus.OK if result.status in {"ok", "empty"} else HTTPStatus.UNPROCESSABLE_ENTITY,
                   {"status": result.status, "message": result.message,
                    "text": result.text, "elapsed_seconds": round(result.elapsed_seconds, 2)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy giao diện web quét tài liệu trên máy này")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Cổng cần nằm trong khoảng 1024–65535")
    url = f"http://127.0.0.1:{args.port}/"
    with ThreadingHTTPServer(("127.0.0.1", args.port), WebHandler) as server:
        print(f"TGMT Scan Studio Web: {url}", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=0.2)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
