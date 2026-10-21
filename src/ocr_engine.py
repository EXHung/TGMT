"""Nhận dạng chữ với Tesseract và dữ liệu ngôn ngữ trong dự án."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Lock
from time import perf_counter

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TESSERACT = PROJECT_ROOT / "tools" / "tesseract" / "tesseract.exe"
LOCAL_TESSDATA = PROJECT_ROOT / "tools" / "tesseract" / "tessdata"
OCR_TIMEOUT_SECONDS = 45
LANGUAGE_CHECK_TIMEOUT_SECONDS = 8
_TESSERACT_LOCK = Lock()


@dataclass(frozen=True)
class OCRResult:
    status: str
    text: str
    message: str
    elapsed_seconds: float = 0.0


def _resolve_executable(explicit: str | None) -> str | None:
    if explicit:
        candidate = Path(explicit).expanduser()
        return str(candidate) if candidate.is_file() else shutil.which(explicit)
    if LOCAL_TESSERACT.is_file():
        return str(LOCAL_TESSERACT)
    return shutil.which("tesseract")


def _installed_languages(executable: str, tessdata: Path | None) -> set[str]:
    command = [executable, "--list-langs"]
    if tessdata is not None:
        command.extend(["--tessdata-dir", str(tessdata)])
    completed = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=LANGUAGE_CHECK_TIMEOUT_SECONDS, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if completed.returncode:
        raise OSError("Tesseract không đọc được dữ liệu ngôn ngữ")
    return {line.strip() for line in (completed.stdout + completed.stderr).splitlines()}


def recognize_text(
    image: np.ndarray,
    languages: str = "vie+eng",
    *,
    tesseract_cmd: str | None = None,
) -> OCRResult:
    """Chạy OCR trên ảnh BGR/xám, ưu tiên bản Tesseract nằm trong dự án."""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return OCRResult("invalid_input", "", "Chưa có ảnh quét để nhận dạng chữ.")
    if languages not in {"vie", "eng", "vie+eng"}:
        return OCRResult("invalid_input", "", "Ngôn ngữ nhận dạng chưa được hỗ trợ.")
    try:
        import pytesseract
    except ImportError:
        return OCRResult(
            "unavailable", "",
            "Thiếu pytesseract trong Python đang chạy. Hãy mở ứng dụng bằng run_scanner.cmd trong thư mục dự án.",
        )
    executable = _resolve_executable(tesseract_cmd)
    if executable is None:
        return OCRResult("unavailable", "", "Chưa tìm thấy Tesseract trong thư mục dự án hoặc PATH.")
    tessdata = LOCAL_TESSDATA if LOCAL_TESSDATA.is_dir() else None
    start = perf_counter()
    try:
        installed = _installed_languages(executable, tessdata)
        missing = [lang for lang in languages.split("+") if lang not in installed]
        if missing:
            return OCRResult(
                "unavailable", "", "Thiếu dữ liệu nhận dạng cho: " + ", ".join(missing) + ".",
                perf_counter() - start,
            )
        if image.ndim == 2:
            prepared = image
        elif image.ndim == 3 and image.shape[2] == 3:
            prepared = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif image.ndim == 3 and image.shape[2] == 4:
            prepared = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            return OCRResult("invalid_input", "", "Định dạng ảnh quét không được hỗ trợ.")
        # pytesseract stores the command in a module global. The child process
        # also inherits TESSDATA_PREFIX; restore both values after this call.
        with _TESSERACT_LOCK:
            previous_command = pytesseract.pytesseract.tesseract_cmd
            previous_data = os.environ.get("TESSDATA_PREFIX")
            previous_subprocess_args = pytesseract.pytesseract.subprocess_args

            def hidden_subprocess_args(*args, **kwargs):
                options = previous_subprocess_args(*args, **kwargs)
                options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                return options

            pytesseract.pytesseract.tesseract_cmd = executable
            pytesseract.pytesseract.subprocess_args = hidden_subprocess_args
            if tessdata is not None:
                os.environ["TESSDATA_PREFIX"] = str(tessdata)
            try:
                text = pytesseract.image_to_string(
                    prepared, lang=languages, config="--psm 3", timeout=OCR_TIMEOUT_SECONDS,
                )
            finally:
                pytesseract.pytesseract.tesseract_cmd = previous_command
                pytesseract.pytesseract.subprocess_args = previous_subprocess_args
                if previous_data is None:
                    os.environ.pop("TESSDATA_PREFIX", None)
                else:
                    os.environ["TESSDATA_PREFIX"] = previous_data
    except subprocess.TimeoutExpired:
        return OCRResult("error", "", "Tesseract không phản hồi khi kiểm tra ngôn ngữ.", perf_counter() - start)
    except RuntimeError as exc:
        if "timeout" in str(exc).lower():
            message = "Nhận dạng chữ quá 45 giây. Hãy thử ảnh nhỏ hơn hoặc rõ hơn."
        else:
            message = "Không thể nhận dạng chữ. Hãy thử lại với ảnh khác."
        return OCRResult("error", "", message, perf_counter() - start)
    except pytesseract.TesseractNotFoundError:
        return OCRResult("unavailable", "", "Không khởi chạy được Tesseract trong thư mục dự án.", perf_counter() - start)
    except (pytesseract.TesseractError, OSError, ValueError):
        return OCRResult("error", "", "Không thể nhận dạng chữ. Hãy kiểm tra bộ OCR trong dự án.", perf_counter() - start)
    return OCRResult(
        "ok" if text.strip() else "empty",
        text,
        "Đã nhận dạng chữ." if text.strip() else "Chưa nhận dạng được chữ. Hãy thử chế độ ảnh khác hoặc chọn ảnh rõ hơn.",
        perf_counter() - start,
    )


def save_text(path: str | Path, text: str) -> None:
    """Ghi UTF-8 bằng tệp tạm để giữ tệp cũ nếu lưu thất bại."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=destination.parent,
            prefix=f".{destination.name}.", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
