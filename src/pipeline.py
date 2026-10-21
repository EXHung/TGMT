"""UI-independent scanner entry point usable from Spyder or a GUI."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .config import DEFAULT_CONFIG
from .debug_utils import DebugImages
from .document_detector import detect_document
from .enhancement import enhance
from .image_io import load_image
from .perspective import validate_corners, warp_document


@dataclass
class ScanResult:
    status: str
    message: str
    original: object = None
    scanned: object = None
    enhanced: object = None
    corners: object = None
    method: str = ""
    score: float = 0.0
    debug_dir: object = None


def scan_document(image, *, manual_corners=None, debug_dir=None,
                  mode="color", config=DEFAULT_CONFIG):
    """Scan BGR ndarray or path. Manual points are in original-image coordinates."""
    try:
        original = load_image(image) if isinstance(image, (str, Path)) else image
        if not isinstance(original, np.ndarray) or original.dtype != np.uint8 or \
           original.ndim != 3 or original.shape[2] != 3:
            raise ValueError("Ảnh đầu vào phải là ảnh màu BGR 8 bit")
        height, width = original.shape[:2]
        if min(height, width) < config.minimum_image_side:
            raise ValueError("Ảnh quá nhỏ để tìm tài liệu")
        if height * width > config.maximum_input_pixels:
            raise ValueError("Ảnh quá lớn; hãy giảm kích thước trước khi quét")
        debug = DebugImages(debug_dir)
        debug.save("01_original", original)
        if manual_corners is not None:
            corners = validate_corners(manual_corners, original.shape)
            method, score = "manual", 1.0
            debug.corners("07_corners", original, corners)
        else:
            detection = detect_document(original, config, debug)
            if detection.corners is None:
                return ScanResult("manual_required", detection.reason, original=original,
                                  score=detection.score, debug_dir=debug.directory)
            corners, method, score = detection.corners, detection.method, detection.score
        scanned = warp_document(original, corners, config.maximum_output_side)
        debug.save("08_warped", scanned)
        enhanced = enhance(scanned, mode)
        debug.save("09_enhanced", enhanced)
        if method == "visible_page_estimate":
            message = "Chỉ căn được phần trang nhìn thấy; ảnh gốc có thể thiếu mép giấy"
        elif method == "open_notebook_right_page":
            message = "Đã tự căn trang vở bên phải; bốn góc được ước lượng từ các mép nhìn thấy"
        elif method in {"visible_projection_estimate", "visible_blackboard_estimate"}:
            message = "Đã tự căn vùng nhìn thấy; một số góc nằm ngoài ảnh hoặc bị che khuất"
        else:
            message = "Đã quét tài liệu"
        return ScanResult("ok", message, original, scanned, enhanced,
                          corners, method, score, debug.directory)
    except (ValueError, OSError, TypeError) as exc:
        return ScanResult("invalid_input", str(exc), original=image if isinstance(image, np.ndarray) else None)
