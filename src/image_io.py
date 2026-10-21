"""OpenCV image I/O that works with Vietnamese Windows paths."""
from pathlib import Path
import os
import tempfile
import cv2
import numpy as np

MAX_FILE_BYTES = 50_000_000
MAX_IMAGE_PIXELS = 40_000_000


def _preflight(path):
    """Reject large files and large decoded dimensions before OpenCV allocates memory."""
    source = Path(path)
    if source.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Tệp ảnh quá lớn; hãy chọn ảnh dưới 50 MB")
    try:
        from PIL import Image
    except ImportError:
        return 1  # OpenCV still applies its own pixel limit while decoding.
    with Image.open(source) as preview:
        width, height = preview.size
        if width * height > MAX_IMAGE_PIXELS:
            raise ValueError("Ảnh quá lớn; hãy giảm kích thước trước khi quét")
        return int(preview.getexif().get(274, 1))


def _orient(image, orientation):
    if orientation == 2:
        return cv2.flip(image, 1)
    if orientation == 3:
        return cv2.rotate(image, cv2.ROTATE_180)
    if orientation == 4:
        return cv2.flip(image, 0)
    if orientation == 5:
        return cv2.transpose(image)
    if orientation == 6:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if orientation == 7:
        return cv2.flip(cv2.transpose(image), -1)
    if orientation == 8:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def load_image(path):
    orientation = _preflight(path)
    data = np.fromfile(str(path), dtype=np.uint8)
    # Disable OpenCV's implicit EXIF rotation so orientation is applied exactly once.
    image = cv2.imdecode(data, cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
    if image is None:
        raise ValueError("Không mở được ảnh. Hãy chọn tệp JPG hoặc PNG hợp lệ")
    if image.shape[0] * image.shape[1] > MAX_IMAGE_PIXELS:
        raise ValueError("Ảnh quá lớn; hãy giảm kích thước trước khi quét")
    return _orient(image, orientation)


def save_image(path, image):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Chỉ hỗ trợ lưu ảnh PNG hoặc JPG")
    ok, encoded = cv2.imencode(suffix, image)
    if not ok:
        raise ValueError("Không mã hóa được ảnh")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".scan-", suffix=suffix,
                                         dir=str(target.parent), delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded.tobytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target
