"""Validate page geometry and rectify the page at source resolution."""
import cv2
import numpy as np


def order_corners(corners):
    points = np.asarray(corners, dtype=np.float32)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise ValueError("Cần bốn góc hợp lệ")
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    points = points[np.argsort(angles)]
    start = int(np.argmin(points[:, 0] + points[:, 1]))
    return np.roll(points, -start, axis=0)


def validate_corners(corners, image_shape, minimum_fraction=0.01):
    height, width = image_shape[:2]
    points = order_corners(corners)
    if (points[:, 0] < 0).any() or (points[:, 0] >= width).any() or \
       (points[:, 1] < 0).any() or (points[:, 1] >= height).any():
        raise ValueError("Góc nằm ngoài ảnh")
    polygon = points.astype(np.float32)
    area = abs(cv2.contourArea(polygon))
    if area < width * height * minimum_fraction or not cv2.isContourConvex(polygon):
        raise ValueError("Bốn góc không tạo thành vùng trang hợp lệ")
    sides = np.linalg.norm(np.roll(points, -1, axis=0) - points, axis=1)
    if sides.min() < 10 or sides.max() / sides.min() > 15:
        raise ValueError("Cạnh trang quá ngắn hoặc méo")
    return points


def warp_document(image, corners, maximum_side=6000):
    points = validate_corners(corners, image.shape)
    top = np.linalg.norm(points[1] - points[0])
    bottom = np.linalg.norm(points[2] - points[3])
    right = np.linalg.norm(points[2] - points[1])
    left = np.linalg.norm(points[3] - points[0])
    width = int(round(max(top, bottom)))
    height = int(round(max(left, right)))
    if min(width, height) < 20:
        raise ValueError("Trang quá nhỏ để chỉnh phối cảnh")
    scale = min(1.0, maximum_side / max(width, height))
    width = max(1, int(width * scale))
    height = max(1, int(height * scale))
    target = np.array([[0, 0], [width - 1, 0],
                       [width - 1, height - 1], [0, height - 1]], dtype=np.float32)
    transform = cv2.getPerspectiveTransform(points, target)
    return cv2.warpPerspective(image, transform, (width, height))
