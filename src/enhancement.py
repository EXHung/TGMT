"""Three scan modes; OCR can choose a mode independently."""
import cv2


def enhance(image, mode="color"):
    if mode == "color":
        return image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    if mode == "gray":
        return gray
    if mode == "bw":
        # Estimate illumination over a region much larger than letter strokes.
        # Dividing by it removes broad shadows before Otsu chooses one threshold.
        scale = min(1.0, 800 / max(gray.shape[:2]))
        small = cv2.resize(gray, None, fx=scale, fy=scale,
                           interpolation=cv2.INTER_AREA) if scale < 1 else gray
        sigma = max(6.0, min(small.shape[:2]) * 0.018)
        background = cv2.GaussianBlur(small, (0, 0), sigma)
        if scale < 1:
            background = cv2.resize(background, (gray.shape[1], gray.shape[0]),
                                    interpolation=cv2.INTER_LINEAR)
        corrected = cv2.divide(gray, background, scale=255)
        _, binary = cv2.threshold(corrected, 0, 255,
                                  cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    if mode == "adaptive":
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 31, 12)
    raise ValueError("Chế độ ảnh phải là color, gray, bw hoặc adaptive")


def apply_enhancement(image, mode="color"):
    """Convenient GUI alias for switching modes without repeating detection."""
    return enhance(image, mode)
