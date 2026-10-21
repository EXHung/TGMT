"""Điểm chạy trong Spyder hoặc dòng lệnh.

Chạy tệp này trực tiếp để mở giao diện. Ví dụ dòng lệnh:
python -m src.main --input images/input/trang.jpg --mode gray
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_io import save_image
from src.ocr_engine import recognize_text, save_text
from src.pipeline import scan_document


def run_cli(
    input_path: str,
    output_path: str | None,
    mode: str,
    debug: bool,
    *,
    ocr: bool = False,
    languages: str = "vie+eng",
    text_output: str | None = None,
    force: bool = False,
) -> int:
    source = Path(input_path)
    destination = Path(output_path) if output_path else Path(__file__).resolve().parent.parent / "images" / "output" / f"{source.stem}_{mode}.png"
    debug_path = Path(__file__).resolve().parent.parent / "images" / "debug" / source.stem if debug else None
    result = scan_document(str(source), mode=mode, debug_dir=debug_path)
    if result.status != "ok" or result.enhanced is None:
        print(result.message, file=sys.stderr)
        return 1
    text_destination = Path(text_output) if text_output else destination.with_suffix(".txt")
    if destination.exists() and not force:
        print(f"Ảnh đầu ra đã tồn tại: {destination}. Dùng --force nếu muốn ghi đè.", file=sys.stderr)
        return 1
    if ocr and text_destination.exists() and not force:
        print(f"Văn bản đầu ra đã tồn tại: {text_destination}. Dùng --force nếu muốn ghi đè.", file=sys.stderr)
        return 1
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        save_image(destination, result.enhanced)
    except (OSError, ValueError) as exc:
        print(f"Không lưu được ảnh quét: {exc}", file=sys.stderr)
        return 1
    print(f"Đã lưu ảnh quét: {destination}")
    print(f"Cách tìm góc: {result.method}")
    if result.method in {"visible_page_estimate", "open_notebook_right_page"}:
        print(f"Lưu ý: {result.message}")
    if ocr:
        ocr_result = recognize_text(result.enhanced, languages)
        if ocr_result.status not in {"ok", "empty"}:
            print(ocr_result.message, file=sys.stderr)
            return 2
        try:
            text_destination.parent.mkdir(parents=True, exist_ok=True)
            save_text(text_destination, ocr_result.text)
        except OSError as exc:
            print(f"Không lưu được văn bản: {exc}", file=sys.stderr)
            return 2
        print(f"Đã lưu văn bản: {text_destination}")
    return 0


def main() -> int:
    # Windows terminals may default to a code page that cannot print Vietnamese.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Ứng dụng quét tài liệu")
    parser.add_argument("--input", help="Ảnh đầu vào; bỏ qua để mở giao diện")
    parser.add_argument("--output", help="Đường dẫn ảnh quét khi dùng --input")
    parser.add_argument("--mode", choices=["color", "gray", "bw"], default="color")
    parser.add_argument("--debug", action="store_true", help="Lưu ảnh trung gian")
    parser.add_argument("--ocr", action="store_true", help="Nhận dạng và lưu văn bản")
    parser.add_argument("--lang", choices=["vie", "eng", "vie+eng"], default="vie+eng")
    parser.add_argument("--text-output", help="Đường dẫn tệp văn bản OCR")
    parser.add_argument("--force", action="store_true", help="Cho phép ghi đè tệp đầu ra")
    args = parser.parse_args()
    if args.input:
        return run_cli(
            args.input, args.output, args.mode, args.debug,
            ocr=args.ocr, languages=args.lang,
            text_output=args.text_output, force=args.force,
        )
    from src.gui import ScannerApp
    app = ScannerApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
