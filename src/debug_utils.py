"""Optional intermediate images, each run in its own folder."""
from pathlib import Path
from uuid import uuid4
import cv2
from .image_io import save_image


class DebugImages:
    def __init__(self, base_dir=None):
        self.directory = None
        if base_dir is not None:
            self.directory = Path(base_dir) / uuid4().hex[:12]
            self.directory.mkdir(parents=True, exist_ok=False)

    def save(self, name, image):
        if self.directory is not None:
            save_image(self.directory / (name + ".png"), image)

    def corners(self, name, image, corners):
        if self.directory is None:
            return
        overlay = image.copy()
        polygon = corners.astype("int32")
        cv2.polylines(overlay, [polygon], True, (0, 255, 0), 3)
        for index, point in enumerate(polygon):
            cv2.circle(overlay, tuple(point), 7, (0, 0, 255), -1)
            cv2.putText(overlay, str(index + 1), tuple(point),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        self.save(name, overlay)
