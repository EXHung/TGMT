"""Local visual audit of newly supplied photographs; no ground-truth labels."""
from pathlib import Path
from time import perf_counter
import sys
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.image_io import load_image, save_image
from src.pipeline import scan_document

project_root = Path(__file__).resolve().parents[1]
source = project_root / "images" / "input"
destination = project_root / "images" / "debug" / "photo_audit"
destination.mkdir(parents=True, exist_ok=True)
photos = sorted(source.glob("*.jpg"))
tiles = []
for index, photo in enumerate(photos, 1):
    start = perf_counter()
    result = scan_document(photo)
    elapsed = perf_counter() - start
    original = load_image(photo)
    display = cv2.resize(original, (360, 480))
    if result.corners is not None:
        ratio = np.array([360 / original.shape[1], 480 / original.shape[0]], dtype=np.float32)
        points = (result.corners * ratio).astype(np.int32)
        cv2.polylines(display, [points], True, (0, 255, 0), 3)
    scan = cv2.resize(result.scanned, (360, 480)) if result.scanned is not None else np.zeros_like(display)
    cv2.putText(display, f"{index:02d} {result.status} {elapsed:.2f}s", (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    tiles.append(np.hstack([display, scan]))
    print(f"{index:02d}\t{photo.name}\t{result.status}\t{result.method}\t{result.score:.3f}\t{elapsed:.3f}")
if tiles:
    save_image(destination / "contact_sheet.jpg", np.vstack(tiles))
