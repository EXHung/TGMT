"""Đo thời gian quét trên ảnh tổng hợp; không đại diện ảnh chụp thật."""

from __future__ import annotations

import statistics
import sys
from pathlib import Path
from time import perf_counter

from src.image_io import load_image
from src.pipeline import scan_document


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    source = Path(__file__).resolve().parents[1] / "images" / "input" / "demo_tong_hop_vi_en.png"
    image = load_image(source)
    times: list[float] = []
    for _ in range(20):
        started = perf_counter()
        result = scan_document(image, mode="gray")
        times.append(perf_counter() - started)
        if result.status != "ok":
            raise RuntimeError(result.message)
    ordered = sorted(times)
    print(f"Ảnh: {image.shape[1]}×{image.shape[0]} px; 20 lượt; không lưu debug")
    print(f"Trung vị: {statistics.median(times):.3f} s")
    print(f"P95 (nearest rank): {ordered[18]:.3f} s")
    print(f"Lớn nhất: {ordered[-1]:.3f} s")


if __name__ == "__main__":
    main()
