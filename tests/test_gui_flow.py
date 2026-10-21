"""Kiểm tra luồng giao diện và tác vụ nền bằng ảnh tổng hợp."""

import gc
import time
import tkinter as tk
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import cv2
import numpy as np

from src.gui import ScannerApp, short_filename, scan_document
from src.image_io import load_image


class GUIFlowTests(unittest.TestCase):
    def test_auto_scan_displays_detected_corners(self):
        try:
            app = ScannerApp()
        except tk.TclError as exc:
            self.skipTest(f"Máy không có màn hình Tk: {exc}")
        try:
            app.root.withdraw()
            image = np.full((480, 640, 3), (35, 55, 70), dtype=np.uint8)
            cv2.rectangle(image, (80, 60), (560, 420), (245, 245, 245), -1)
            app.original = image
            app.original_panel.set_image(image)
            # Previous manual points must not override a fresh automatic scan.
            app.manual_points = [(90, 70), (550, 70), (550, 410), (90, 410)]
            app.selecting_points = False
            with patch("src.gui.scan_document", wraps=scan_document) as scanner:
                app._scan()
                deadline = time.monotonic() + 5
                while app.busy and time.monotonic() < deadline:
                    app.root.update()
                    time.sleep(0.02)
                self.assertFalse(app.busy)
                self.assertIsNone(scanner.call_args.kwargs["manual_corners"])
            self.assertIsNotNone(app.enhanced)
            self.assertEqual(len(app.original_panel.points), 4)
            self.assertIn("tự động", app.status_var.get())
        finally:
            app._close()
            del app
            gc.collect()

    def test_failed_auto_scan_does_not_force_manual_mode(self):
        try:
            app = ScannerApp()
        except tk.TclError as exc:
            self.skipTest(f"Máy không có màn hình Tk: {exc}")
        try:
            image = np.full((480, 640, 3), 220, dtype=np.uint8)
            app.root.withdraw()
            app.original = image
            app.original_panel.set_image(image)
            app._scan()
            deadline = time.monotonic() + 5
            while app.busy and time.monotonic() < deadline:
                app.root.update()
                time.sleep(0.02)
            self.assertFalse(app.busy)
            self.assertFalse(app.selecting_points)
            self.assertEqual(app.manual_points, [])
            self.assertEqual(str(app.scan_button["state"]), "normal")
            self.assertIn("Tự căn", app.scan_button["text"])
        finally:
            app._close()
            del app
            gc.collect()

    def test_long_filename_and_background_save(self):
        name = "1790394342321_4233877387456589939_4233877387456589939_843e2a8e9c01e9ac010fbb72be81310a.jpg"
        shortened = short_filename(name)
        self.assertLessEqual(len(shortened), 54)
        self.assertTrue(shortened.endswith(".jpg"))
        self.assertIn("…", shortened)
        try:
            app = ScannerApp()
        except tk.TclError as exc:
            self.skipTest(f"Máy không có màn hình Tk: {exc}")
        try:
            app.root.withdraw()
            app.image_path = Path(name)
            app.enhanced = np.full((100, 150, 3), 205, dtype=np.uint8)
            app._refresh_controls()
            with TemporaryDirectory() as folder:
                target = Path(folder) / "ảnh quét.png"
                with patch("src.gui.filedialog.asksaveasfilename", return_value=str(target)):
                    app._save_image()
                self.assertTrue(app.busy)
                deadline = time.monotonic() + 5
                while app.busy and time.monotonic() < deadline:
                    app.root.update()
                    time.sleep(0.02)
                self.assertFalse(app.busy)
                self.assertEqual(load_image(target).shape, app.enhanced.shape)
                self.assertIn("Đã lưu ảnh quét", app.status_var.get())
        finally:
            app._close()
            del app
            gc.collect()

    def test_scan_then_change_mode_and_invalidate_ocr(self):
        try:
            app = ScannerApp()
        except tk.TclError as exc:
            self.skipTest(f"Máy không có màn hình Tk: {exc}")
        try:
            app.root.withdraw()
            image = np.full((480, 640, 3), (35, 55, 70), dtype=np.uint8)
            cv2.rectangle(image, (80, 60), (560, 420), (245, 245, 245), -1)
            app.original = image
            app.original_panel.set_image(image)
            app.manual_points = [(80, 60), (560, 60), (560, 420), (80, 420)]
            app.selecting_points = True
            app._scan()
            deadline = time.monotonic() + 5
            while app.busy and time.monotonic() < deadline:
                app.root.update()
                time.sleep(0.02)
            self.assertFalse(app.busy, "Tác vụ quét không hoàn tất trong 5 giây")
            self.assertIsNotNone(app.enhanced)
            self.assertEqual(len(app.original_panel.points), 4)
            previous_revision = app.image_revision
            app.mode_var.set("Thang xám")
            app._change_mode()
            while app.busy and time.monotonic() < deadline:
                app.root.update()
                time.sleep(0.02)
            self.assertFalse(app.busy, "Đổi chế độ ảnh không hoàn tất")
            self.assertEqual(app.enhanced.ndim, 2)
            self.assertGreater(app.image_revision, previous_revision)
            self.assertEqual(app.ocr_revision, -1)
        finally:
            app._close()
            del app
            gc.collect()


if __name__ == "__main__":
    unittest.main()
