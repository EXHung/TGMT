"""Tạo ảnh demo tổng hợp có nhãn; không dùng làm kết quả ảnh chụp thật."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "images" / "input" / "demo_tong_hop_vi_en.png"
LABEL = ROOT / "tests" / "data" / "demo_tong_hop_vi_en.json"
TEXT = [
    "TÀI LIỆU MẪU",
    "Đồ án Thị giác máy tính",
    "Ứng dụng quét tài liệu và nhận dạng chữ.",
    "This is a synthetic document scan test.",
    "Ngày 26 tháng 9 năm 2026",
]


def make_demo() -> tuple[Path, Path]:
    page = Image.new("RGB", (820, 1080), "#fbfbf8")
    drawing = ImageDraw.Draw(page)
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    title_path = Path("C:/Windows/Fonts/segoeuib.ttf")
    title_font = ImageFont.truetype(str(title_path), 53) if title_path.exists() else ImageFont.load_default()
    body_font = ImageFont.truetype(str(font_path), 31) if font_path.exists() else ImageFont.load_default()
    drawing.text((85, 105), TEXT[0], fill="#172b44", font=title_font)
    drawing.line((85, 186, 735, 186), fill="#2c75a5", width=5)
    for index, line in enumerate(TEXT[1:]):
        drawing.text((85, 245 + index * 115), line, fill="#202a35", font=body_font)
    drawing.rectangle((85, 810, 735, 930), outline="#b7c6d5", width=3)
    drawing.text((115, 840), "VI  +  EN", fill="#3b516b", font=body_font)

    page_bgr = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
    background = np.full((1150, 1350, 3), (74, 88, 105), dtype=np.uint8)
    y, x = np.indices(background.shape[:2])
    background[:, :, 0] = np.clip(background[:, :, 0].astype(np.int16) + x // 80, 0, 255).astype(np.uint8)
    background[:, :, 1] = np.clip(background[:, :, 1].astype(np.int16) + y // 90, 0, 255).astype(np.uint8)
    corners = np.float32([[170, 80], [1110, 160], [1180, 1010], [95, 1050]])
    source = np.float32([[0, 0], [819, 0], [819, 1079], [0, 1079]])
    transform = cv2.getPerspectiveTransform(source, corners)
    projected = cv2.warpPerspective(page_bgr, transform, (1350, 1150))
    mask = cv2.warpPerspective(np.full((1080, 820), 255, np.uint8), transform, (1350, 1150))
    background[mask > 0] = projected[mask > 0]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LABEL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imencode(".png", background)[1].tofile(str(OUTPUT))
    LABEL.write_text(
        json.dumps({"source": "synthetic", "corners": corners.tolist(), "text": TEXT}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return OUTPUT, LABEL


if __name__ == "__main__":
    image_path, label_path = make_demo()
    print(image_path)
    print(label_path)
