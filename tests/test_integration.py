"""Independent integration checks for the document scanner.

Run from the project root: python -m unittest discover -s tests -v
"""

import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np


class ScannerIntegrationTests(unittest.TestCase):
    @staticmethod
    def sample_image():
        image = np.full((480, 640, 3), (35, 55, 70), dtype=np.uint8)
        cv2.rectangle(image, (80, 60), (560, 420), (245, 245, 245), -1)
        cv2.putText(image, "TEST 123", (150, 220), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (20, 20, 20), 3)
        return image

    def test_package_entry_point_imports(self):
        """The documented module invocation must load from the project root."""
        importlib.import_module("src.main")

    def test_manual_scan_and_unicode_path_round_trip(self):
        from src.image_io import load_image, save_image
        from src.pipeline import scan_document

        corners = [(80, 60), (560, 60), (560, 420), (80, 420)]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "Tài liệu tiếng Việt 01.png"
            output = Path(temporary) / "Kết quả quét.png"
            save_image(source, self.sample_image())
            result = scan_document(source, manual_corners=corners, mode="gray")
            self.assertEqual(result.status, "ok", result.message)
            self.assertEqual(result.enhanced.ndim, 2)
            save_image(output, result.enhanced)
            self.assertEqual(load_image(output).shape[:2], result.enhanced.shape[:2])

    def test_invalid_corners_do_not_produce_scan(self):
        from src.pipeline import scan_document

        image = self.sample_image()
        for corners in (
            [(80, 60)] * 4,
            [(-1, 60), (560, 60), (560, 420), (80, 420)],
            [(80, 60), (81, 60), (81, 61), (80, 61)],
        ):
            with self.subTest(corners=corners):
                result = scan_document(image, manual_corners=corners)
                self.assertNotEqual(result.status, "ok")
                self.assertIsNone(result.enhanced)

    def test_blank_image_requires_manual_selection(self):
        from src.pipeline import scan_document

        blank = np.full((480, 640, 3), 128, dtype=np.uint8)
        result = scan_document(blank)
        self.assertEqual(result.status, "manual_required", result.message)
        self.assertIsNone(result.enhanced)

    def test_failed_save_does_not_claim_success(self):
        from src.image_io import save_image

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "folder.png"
            directory.mkdir()
            with self.assertRaises((OSError, ValueError)):
                save_image(directory, self.sample_image())

    def test_selecting_new_corners_invalidates_old_results(self):
        """Starting a new crop must not leave old scan/OCR eligible for save."""
        from src.gui import ScannerApp

        class FakePanel:
            def set_points(self, _points):
                pass

            def set_image(self, _image):
                pass

        class FakeStatus:
            def set(self, _message):
                pass

        app = SimpleNamespace(
            original=self.sample_image(),
            scanned=self.sample_image(),
            enhanced=self.sample_image(),
            manual_points=[(80, 60), (560, 60), (560, 420), (80, 420)],
            selecting_points=False,
            image_revision=3,
            ocr_revision=3,
            original_panel=FakePanel(),
            output_panel=FakePanel(),
            status_var=FakeStatus(),
            _clear_text=lambda: None,
            _refresh_controls=lambda: None,
        )
        ScannerApp._start_manual(app)
        self.assertTrue(app.selecting_points)
        self.assertEqual(app.manual_points, [])
        self.assertIsNone(app.enhanced)
        self.assertNotEqual(app.ocr_revision, app.image_revision)


if __name__ == "__main__":
    unittest.main()
