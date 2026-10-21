"""Synthetic smoke checks; real photo evaluation belongs in docs/testing.md."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.image_io import load_image, save_image
from src.pipeline import scan_document
from src.perspective import validate_corners
from src.enhancement import enhance
from src.document_detector import _bright_page_fallback


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.image = np.full((700, 900, 3), (35, 55, 75), dtype=np.uint8)
        self.page = np.array([[160, 90], [750, 130], [700, 620], [120, 590]], dtype=np.int32)
        cv2.fillConvexPoly(self.image, self.page, (245, 245, 245))
        cv2.polylines(self.image, [self.page], True, (10, 10, 10), 8)
        for y in range(190, 520, 50):
            cv2.line(self.image, (220, y), (620, y + 5), (20, 20, 20), 4)

    def test_auto_scan(self):
        result = scan_document(self.image, mode="gray")
        self.assertEqual(result.status, "ok", result.message)
        self.assertEqual(result.enhanced.ndim, 2)
        self.assertGreater(result.scanned.shape[0], 300)
        self.assertGreater(result.scanned.shape[1], 400)

    def test_manual_unordered_corners(self):
        result = scan_document(self.image, manual_corners=self.page[[2, 0, 3, 1]], mode="bw")
        self.assertEqual(result.status, "ok", result.message)
        self.assertEqual(result.method, "manual")
        self.assertEqual(set(np.unique(result.enhanced)), {0, 255})

    def test_invalid_corners(self):
        with self.assertRaises(ValueError):
            validate_corners([[1, 1]] * 4, self.image.shape)

    def test_blank_rejected(self):
        blank = np.full_like(self.image, 220)
        self.assertEqual(scan_document(blank).status, "manual_required")

    def test_unicode_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "Tài liệu tiếng Việt.png"
            save_image(path, self.image)
            self.assertTrue(np.array_equal(load_image(path), self.image))

    def test_file_size_rejected_before_decode(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "large.png"
            path.write_bytes(b"not an image")
            with patch("src.image_io.MAX_FILE_BYTES", 5):
                with self.assertRaisesRegex(ValueError, "quá lớn"):
                    load_image(path)

    def test_save_failure_preserves_existing_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "existing.png"
            path.write_bytes(b"previous contents")
            with patch("src.image_io.os.replace", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    save_image(path, self.image)
            self.assertEqual(path.read_bytes(), b"previous contents")
            self.assertFalse(list(Path(folder).glob(".scan-*")))

    def test_black_white_removes_broad_shadow(self):
        page = np.full((600, 500, 3), 225, dtype=np.uint8)
        cv2.rectangle(page, (130, 250), (430, 590), (95, 95, 95), -1)
        cv2.putText(page, "TEXT", (150, 420), cv2.FONT_HERSHEY_SIMPLEX,
                    2.0, (15, 15, 15), 5)
        binary = enhance(page, "bw")
        shadow_without_letters = binary[275:325, 160:390]
        letters = binary[380:430, 160:390]
        self.assertGreater(np.mean(shadow_without_letters == 255), 0.90)
        self.assertGreater(np.mean(letters == 0), 0.03)

    def test_bright_page_fallback_rejects_blank_and_accepts_page(self):
        blank = np.full((700, 900, 3), 220, dtype=np.uint8)
        self.assertIsNone(_bright_page_fallback(blank))
        page = blank.copy()
        for y in range(100, 600, 30):
            cv2.line(page, (100, y), (800, y), (30, 30, 30), 2)
        self.assertIsNotNone(_bright_page_fallback(page))

    def test_classroom_photos_with_missing_corners(self):
        """The supplied board and projected slide must scan without hand-picked points."""
        folder = Path(__file__).resolve().parents[1] / "images" / "input"
        cases = (
            ("1790394342374_*e058eb06be4d39a4b7f99d381a4a7d61.jpg",
             "visible_projection_estimate", (0.0, 0.10, 0.95, 0.70)),
            ("1790394342521_*2643842dea5c0d2429f96dd4a520144f.jpg",
             "visible_blackboard_estimate", (0.0, 0.30, 0.80, 0.95)),
        )
        if not all(list(folder.glob(pattern)) for pattern, _, _ in cases):
            self.skipTest("Cần ảnh lớp học do người dùng cung cấp")
        for pattern, method, (min_x, min_y, max_x, max_y) in cases:
            with self.subTest(pattern=pattern):
                result = scan_document(next(folder.glob(pattern)))
                self.assertEqual(result.status, "ok", result.message)
                self.assertEqual(result.method, method)
                height, width = result.original.shape[:2]
                self.assertLessEqual(result.corners[:, 0].min() / width, min_x + .05)
                self.assertLessEqual(result.corners[:, 1].min() / height, min_y + .05)
                self.assertGreaterEqual(result.corners[:, 0].max() / width, max_x)
                self.assertGreaterEqual(result.corners[:, 1].max() / height, max_y)
                self.assertGreater(result.scanned.size, 0)


if __name__ == "__main__":
    unittest.main()
