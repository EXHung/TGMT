"""Integration check for the local web adapter using the supplied demo image."""

import base64
from http import HTTPStatus
from pathlib import Path
import tempfile
import unittest

from src.ocr_engine import LOCAL_TESSERACT
from src.web_server import WebHandler


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "images" / "input" / "demo_tong_hop_vi_en.png"


@unittest.skipUnless(DEMO.is_file() and LOCAL_TESSERACT.is_file(), "Thiếu ảnh mẫu hoặc bộ OCR cục bộ")
class WebAdapterTests(unittest.TestCase):
    def test_auto_scan_then_vietnamese_english_ocr(self):
        handler = object.__new__(WebHandler)
        responses = []
        handler._json = lambda status, payload: responses.append((status, payload))
        handler._scan(DEMO, {"mode": ["color"]})
        status, scan = responses[-1]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(scan["status"], "ok")
        self.assertEqual(len(scan["corners"]), 4)
        self.assertTrue(scan["image"].startswith("data:image/png;base64,"))
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "scan.png"
            output.write_bytes(base64.b64decode(scan["image"].split(",", 1)[1]))
            handler._ocr(output, {"lang": ["vie+eng"]})
        status, ocr = responses[-1]
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(ocr["status"], "ok")
        self.assertIn("TÀI LIỆU", ocr["text"])


if __name__ == "__main__":
    unittest.main()
