"""Giao diện quét tài liệu với hai chủ đề và phản hồi tương tác nhẹ."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from itertools import count

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.enhancement import enhance
from src.image_io import load_image, save_image
from src.ocr_engine import recognize_text, save_text
from src.pipeline import scan_document


MODES = {"Màu": "color", "Thang xám": "gray", "Đen trắng": "bw"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = PROJECT_ROOT / "images" / "input"
OUTPUT_DIR = PROJECT_ROOT / "images" / "output"


LANGUAGES = {
    "Tiếng Việt và tiếng Anh": "vie+eng",
    "Tiếng Việt": "vie",
    "Tiếng Anh": "eng",
}

PALETTES = {
    "dark": {
        "window": "#091321", "header": "#101F34", "card": "#14243A",
        "panel": "#0E1C2E", "canvas": "#0B1728", "text": "#F5F8FC",
        "muted": "#A9BDD3", "border": "#2A405A", "primary": "#4D8EFF",
        "primary_hover": "#70A5FF", "primary_ink": "#FFFFFF", "accent": "#43D7B2",
        "success": "#43D7B2", "danger": "#FF7889", "disabled": "#26384D",
        "disabled_ink": "#7F95AB", "focus": "#8BB8FF", "shadow": "#050D18",
    },
    "light": {
        "window": "#EEF3F9", "header": "#F9FBFE", "card": "#FFFFFF",
        "panel": "#F7FAFE", "canvas": "#E8EFF7", "text": "#14243A",
        "muted": "#53677E", "border": "#D5E0EB", "primary": "#2563EB",
        "primary_hover": "#1D4ED8", "primary_ink": "#FFFFFF", "accent": "#087F70",
        "success": "#087F70", "danger": "#C73650", "disabled": "#E5EBF2",
        "disabled_ink": "#8FA0B1", "focus": "#2563EB", "shadow": "#DDE6F0",
    },
}


def _blend(first: str, second: str, amount: float) -> str:
    """Interpolate a pair of #RRGGBB colours for a short hover transition."""
    return "#" + "".join(
        f"{round(int(first[i:i + 2], 16) * (1 - amount) + int(second[i:i + 2], 16) * amount):02x}"
        for i in (1, 3, 5)
    )


def _bgr(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (5, 3, 1))


class MotionButton(ttk.Button):
    """A normal keyboard-accessible ttk button with animated hover colour."""

    _ids = count(1)

    def __init__(self, parent, *, variant: str = "quiet", **kwargs) -> None:
        self.variant = variant
        self._style_name = f"Motion{next(self._ids)}.TButton"
        self._style_api = ttk.Style(parent)
        self._base = "#14243A"
        self._hover = "#1C3150"
        self._current = self._base
        self._animation = None
        self.motion_enabled = True
        super().__init__(parent, style=self._style_name, **kwargs)
        self.bind("<Enter>", lambda _event: self._animate(self._hover), add="+")
        self.bind("<Leave>", lambda _event: self._animate(self._base), add="+")

    def retheme(self, palette: dict[str, str], *, motion: bool) -> None:
        if self._animation is not None:
            self.after_cancel(self._animation)
            self._animation = None
        self.motion_enabled = motion
        if self.variant == "primary":
            self._base, self._hover = palette["primary"], palette["primary_hover"]
            ink = palette["primary_ink"]
        elif self.variant == "danger":
            self._base, self._hover = palette["card"], _blend(palette["card"], palette["danger"], .20)
            ink = palette["danger"]
        else:
            self._base, self._hover = palette["card"], _blend(palette["card"], palette["primary"], .15)
            ink = palette["text"]
        self._current = self._base
        padding = (15, 7) if self.variant == "primary" else (11, 6)
        self._style_api.configure(
            self._style_name, background=self._base, foreground=ink,
            font=("Segoe UI", 10, "bold" if self.variant == "primary" else "normal"),
            padding=padding, relief="flat", borderwidth=1, focusthickness=2,
            focuscolor=palette["focus"], bordercolor=palette["border"],
        )
        self._style_api.map(
            self._style_name,
            background=[("disabled", palette["disabled"])],
            foreground=[("disabled", palette["disabled_ink"])],
        )

    def _animate(self, target: str) -> None:
        if self._animation is not None:
            self.after_cancel(self._animation)
            self._animation = None
        if "disabled" in self.state() or not self.motion_enabled:
            self._current = target
            self._style_api.configure(self._style_name, background=target)
            return
        start = self._current

        def frame(step: int) -> None:
            self._current = _blend(start, target, step / 7)
            self._style_api.configure(self._style_name, background=self._current)
            self._animation = self.after(22, lambda: frame(step + 1)) if step < 7 else None

        frame(1)


def short_filename(name: str, limit: int = 54) -> str:
    """Keep both ends of long camera filenames visible in the header."""
    if len(name) <= limit:
        return name
    stem, dot, suffix = name.rpartition(".")
    extension = f".{suffix}" if dot else ""
    available = limit - len(extension) - 1
    if available < 8:
        return name[: limit - 1] + "…"
    return stem[: available // 2] + "…" + stem[-(available - available // 2):] + extension


class ImagePanel(ttk.Frame):
    """Khung ảnh hỗ trợ phóng to, kéo xem và trả tọa độ ảnh gốc."""

    def __init__(self, parent: tk.Misc, title: str, on_click=None, *, animate_scan=False) -> None:
        super().__init__(parent, style="Card.TFrame")
        self.palette = PALETTES["dark"]
        self.animate_scan = animate_scan
        self.motion_enabled = True
        self._sweep_generation = 0
        bar = ttk.Frame(self, style="Card.TFrame")
        bar.pack(fill="x", padx=15, pady=(12, 9))
        ttk.Label(bar, text=title, style="PanelTitle.TLabel").pack(side="left")
        self.zoom_var = tk.StringVar(value="100%")
        ttk.Button(bar, text="Vừa khung", style="Tiny.TButton", command=self.fit).pack(side="right")
        ttk.Button(bar, text="+", style="Tiny.TButton", width=2, command=lambda: self.zoom_by(1.25)).pack(side="right", padx=(0, 3))
        ttk.Button(bar, text="−", style="Tiny.TButton", width=2, command=lambda: self.zoom_by(.8)).pack(side="right", padx=(0, 3))
        ttk.Label(bar, textvariable=self.zoom_var, style="MutedCard.TLabel").pack(side="right", padx=(0, 8))
        self.canvas = tk.Canvas(
            self, bg=self.palette["canvas"], highlightthickness=1,
            highlightbackground=self.palette["border"],
            cursor="crosshair" if on_click else "arrow",
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<MouseWheel>", self._wheel)
        self.canvas.bind("<ButtonPress-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._pan)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.fit())
        self.canvas.bind("<Enter>", lambda _event: self.canvas.configure(highlightbackground=self.palette["primary"]))
        self.canvas.bind("<Leave>", lambda _event: self.canvas.configure(highlightbackground=self.palette["border"]))
        if on_click:
            self.canvas.bind("<Button-1>", self._clicked)
        self.image: np.ndarray | None = None
        self.photo: ImageTk.PhotoImage | None = None
        self.points: list[tuple[float, float]] = []
        self.on_click = on_click
        self.scale = 1.0
        self.offset = (0, 0)
        self.zoom = 1.0
        self.pan_offset = [0, 0]
        self._pan_anchor: tuple[int, int] | None = None

    def fit(self) -> None:
        self.zoom = 1.0
        self.pan_offset = [0, 0]
        self.redraw()

    def zoom_by(self, factor: float) -> None:
        if self.image is None:
            return
        self.zoom = max(1.0, min(self.zoom * factor, 8.0))
        if self.zoom == 1.0:
            self.pan_offset = [0, 0]
        self.redraw()

    def set_palette(self, palette: dict[str, str], *, motion: bool) -> None:
        self.palette = palette
        self.motion_enabled = motion
        self.canvas.configure(bg=palette["canvas"], highlightbackground=palette["border"])
        self.redraw()

    def _wheel(self, event: tk.Event) -> None:
        self.zoom_by(1.2 if event.delta > 0 else 1 / 1.2)

    def _start_pan(self, event: tk.Event) -> None:
        self._pan_anchor = (event.x, event.y)

    def _pan(self, event: tk.Event) -> None:
        if self._pan_anchor is None or self.zoom <= 1.0:
            return
        self.pan_offset[0] += event.x - self._pan_anchor[0]
        self.pan_offset[1] += event.y - self._pan_anchor[1]
        self._pan_anchor = (event.x, event.y)
        self.redraw()

    def set_image(self, image: np.ndarray | None) -> None:
        self._sweep_generation += 1
        self.image = image
        self.zoom = 1.0
        self.pan_offset = [0, 0]
        self.redraw()
        if image is not None and self.animate_scan and self.motion_enabled and self.winfo_ismapped():
            generation = self._sweep_generation
            self.after(50, lambda: self._sweep_step(generation, 0))

    def _sweep_step(self, generation: int, step: int) -> None:
        if generation != self._sweep_generation or self.image is None or not self.winfo_exists():
            return
        self.canvas.delete("scan-sweep")
        if step >= 16:
            return
        y = self.offset[1] + round(self.image.shape[0] * self.scale * step / 16)
        self.canvas.create_line(0, y, self.canvas.winfo_width(), y, fill=self.palette["accent"], width=2, tags="scan-sweep")
        self.after(26, lambda: self._sweep_step(generation, step + 1))

    def set_points(self, points: list[tuple[float, float]]) -> None:
        self.points = points
        self.redraw()

    def _clicked(self, event: tk.Event) -> None:
        if self.image is None or self.on_click is None:
            return
        x = (event.x - self.offset[0]) / self.scale
        y = (event.y - self.offset[1]) / self.scale
        height, width = self.image.shape[:2]
        if 0 <= x < width and 0 <= y < height:
            self.on_click((float(x), float(y)))

    def redraw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        self.zoom_var.set(f"{round(self.zoom * 100)}%")
        if self.image is None:
            center_x = max(canvas.winfo_width() // 2, 100)
            center_y = max(canvas.winfo_height() // 2, 100)
            canvas.create_rectangle(
                center_x - 65, center_y - 92, center_x + 65, center_y + 56,
                outline=self.palette["border"], width=2, dash=(7, 5),
            )
            canvas.create_line(
                center_x - 40, center_y - 35, center_x + 40, center_y - 35,
                fill=self.palette["border"], width=3,
            )
            canvas.create_text(
                center_x, center_y + 95,
                text="Chưa có ảnh" if self.on_click else "Bản quét sẽ hiện ở đây",
                fill=self.palette["muted"], font=("Segoe UI", 10),
            )
            return
        height, width = self.image.shape[:2]
        available_width = max(canvas.winfo_width() - 20, 1)
        available_height = max(canvas.winfo_height() - 20, 1)
        self.scale = min(available_width / width, available_height / height, 1.0) * self.zoom
        view_width = max(1, round(width * self.scale))
        view_height = max(1, round(height * self.scale))
        self.offset = (
            (canvas.winfo_width() - view_width) // 2 + self.pan_offset[0],
            (canvas.winfo_height() - view_height) // 2 + self.pan_offset[1],
        )
        # Render only visible canvas pixels, even when zoomed into a large photo.
        transform = np.float32([
            [self.scale, 0, self.offset[0]],
            [0, self.scale, self.offset[1]],
        ])
        preview = cv2.warpAffine(
            self.image, transform,
            (max(canvas.winfo_width(), 1), max(canvas.winfo_height(), 1)),
            flags=cv2.INTER_AREA if self.scale < 1 else cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=_bgr(self.palette["canvas"]),
        )
        if preview.ndim == 2:
            rgb = cv2.cvtColor(preview, cv2.COLOR_GRAY2RGB)
        elif preview.shape[2] == 4:
            rgb = cv2.cvtColor(preview, cv2.COLOR_BGRA2RGB)
        else:
            rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        self.photo = ImageTk.PhotoImage(pil, master=canvas)
        canvas.create_image(0, 0, anchor="nw", image=self.photo)
        if self.points:
            coords = [(self.offset[0] + x * self.scale, self.offset[1] + y * self.scale) for x, y in self.points]
            if len(coords) >= 2:
                flat = [v for point in coords for v in point]
                canvas.create_line(*flat, fill=self.palette["accent"], width=3)
            if len(coords) == 4:
                canvas.create_line(*coords[-1], *coords[0], fill=self.palette["accent"], width=3)
            for index, (x, y) in enumerate(coords, 1):
                canvas.create_oval(x - 7, y - 7, x + 7, y + 7, fill=self.palette["accent"], outline="white", width=2)
                canvas.create_text(x + 14, y - 14, text=str(index), fill=self.palette["text"], font=("Segoe UI", 10, "bold"))


class ScannerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("TGMT Scan Studio · Quét tài liệu")
        self.root.geometry("1420x820")
        self.root.minsize(920, 720)
        self.theme_name = "dark"
        self.palette = PALETTES[self.theme_name]
        self.root.configure(bg=self.palette["window"])
        self.messages: queue.Queue[tuple[int, str, object]] = queue.Queue()
        self.task_id = 0
        self.busy = False
        self.cancel_requested = False
        self.exported = False
        self.buttons: list[MotionButton] = []
        self.toast_widget: tk.Frame | None = None
        self._toast_generation = 0
        self.image_path: Path | None = None
        self.original: np.ndarray | None = None
        self.scanned: np.ndarray | None = None
        self.enhanced: np.ndarray | None = None
        self.manual_points: list[tuple[float, float]] = []
        self.selecting_points = False
        self.image_revision = 0
        self.ocr_revision = -1
        self.status_var = tk.StringVar(value="Chọn ảnh để bắt đầu.")
        self.file_var = tk.StringVar(value="Chưa chọn ảnh")
        self.file_tooltip: tk.Toplevel | None = None
        self.mode_var = tk.StringVar(value="Màu")
        self.language_var = tk.StringVar(value="Tiếng Việt và tiếng Anh")
        self.debug_var = tk.BooleanVar(value=False)
        self.motion_var = tk.BooleanVar(value=True)
        self._style()
        self._build()
        self._refresh_controls()
        self._bind_shortcuts()
        self.poll_job = self.root.after(80, self._poll)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _style(self) -> None:
        p = self.palette
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background=p["window"])
        style.configure("Card.TFrame", background=p["card"])
        style.configure("Header.TFrame", background=p["header"])
        style.configure("Step.TFrame", background=p["card"])
        style.configure("TLabel", background=p["window"], foreground=p["text"], font=("Segoe UI", 10))
        style.configure("HeaderKicker.TLabel", background=p["header"], foreground=p["accent"], font=("Segoe UI", 9, "bold"))
        style.configure("HeaderTitle.TLabel", background=p["header"], foreground=p["text"], font=("Segoe UI", 20, "bold"))
        style.configure("HeaderSub.TLabel", background=p["header"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("HeaderFile.TLabel", background=p["header"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("Section.TLabel", background=p["card"], foreground=p["text"], font=("Segoe UI", 12, "bold"))
        style.configure("PanelTitle.TLabel", background=p["card"], foreground=p["text"], font=("Segoe UI", 11, "bold"))
        style.configure("Card.TLabel", background=p["card"], foreground=p["text"], font=("Segoe UI", 10))
        style.configure("MutedCard.TLabel", background=p["card"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("Footer.TLabel", background=p["window"], foreground=p["muted"], font=("Segoe UI", 9))
        style.configure("StatusDot.TLabel", background=p["window"], foreground=p["accent"], font=("Segoe UI", 13, "bold"))
        for state, color in (("Idle", p["muted"]), ("Active", p["primary"]), ("Done", p["accent"])):
            style.configure(f"Step{state}.TLabel", background=p["card"], foreground=color, font=("Segoe UI", 9, "bold"))
        style.configure("TButton", background=p["card"], foreground=p["text"], font=("Segoe UI", 10), padding=(9, 7), borderwidth=1, relief="flat")
        style.map("TButton", background=[("disabled", p["disabled"]), ("active", p["panel"])], foreground=[("disabled", p["disabled_ink"])])
        style.configure("Tiny.TButton", background=p["card"], foreground=p["muted"], font=("Segoe UI", 9), padding=(5, 3), borderwidth=0, relief="flat")
        style.map("Tiny.TButton", background=[("active", p["panel"])], foreground=[("active", p["text"])])
        style.configure("TCombobox", font=("Segoe UI", 10), padding=(6, 7), fieldbackground=p["panel"], background=p["card"], foreground=p["text"], arrowcolor=p["muted"])
        style.map("TCombobox", fieldbackground=[("readonly", p["panel"]), ("disabled", p["disabled"])], foreground=[("readonly", p["text"]), ("disabled", p["disabled_ink"])])
        style.configure("TCheckbutton", background=p["card"], foreground=p["muted"], font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", p["card"])], foreground=[("active", p["text"])])
        style.configure("Horizontal.TProgressbar", background=p["accent"], troughcolor=p["panel"], borderwidth=0)

    def _button(self, parent, text: str, command, *, variant="quiet") -> MotionButton:
        button = MotionButton(parent, text=text, command=command, variant=variant)
        button.retheme(self.palette, motion=self.motion_var.get())
        self.buttons.append(button)
        return button

    def _build(self) -> None:
        self.header = ttk.Frame(self.root, style="Header.TFrame")
        self.header.pack(fill="x")
        header_inner = ttk.Frame(self.header, style="Header.TFrame")
        header_inner.pack(fill="x", padx=23, pady=(9, 9))
        self.logo_canvas = tk.Canvas(header_inner, width=48, height=48, bd=0, highlightthickness=0)
        self.logo_canvas.pack(side="left", padx=(0, 14))
        self._draw_logo()
        title_group = ttk.Frame(header_inner, style="Header.TFrame")
        title_group.pack(side="left", fill="x", expand=True)
        ttk.Label(title_group, text="TGMT  /  SCAN STUDIO", style="HeaderKicker.TLabel").pack(anchor="w")
        ttk.Label(title_group, text="Quét tài liệu", style="HeaderTitle.TLabel").pack(anchor="w")
        subline = ttk.Frame(title_group, style="Header.TFrame")
        subline.pack(fill="x")
        ttk.Label(subline, text="Tự căn bốn góc · Làm rõ ảnh · Nhận dạng chữ", style="HeaderSub.TLabel").pack(side="left")
        self.file_label = ttk.Label(subline, textvariable=self.file_var, style="HeaderFile.TLabel")
        self.file_label.pack(side="left", padx=(14, 0))
        self.file_label.bind("<Enter>", self._show_file_tooltip)
        self.file_label.bind("<Leave>", self._hide_file_tooltip)
        self.open_button = self._button(header_inner, "Chọn ảnh   Ctrl+O", self._choose_image, variant="primary")
        self.open_button.pack(side="right", padx=(8, 0))
        self.theme_button = self._button(header_inner, "Giao diện sáng", self._toggle_theme)
        self.theme_button.pack(side="right", padx=(8, 0))

        workflow = ttk.Frame(self.root)
        workflow.pack(fill="x", padx=22, pady=(8, 2))
        self.step_labels: list[ttk.Label] = []
        for index, title in enumerate(("Nạp ảnh", "Tự căn & quét", "Nhận dạng (tùy chọn)", "Xuất kết quả")):
            workflow.columnconfigure(index, weight=1)
            cell = ttk.Frame(workflow, style="Step.TFrame", padding=(13, 7))
            cell.grid(row=0, column=index, sticky="ew", padx=4)
            label = ttk.Label(cell, text=f"{index + 1:02d}  {title}", style="StepIdle.TLabel")
            label.pack(anchor="w")
            self.step_labels.append(label)

        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=22, pady=(4, 4))
        preview = ttk.Frame(body)
        body.add(preview, weight=4)
        previews = ttk.PanedWindow(preview, orient="horizontal")
        previews.pack(fill="both", expand=True)
        self.original_panel = ImagePanel(previews, "Ảnh gốc", self._add_point)
        self.output_panel = ImagePanel(previews, "Ảnh sau khi quét", animate_scan=True)
        previews.add(self.original_panel, weight=1)
        previews.add(self.output_panel, weight=1)

        right = ttk.Frame(body, style="Card.TFrame", width=356)
        body.add(right, weight=0)
        controls = ttk.Frame(right, style="Card.TFrame")
        controls.pack(fill="x", padx=17, pady=(10, 2))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Bảng điều khiển", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(controls, text="Quét tự động là thao tác chính", style="MutedCard.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(1, 6))
        self.scan_button = self._button(controls, "Tự căn và quét   Ctrl+Enter", self._scan, variant="primary")
        self.scan_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        self.manual_button = self._button(controls, "Chỉnh góc nếu cần", self._start_manual)
        self.manual_button.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        ttk.Label(controls, text="Chế độ ảnh", style="Card.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.mode_combo = ttk.Combobox(controls, textvariable=self.mode_var, values=list(MODES), state="readonly", width=12)
        self.mode_combo.grid(row=5, column=0, columnspan=2, sticky="ew")
        self.mode_combo.bind("<<ComboboxSelected>>", self._change_mode)
        ttk.Label(controls, text="Ngôn ngữ nhận dạng", style="Card.TLabel").grid(row=6, column=0, columnspan=2, sticky="w", pady=(5, 2))
        self.language_combo = ttk.Combobox(controls, textvariable=self.language_var, values=list(LANGUAGES), state="readonly", width=18)
        self.language_combo.grid(row=7, column=0, columnspan=2, sticky="ew")
        self.language_combo.bind("<<ComboboxSelected>>", self._language_changed)
        ttk.Checkbutton(controls, text="Lưu ảnh từng bước", variable=self.debug_var).grid(row=8, column=0, sticky="w", pady=(4, 0))
        ttk.Checkbutton(controls, text="Hiệu ứng", variable=self.motion_var, command=self._motion_changed).grid(row=8, column=1, sticky="e", pady=(4, 0))
        self.ocr_button = self._button(controls, "Nhận dạng chữ", self._run_ocr, variant="primary")
        self.ocr_button.grid(row=9, column=0, sticky="ew", padx=(0, 4), pady=(6, 0))
        self.cancel_button = self._button(controls, "Hủy xử lý", self._cancel, variant="danger")
        self.cancel_button.grid(row=9, column=1, sticky="ew", padx=(4, 0), pady=(6, 0))

        ttk.Separator(right, orient="horizontal").pack(fill="x", padx=17, pady=(7, 7))
        ttk.Label(right, text="Văn bản nhận dạng", style="Section.TLabel").pack(anchor="w", padx=17, pady=(0, 3))
        self.text_area = scrolledtext.ScrolledText(
            right, width=30, height=3, wrap="word", undo=True,
            font=("Segoe UI", 10), relief="flat", borderwidth=0,
            padx=12, pady=11, insertwidth=2,
        )
        self.text_area.pack(fill="both", expand=True, padx=17, pady=(0, 7))
        self.text_area.bind("<KeyRelease>", lambda _event: self._refresh_controls())
        saves = ttk.Frame(right, style="Card.TFrame")
        saves.pack(fill="x", padx=17, pady=(0, 8))
        saves.columnconfigure(0, weight=1)
        saves.columnconfigure(1, weight=1)
        self.save_image_button = self._button(saves, "Lưu ảnh quét", self._save_image)
        self.save_image_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.save_text_button = self._button(saves, "Lưu văn bản", self._save_text)
        self.save_text_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.copy_button = self._button(saves, "Sao chép văn bản", self._copy_text)
        self.copy_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        footer = ttk.Frame(self.root)
        self.footer = footer
        footer.pack(fill="x", padx=25, pady=(0, 6))
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=155)
        ttk.Label(footer, text="●", style="StatusDot.TLabel").pack(side="left", padx=(0, 7))
        ttk.Label(footer, textvariable=self.status_var, style="Footer.TLabel").pack(side="left")
        ttk.Label(footer, text="Cuộn để phóng to · Nhấp đúp để vừa khung", style="Footer.TLabel").pack(side="right")
        self._apply_theme()

    def _draw_logo(self) -> None:
        p = self.palette
        canvas = self.logo_canvas
        canvas.configure(bg=p["header"])
        canvas.delete("all")
        canvas.create_rectangle(3, 3, 45, 45, fill=p["primary"], outline="")
        canvas.create_polygon(14, 10, 30, 10, 36, 16, 36, 38, 14, 38, fill=p["primary_ink"], outline="")
        canvas.create_polygon(30, 10, 30, 16, 36, 16, fill=p["primary"], outline="")
        canvas.create_line(18, 25, 32, 25, fill=p["accent"], width=3)
        canvas.create_line(18, 31, 28, 31, fill=p["primary"], width=2)

    def _apply_theme(self) -> None:
        self.palette = PALETTES[self.theme_name]
        p = self.palette
        self._style()
        self.root.configure(bg=p["window"])
        self._draw_logo()
        self.original_panel.set_palette(p, motion=self.motion_var.get())
        self.output_panel.set_palette(p, motion=self.motion_var.get())
        for button in self.buttons:
            button.retheme(p, motion=self.motion_var.get())
        self.text_area.configure(
            bg=p["panel"], fg=p["text"], insertbackground=p["primary"],
            selectbackground=p["primary"], selectforeground=p["primary_ink"],
        )
        self.theme_button.configure(text="Giao diện sáng" if self.theme_name == "dark" else "Giao diện tối")
        self._update_workflow()

    def _toggle_theme(self) -> None:
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self._apply_theme()

    def _motion_changed(self) -> None:
        for button in self.buttons:
            button.retheme(self.palette, motion=self.motion_var.get())
        self.original_panel.motion_enabled = self.motion_var.get()
        self.output_panel.motion_enabled = self.motion_var.get()
        if not self.motion_var.get():
            self.output_panel._sweep_generation += 1
            self.output_panel.canvas.delete("scan-sweep")

    def _bind_shortcuts(self) -> None:
        bindings = {
            "<Control-o>": (self.open_button, self._choose_image),
            "<Control-Return>": (self.scan_button, self._scan),
            "<Control-Shift-R>": (self.ocr_button, self._run_ocr),
            "<Control-s>": (self.save_image_button, self._save_image),
            "<Control-Shift-S>": (self.save_text_button, self._save_text),
            "<Escape>": (self.cancel_button, self._cancel),
        }
        for sequence, (button, action) in bindings.items():
            self.root.bind(sequence, lambda _event, b=button, a=action: self._shortcut(b, a), add="+")

    @staticmethod
    def _shortcut(button: ttk.Button, action) -> str:
        if "disabled" not in button.state():
            action()
        return "break"

    def _update_workflow(self) -> None:
        if not hasattr(self, "step_labels"):
            return
        if self.original is None:
            active = 0
        elif self.scanned is None:
            active = 1
        elif self.exported:
            active = 4
        elif self.ocr_revision != self.image_revision:
            active = 2
        else:
            active = 3
        for index, label in enumerate(self.step_labels):
            state = "Done" if index < active else "Active" if index == active else "Idle"
            label.configure(style=f"Step{state}.TLabel")

    def _show_toast(self, message: str, *, kind: str = "success") -> None:
        if not self.root.winfo_ismapped():
            return
        self._toast_generation += 1
        generation = self._toast_generation
        if self.toast_widget is not None:
            self.toast_widget.destroy()
        p = self.palette
        accent = p["danger"] if kind == "error" else p["success"]
        self.toast_widget = tk.Frame(
            self.root, bg=p["card"], highlightthickness=1,
            highlightbackground=accent, padx=13, pady=9,
        )
        tk.Label(
            self.toast_widget, text=f"●  {message}", bg=p["card"], fg=p["text"],
            font=("Segoe UI", 10, "bold"),
        ).pack()
        self.toast_widget.place(relx=0.0, rely=1.0, x=25, y=-42, anchor="sw")

        def finish() -> None:
            if generation == self._toast_generation and self.toast_widget is not None:
                self.toast_widget.destroy()
                self.toast_widget = None

        if self.motion_var.get():
            def slide(step: int) -> None:
                if generation != self._toast_generation or self.toast_widget is None:
                    return
                self.toast_widget.place_configure(y=-57 + round(15 * step / 5))
                if step < 5:
                    self.root.after(22, lambda: slide(step + 1))
            slide(0)
        else:
            self.toast_widget.place_configure(y=-42)
        self.root.after(2800, finish)

    def _show_file_tooltip(self, _event=None) -> None:
        if self.image_path is None or self.file_tooltip is not None:
            return
        tooltip = tk.Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{self.file_label.winfo_rootx()}+{self.file_label.winfo_rooty() + self.file_label.winfo_height() + 3}")
        tk.Label(tooltip, text=str(self.image_path), bg="#152a45", fg="white",
                 padx=8, pady=5, wraplength=680, justify="left").pack()
        self.file_tooltip = tooltip

    def _hide_file_tooltip(self, _event=None) -> None:
        if self.file_tooltip is not None:
            self.file_tooltip.destroy()
            self.file_tooltip = None

    def _refresh_controls(self) -> None:
        self.open_button.configure(state="disabled" if self.busy else "normal")
        self.scan_button.configure(text="Quét theo góc đã chọn" if self.selecting_points else "Tự căn và quét")
        self.scan_button.configure(state="normal" if self.original is not None and not self.busy else "disabled")
        self.manual_button.configure(state="normal" if self.original is not None and not self.busy else "disabled")
        self.mode_combo.configure(state="readonly" if self.scanned is not None and not self.busy else "disabled")
        self.language_combo.configure(state="readonly" if self.enhanced is not None and not self.busy else "disabled")
        self.ocr_button.configure(state="normal" if self.enhanced is not None and not self.busy else "disabled")
        self.cancel_button.configure(state="normal" if self.busy and not self.cancel_requested else "disabled")
        self.save_image_button.configure(state="normal" if self.enhanced is not None and not self.busy else "disabled")
        text_available = bool(self.text_area.get("1.0", "end-1c").strip())
        valid_text = text_available and self.ocr_revision == self.image_revision
        self.save_text_button.configure(state="normal" if valid_text and not self.busy else "disabled")
        self.copy_button.configure(state="normal" if valid_text and not self.busy else "disabled")
        self._update_workflow()

    def _set_busy(self, value: bool, message: str = "") -> None:
        self.busy = value
        if value:
            self.progress.pack(side="right", padx=(10, 0))
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.pack_forget()
        if message:
            self.status_var.set(message)
        self._refresh_controls()

    def _submit(self, kind: str, work, message: str) -> None:
        if self.busy:
            return
        self.task_id += 1
        task_id = self.task_id
        self.cancel_requested = False
        self._set_busy(True, message)
        messages = self.messages

        def worker() -> None:
            try:
                result = work()
                messages.put((task_id, kind, result))
            except Exception as exc:
                messages.put((task_id, "error", (kind, str(exc))))

        threading.Thread(target=worker, daemon=True, name=f"scanner-{kind}").start()

    def _poll(self) -> None:
        try:
            while True:
                task_id, kind, result = self.messages.get_nowait()
                if task_id != self.task_id:
                    continue
                cancelled = self.cancel_requested
                self.cancel_requested = False
                self._set_busy(False)
                if cancelled:
                    self.status_var.set("Đã hủy xử lý.")
                    continue
                if kind == "open":
                    path, image = result
                    self.image_path = path
                    self.original = image
                    self.scanned = None
                    self.enhanced = None
                    self.manual_points = []
                    self.selecting_points = False
                    self.image_revision += 1
                    self._clear_text()
                    self._hide_file_tooltip()
                    self.file_var.set(short_filename(path.name))
                    self.original_panel.set_points([])
                    self.original_panel.set_image(image)
                    self.output_panel.set_image(None)
                    self.status_var.set("Ảnh đã mở. Bấm Tự căn và quét để tiếp tục.")
                    self._show_toast("Đã mở ảnh. Sẵn sàng tự căn.")
                elif kind == "scan":
                    if result.status == "ok" and result.scanned is not None:
                        self.scanned = result.scanned
                        self.enhanced = result.enhanced
                        self.image_revision += 1
                        self._clear_text()
                        self.original_panel.set_points(
                            [tuple(map(float, point)) for point in result.corners]
                            if result.corners is not None else []
                        )
                        self.output_panel.set_image(self.enhanced)
                        if result.method == "manual":
                            self.status_var.set("Đã quét theo bốn góc đã chọn. Bạn có thể lưu ảnh.")
                        elif result.method == "visible_page_estimate":
                            self.status_var.set("Đã tự căn phần trang nhìn thấy; ảnh có thể thiếu mép giấy.")
                        elif result.method == "open_notebook_right_page":
                            self.status_var.set("Đã tự căn trang vở bên phải; góc được ước lượng từ các mép nhìn thấy.")
                        else:
                            self.status_var.set("Đã tự động xác định bốn góc và quét tài liệu. Bạn có thể lưu ảnh.")
                        self._show_toast("Đã tạo bản quét")
                    else:
                        self.scanned = None
                        self.enhanced = None
                        self.image_revision += 1
                        self._clear_text()
                        self.output_panel.set_image(None)
                        if result.status == "manual_required":
                            self.selecting_points = False
                            self.manual_points = []
                            self.original_panel.set_points([])
                            self.status_var.set(f"{result.message}. Thử ảnh rõ hơn hoặc dùng Chỉnh góc nếu cần.")
                        elif result.status == "invalid_input" and len(self.manual_points) == 4:
                            self.selecting_points = True
                            self.status_var.set(f"{result.message} Chọn lại bốn góc rồi quét lại.")
                        else:
                            self.status_var.set(result.message)
                        self._show_toast("Chưa tìm được trang phù hợp", kind="error")
                elif kind == "enhance":
                    self.enhanced = result
                    self.output_panel.set_image(self.enhanced)
                    self.image_revision += 1
                    self._clear_text()
                    self.status_var.set("Đã đổi chế độ ảnh. Nhận dạng chữ lại nếu cần.")
                elif kind == "ocr":
                    if result.status in {"ok", "empty"}:
                        self.text_area.delete("1.0", "end")
                        self.text_area.insert("1.0", result.text)
                        self.ocr_revision = self.image_revision
                        self._show_toast("Đã nhận dạng chữ" if result.status == "ok" else "Chưa đọc được chữ")
                    self.status_var.set(result.message)
                elif kind == "save_image":
                    self.exported = True
                    self.status_var.set(f"Đã lưu ảnh quét: {result}")
                    self._show_toast("Đã lưu ảnh quét")
                elif kind == "error":
                    if result[0] == "open" and self.image_path is not None:
                        self.status_var.set("Không mở được ảnh mới; kết quả ảnh trước vẫn đang hiển thị.")
                    elif result[0] == "save_image":
                        self.status_var.set("Không lưu được ảnh. Hãy thử thư mục khác.")
                    else:
                        self.status_var.set("Xử lý gặp lỗi. Bạn có thể thử lại hoặc chọn ảnh khác.")
                    action = {"open": "mở ảnh", "scan": "quét tài liệu", "enhance": "đổi chế độ ảnh",
                              "ocr": "nhận dạng chữ", "save_image": "lưu ảnh"}.get(result[0], "xử lý")
                    messagebox.showerror("Lỗi xử lý", f"Không thể {action}.\nChi tiết: {result[1]}")
                    self._show_toast("Xử lý chưa hoàn tất", kind="error")
                self._refresh_controls()
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.poll_job = self.root.after(80, self._poll)

    def _choose_image(self) -> None:
        name = filedialog.askopenfilename(
            title="Chọn ảnh tài liệu", initialdir=str(INPUT_DIR), filetypes=[("Ảnh JPG và PNG", "*.jpg *.jpeg *.png"), ("Tất cả tệp", "*.*")],
        )
        if not name:
            return
        path = Path(name)

        def load():
            image = load_image(path)
            if image is None or image.size == 0:
                raise ValueError("Không đọc được ảnh. Hãy chọn tệp JPG hoặc PNG hợp lệ.")
            return path, image

        self._submit("open", load, "Đang mở ảnh…")

    def _scan(self) -> None:
        if self.original is None:
            return
        if self.selecting_points and len(self.manual_points) != 4:
            self.status_var.set("Hãy chọn đủ bốn góc trước khi quét tài liệu.")
            return
        image = self.original
        corners = self.manual_points.copy() if self.selecting_points and len(self.manual_points) == 4 else None
        mode = MODES[self.mode_var.get()]
        debug_dir = None
        if self.debug_var.get():
            stem = self.image_path.stem if self.image_path else "anh"
            debug_dir = Path(__file__).resolve().parent.parent / "images" / "debug" / stem
        self.selecting_points = False
        self._submit(
            "scan",
            lambda: scan_document(image, manual_corners=corners, mode=mode, debug_dir=debug_dir),
            "Đang quét tài liệu…",
        )

    def _start_manual(self) -> None:
        if self.original is None:
            return
        self.selecting_points = True
        self.manual_points = []
        self.scanned = None
        self.enhanced = None
        self.image_revision += 1
        self._clear_text()
        self.output_panel.set_image(None)
        self.original_panel.set_points([])
        self.status_var.set("Chọn lần lượt bốn góc trang trên ảnh gốc, rồi bấm Quét theo góc đã chọn.")
        self._refresh_controls()

    def _add_point(self, point: tuple[float, float]) -> None:
        if not self.selecting_points or self.busy:
            return
        if len(self.manual_points) == 4:
            self.manual_points.clear()
        self.manual_points.append(point)
        self.original_panel.set_points(self.manual_points)
        count = len(self.manual_points)
        self.status_var.set("Đã chọn bốn góc. Bấm Quét theo góc đã chọn." if count == 4 else f"Đã chọn {count}/4 góc.")

    def _change_mode(self, _event=None) -> None:
        if self.scanned is None or self.busy:
            return
        scanned = self.scanned
        mode = MODES[self.mode_var.get()]
        self.enhanced = None
        self.image_revision += 1
        self._clear_text()
        self._submit("enhance", lambda: enhance(scanned, mode), "Đang đổi chế độ ảnh…")

    def _run_ocr(self) -> None:
        if self.enhanced is None:
            return
        image = self.enhanced.copy()
        languages = LANGUAGES[self.language_var.get()]
        self._clear_text()
        self._submit("ocr", lambda: recognize_text(image, languages), "Đang nhận dạng chữ…")

    def _language_changed(self, _event=None) -> None:
        self._clear_text()
        if self.enhanced is not None:
            self.status_var.set("Đã đổi ngôn ngữ. Hãy nhận dạng chữ lại.")
        self._refresh_controls()

    def _clear_text(self) -> None:
        self.text_area.delete("1.0", "end")
        self.ocr_revision = -1
        self.exported = False

    def _cancel(self) -> None:
        if self.busy:
            self.cancel_requested = True
            self.status_var.set("Đang hủy…")
            self._refresh_controls()

    def _save_image(self) -> None:
        if self.enhanced is None:
            return
        initial = f"{self.image_path.stem if self.image_path else 'tai_lieu'}_quet.png"
        name = filedialog.asksaveasfilename(title="Lưu ảnh quét", defaultextension=".png", initialdir=str(OUTPUT_DIR), initialfile=initial, filetypes=[("Ảnh PNG", "*.png"), ("Ảnh JPEG", "*.jpg")])
        if not name:
            return
        path = Path(name)
        if path.exists() and not messagebox.askyesno("Ghi đè tệp", f"Tệp {path.name} đã tồn tại. Bạn muốn ghi đè?"):
            return
        image = self.enhanced.copy()
        self._submit("save_image", lambda: save_image(path, image), "Đang lưu ảnh quét…")

    def _save_text(self) -> None:
        if self.ocr_revision != self.image_revision:
            return
        text = self.text_area.get("1.0", "end-1c")
        if not text.strip():
            return
        initial = f"{self.image_path.stem if self.image_path else 'tai_lieu'}_van_ban.txt"
        name = filedialog.asksaveasfilename(title="Lưu văn bản", defaultextension=".txt", initialdir=str(OUTPUT_DIR), initialfile=initial, filetypes=[("Văn bản UTF-8", "*.txt")])
        if not name:
            return
        path = Path(name)
        if path.exists() and not messagebox.askyesno("Ghi đè tệp", f"Tệp {path.name} đã tồn tại. Bạn muốn ghi đè?"):
            return
        try:
            save_text(path, text)
        except OSError as exc:
            messagebox.showerror("Không lưu được văn bản", f"Hãy chọn thư mục khác và thử lại.\n{exc}")
            return
        self.status_var.set(f"Đã lưu văn bản: {path}")
        self.exported = True
        self._update_workflow()
        self._show_toast("Đã lưu văn bản UTF-8")

    def _copy_text(self) -> None:
        if self.ocr_revision != self.image_revision:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.text_area.get("1.0", "end-1c"))
        self.status_var.set("Đã sao chép văn bản.")
        self._show_toast("Đã sao chép văn bản")

    def _close(self) -> None:
        self.task_id += 1
        if self.poll_job is not None:
            self.root.after_cancel(self.poll_job)
            self.poll_job = None
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()
