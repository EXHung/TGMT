"""Small, central collection of scanner parameters (pixels refer to resized images)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ScanConfig:
    detection_long_side: int = 1000
    minimum_image_side: int = 100
    maximum_input_pixels: int = 40_000_000
    minimum_page_fraction: float = 0.08
    maximum_page_fraction: float = 0.96
    maximum_output_side: int = 6000
    canny_low: int = 50
    canny_high: int = 150
    max_candidates: int = 20
    min_score: float = 0.30


DEFAULT_CONFIG = ScanConfig()
