"""Find a page quadrilateral using a few bounded edge configurations."""
from dataclasses import dataclass
import cv2
import numpy as np
from .config import DEFAULT_CONFIG
from .perspective import order_corners, validate_corners


@dataclass
class Detection:
    corners: object = None
    score: float = 0.0
    method: str = ""
    reason: str = ""


def _candidate(contour, shape, config):
    image_area = shape[0] * shape[1]
    area = cv2.contourArea(contour)
    fraction = area / image_area
    if not config.minimum_page_fraction <= fraction <= config.maximum_page_fraction:
        return None
    perimeter = cv2.arcLength(contour, True)
    for epsilon in (0.015, 0.025, 0.04):
        polygon = cv2.approxPolyDP(contour, epsilon * perimeter, True)
        if len(polygon) != 4 or not cv2.isContourConvex(polygon):
            continue
        try:
            corners = validate_corners(polygon.reshape(4, 2), shape, config.minimum_page_fraction)
        except ValueError:
            continue
        box_area = abs(cv2.contourArea(corners))
        rectangularity = min(1.0, area / max(box_area, 1.0))
        margin = min(corners[:, 0].min(), corners[:, 1].min(),
                     shape[1] - 1 - corners[:, 0].max(),
                     shape[0] - 1 - corners[:, 1].max())
        border_factor = 0.85 if margin < 2 else 1.0
        score = (0.7 * min(1.0, fraction / 0.5) + 0.3 * rectangularity) * border_factor
        return corners, score
    return None


def _bright_page_fallback(image):
    """Keep all visible content when a light notebook page touches the frame.

    This is a conservative axis-aligned crop, not a claim that four physical
    page corners were found. Reject sparse bright regions such as a projector.
    """
    height, width = image.shape[:2]
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    luminance = lab[:, :, 0]
    saturation = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1]
    light = np.uint8((luminance > 100) & (saturation < 95)) * 255
    close_size = max(3, int(round(min(height, width) * 0.027)) | 1)
    open_size = max(3, int(round(min(height, width) * 0.019)) | 1)
    light = cv2.morphologyEx(light, cv2.MORPH_CLOSE,
                             np.ones((close_size, close_size), np.uint8))
    light = cv2.morphologyEx(light, cv2.MORPH_OPEN,
                             np.ones((open_size, open_size), np.uint8))
    contours, _ = cv2.findContours(light, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    coverage = cv2.contourArea(contour) / (height * width)
    if coverage < 0.82:
        return None
    x, y, w, h = cv2.boundingRect(contour)
    if w / width < 0.78 or h / height < 0.78:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture = cv2.Canny(gray, 60, 160)
    if np.mean(texture > 0) < 0.008:
        return None
    padding_x, padding_y = round(width * 0.025), round(height * 0.025)
    left, top = max(0, x - padding_x), max(0, y - padding_y)
    right, bottom = min(width - 1, x + w - 1 + padding_x), min(height - 1, y + h - 1 + padding_y)
    corners = np.array([[left, top], [right, top], [right, bottom], [left, bottom]],
                       dtype=np.float32)
    return corners, coverage


def _open_notebook_right_page(image):
    """Locate a visible notebook fold and conservatively keep its right page."""
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = cv2.GaussianBlur(gray, (9, 9), 0).astype(np.float32)
    positions = []
    strengths = []
    low, high = int(width * 0.018), int(width * 0.27)
    for first, last in ((0.15, 0.35), (0.35, 0.65), (0.65, 0.85)):
        band = smooth[int(height * first):int(height * last)]
        profile = np.abs(np.diff(band, axis=1)).mean(axis=0)
        position = low + int(np.argmax(profile[low:high]))
        positions.append(position)
        strengths.append(profile[position])
    if min(strengths) < 3.5 or max(positions) - min(positions) > width * 0.035:
        return None
    # A genuine fold drifts gently rightwards from top to bottom in this view.
    if not positions[0] <= positions[1] <= positions[2]:
        return None
    seam = positions[1]
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    sat = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1]
    paper = (lab[:, :, 0] > 100) & (sat < 95)
    if seam > width * .06:
        if np.mean(paper[int(height*.25):int(height*.75), :max(low, seam-10)]) < .82:
            return None  # dark desk or other object to the left, not a second page
    elif min(strengths) < 4.5 or max(positions) - min(positions) > width*.02:
        return None  # a seam very near the frame needs stronger evidence
    body = paper[:, seam + int(width*.03):int(width*.88)]
    rows = np.flatnonzero(body.mean(axis=1) > .75)
    if len(rows) < height * .65:
        return None
    top = max(0, int(rows[0]) - int(height*.004))
    bottom = min(height-1, int(rows[-1]) + int(height*.004))
    cols = np.flatnonzero(paper[top:bottom, seam+10:].mean(axis=0) > .65)
    if len(cols) < width * .55:
        return None
    right = min(width-1, seam+10+int(cols[-1])+int(width*.004))
    right_top = right_bottom = right
    # Track the first sustained paper-to-desk transition in horizontal bands.
    # A fixed outer boundary leaves a triangular desk strip on slanted pages.
    outer_samples = []
    for center in np.linspace(max(top+30, int(height*.2)),
                              min(bottom-30, int(height*.8)), 5):
        first = max(top, int(center)-40)
        last = min(bottom, int(center)+40)
        profile = paper[first:last].mean(axis=0)
        search_start = max(int(width*.7), seam+int(width*.4))
        below = np.flatnonzero(profile[search_start:] < .75)
        if len(below):
            boundary = search_start + int(below[0])
            if boundary > width*.78:
                outer_samples.append((center, boundary))
    if len(outer_samples) >= 3:
        ys, xs = np.array(outer_samples).T
        slope, intercept = np.polyfit(ys, xs, 1)
        residual = np.median(np.abs(xs - (slope*ys + intercept)))
        if residual < width*.025 and 0 <= slope <= .12:
            padding = width*.004
            right_top = min(width-1, int(slope*top+intercept+padding))
            right_bottom = min(width-1, int(slope*bottom+intercept+padding))
    left = max(0, positions[0]-int(width*.002))
    if min(right_top,right_bottom)-left < width*.6 or bottom-top < height*.7:
        return None
    slope = (positions[2] - positions[0]) / (height * .5)
    left_top = max(0, int(left + slope * (top - height*.5)))
    left_bottom = max(0, int(left + slope * (bottom - height*.5)))
    return np.array([[left_top,top],[right_top,top],[right_bottom,bottom],[left_bottom,bottom]],
                    dtype=np.float32)


def _longest_row_run(coverage, threshold):
    """Return the longest continuous band whose rows mostly contain a region."""
    active = coverage >= threshold
    changes = np.diff(np.r_[False, active, False].astype(np.int8))
    starts, ends = np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)
    return max(zip(starts, ends), key=lambda pair: pair[1] - pair[0], default=None)


def _visible_display_fallback(image):
    """Estimate the visible screen/board when its physical corners are cropped.

    Require a broad, continuous bright or dark band and a different region above
    it. This is intentionally limited to nearly full-width classroom displays.
    """
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture = cv2.Canny(gray, 60, 160)
    if np.mean(texture > 0) < .008:
        return None
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    saturation = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1]
    bright = (lab[:, :, 0] > 145) & (saturation < 120)
    dark = gray < 130

    bright_run = _longest_row_run(bright.mean(axis=1), .72)
    if bright_run is not None:
        top, end = bright_run
        if (.07 * height < top < .32 * height and
                end - top > .48 * height and end < .82 * height and
                bright[:max(1, top - int(.025 * height))].mean() < .65):
            # The projected image reaches the right frame in this view. Its
            # bottom is partly hidden, so crop at the last mostly bright row.
            ys = np.linspace(top + .12 * (end - top),
                             top + .88 * (end - top), 7).astype(int)
            lefts = []
            for y in ys:
                row = np.mean(bright[max(0, y-3):min(height, y+4)], axis=0)
                active = np.flatnonzero(row > .7)
                if len(active) and active[0] < .08 * width:
                    lefts.append((y, active[0]))
            if len(lefts) >= 5 and bright[top:end, -int(.05*width):].mean() > .8:
                slope, intercept = np.polyfit(*np.asarray(lefts).T, 1)
                corners = np.array([
                    [np.clip(slope * top + intercept, 0, width-1), top],
                    [width-1, top], [width-1, end-1],
                    [np.clip(slope * (end-1) + intercept, 0, width-1), end-1],
                ], dtype=np.float32)
                return corners, "visible_projection_estimate"

    dark_run = _longest_row_run(dark.mean(axis=1), .65)
    if dark_run is not None:
        top, end = dark_run
        if (.18 * height < top < .52 * height and
                end > .95 * height and end - top > .45 * height and
                dark[:max(1, top-int(.025*height))].mean() < .35):
            ys = np.linspace(top + .08 * (end-top),
                             top + .80 * (end-top), 9).astype(int)
            rights = []
            for y in ys:
                row = np.mean(dark[max(0, y-3):min(height, y+4)], axis=0)
                # Ignore isolated chalk strokes and require a sustained light
                # wall to the right of the board.
                smooth = np.convolve(row, np.ones(15)/15, mode="same")
                transitions = np.flatnonzero(smooth[int(.72*width):] < .35)
                if len(transitions):
                    x = int(.72*width) + int(transitions[0])
                    if .76*width < x < .96*width:
                        rights.append((y, x))
            if len(rights) >= 6 and dark[top:end, :int(.05*width)].mean() > .7:
                slope, intercept = np.polyfit(*np.asarray(rights).T, 1)
                corners = np.array([
                    [0, top], [np.clip(slope*top+intercept, 1, width-1), top],
                    [np.clip(slope*(height-1)+intercept, 1, width-1), height-1],
                    [0, height-1],
                ], dtype=np.float32)
                return corners, "visible_blackboard_estimate"
    return None


def detect_document(image, config=DEFAULT_CONFIG, debug=None):
    height, width = image.shape[:2]
    scale = min(1.0, config.detection_long_side / max(height, width))
    resized = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else image.copy()
    if debug:
        debug.save("02_resized", resized)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    if debug:
        debug.save("03_gray", gray)
        debug.save("04_blur", blurred)
    configurations = [
        ("canny", blurred, False),
        ("canny_closed", blurred, True),
        ("clahe_closed", cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(blurred), True),
    ]
    candidates = []
    for name, source, close in configurations:
        edges = cv2.Canny(source, config.canny_low, config.canny_high)
        if close:
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        if debug:
            debug.save("05_edges_" + name, edges)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:config.max_candidates]
        for contour in contours:
            candidate = _candidate(contour, resized.shape, config)
            if candidate is not None:
                corners, score = candidate
                candidates.append((score, corners, name))
    best = max(candidates, key=lambda item: item[0]) if candidates else None
    if best is None or best[0] < config.min_score:
        display = _visible_display_fallback(resized)
        if display is not None:
            display_corners, method = display
            display_corners[:, 0] *= width / resized.shape[1]
            display_corners[:, 1] *= height / resized.shape[0]
            try:
                display_corners = validate_corners(
                    display_corners, image.shape, config.minimum_page_fraction)
            except ValueError:
                display_corners = None
            if display_corners is not None:
                if debug:
                    debug.corners("07_corners", image, display_corners)
                return Detection(corners=display_corners, score=0.0,
                                 method=method,
                                 reason="Ước lượng vùng nhìn thấy; ảnh không chứa đủ bốn góc thật")
        right_page = _open_notebook_right_page(resized)
        if right_page is not None:
            right_page[:, 0] *= width / resized.shape[1]
            right_page[:, 1] *= height / resized.shape[0]
            try:
                right_page = validate_corners(right_page, image.shape, config.minimum_page_fraction)
            except ValueError:
                right_page = None
            if right_page is not None:
                if debug:
                    debug.corners("07_corners", image, right_page)
                return Detection(corners=right_page, score=0.0,
                                 method="open_notebook_right_page",
                                 reason="Ước lượng vùng trang phải; mép ngoài có thể chưa chính xác")
        fallback = _bright_page_fallback(resized)
        if fallback is None:
            reason = ("Vùng trang tìm được chưa đủ tin cậy" if best is not None
                      else "Không tìm được đường viền trang có bốn góc hợp lệ")
            return Detection(score=best[0] if best is not None else 0.0, reason=reason)
        corners, score = fallback
        corners[:, 0] *= width / resized.shape[1]
        corners[:, 1] *= height / resized.shape[0]
        corners = order_corners(corners)
        try:
            corners = validate_corners(corners, image.shape, config.minimum_page_fraction)
        except ValueError as exc:
            return Detection(reason=str(exc))
        if debug:
            debug.corners("07_corners", image, corners)
        return Detection(corners=corners, score=0.0, method="visible_page_estimate",
                         reason="Chỉ giữ phần trang nhìn thấy; không xác định đủ bốn góc giấy")
    score, corners, method = best
    # Actual resize dimensions can differ by a pixel; convert each axis separately.
    corners[:, 0] *= width / resized.shape[1]
    corners[:, 1] *= height / resized.shape[0]
    corners = order_corners(corners)
    try:
        validate_corners(corners, image.shape, config.minimum_page_fraction)
    except ValueError as exc:
        return Detection(score=score, reason=str(exc))
    if debug:
        debug.corners("07_corners", image, corners)
    return Detection(corners=corners, score=score, method=method)
