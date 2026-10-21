"""Kiểm tra adapter OCR bằng engine giả; không thay cho đánh giá OCR thật."""

from pathlib import Path
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

import numpy as np

from src.ocr_engine import recognize_text, save_text


class OCREngineTests(unittest.TestCase):
    def test_invalid_input(self):
        result = recognize_text(np.empty((0, 0), dtype=np.uint8))
        self.assertEqual(result.status, "invalid_input")

    def test_missing_language_does_not_crash(self):
        fake = ModuleType("pytesseract")
        fake.pytesseract = fake
        fake.TesseractNotFoundError = type("TesseractNotFoundError", (Exception,), {})
        fake.TesseractError = type("TesseractError", (Exception,), {})
        with patch.dict("sys.modules", {"pytesseract": fake}), \
             patch("src.ocr_engine._resolve_executable", return_value="tesseract"), \
             patch("src.ocr_engine._installed_languages", return_value={"eng"}):
            result = recognize_text(np.full((20, 30, 3), 255, dtype=np.uint8), "vie+eng")
        self.assertEqual(result.status, "unavailable")
        self.assertIn("vie", result.message)

    def test_unicode_text_round_trip(self):
        sample = "Tài liệu tiếng Việt — kiểm thử.\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "văn bản.txt"
            save_text(path, sample)
            self.assertEqual(path.read_text(encoding="utf-8"), sample)


if __name__ == "__main__":
    unittest.main()
