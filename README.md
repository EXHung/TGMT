# Scan Studio

Ứng dụng quét tài liệu chạy cục bộ: tự tìm vùng trang hoặc vùng bảng/màn chiếu nhìn thấy, căn phối cảnh, làm rõ ảnh và nhận dạng chữ tiếng Việt, tiếng Anh bằng Tesseract. Giao diện web chạy trên máy cá nhân tại `http://127.0.0.1:8765/`; bản Tkinter cũ và CLI dùng chung lõi xử lý.

## Cài đặt trên Windows

Yêu cầu Python 3.12 và Tesseract OCR có dữ liệu ngôn ngữ `eng` và `vie`.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Cài Tesseract riêng và thêm `tesseract.exe` vào `PATH`, hoặc đặt bộ Tesseract Windows vào `tools/tesseract/` gồm `tesseract.exe` và `tessdata/eng.traineddata`, `tessdata/vie.traineddata`. Thư viện `pytesseract` trong `requirements.txt` chỉ là cầu nối Python; cần chương trình Tesseract để dùng OCR. Mã nguồn hoạt động ở chế độ quét ảnh ngay cả khi chưa cài Tesseract.

## Chạy ứng dụng

```powershell
.\run_scanner.cmd
```

Mở `http://127.0.0.1:8765/` nếu trình duyệt chưa tự mở. Có thể dùng `run_desktop.cmd` cho giao diện Tkinter, hoặc:

```powershell
.\.venv\Scripts\python.exe -m src.main --input images/input/demo_tong_hop_vi_en.png --mode color
```

Ảnh của bạn đặt trong `images/input/`. Ảnh quét và ảnh gỡ lỗi có thể lưu vào `images/output/` và `images/debug/`. Chỉ ảnh demo tổng hợp được đưa vào repo; ảnh cá nhân và đầu ra được loại khỏi Git.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Lần kiểm tra gần nhất: **24/24 kiểm thử đạt**. Bộ tự căn trả vùng quét trên cả 9 ảnh JPG thật đã khảo sát tại máy phát triển. Với ảnh bảng hoặc màn chiếu thiếu góc thật, ứng dụng chỉ **ước lượng vùng nhìn thấy**, không khôi phục nội dung đã nằm ngoài khung hay bị che. Các ảnh thật không được đăng công khai trong repo này; kiểm thử phụ thuộc ảnh thật sẽ tự bỏ qua khi không có ảnh.

Xem thêm [hướng dẫn bản web](docs/web-app.md), [lộ trình](docs/roadmap.md) và [ghi chú kiểm thử](docs/testing.md).
