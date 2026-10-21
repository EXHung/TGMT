# Scan Studio Web

Ngày triển khai: 21/10/2026.

## Mục tiêu và thiết kế

Bản web chuyển luồng chọn ảnh → tự căn bốn góc → tạo bản quét → OCR → tải kết quả sang trình duyệt. Công cụ UI UX Pro Max tại `D:\NEW\New folder\Tool-git\UX-UI` đã được dùng để tạo hệ thống thiết kế cho một ứng dụng quét tài liệu responsive và tra cứu hướng dẫn về tải ảnh, tiến trình, thao tác kéo thả, khả năng tiếp cận. Bản triển khai dùng bố cục lưới gọn kiểu Swiss, nền slate sáng, màu xanh lam cho hành động chính, xanh ngọc cho góc phát hiện và trạng thái. Có chủ đề tối, nhãn tiếng Việt, focus rõ, hỗ trợ bàn phím và `prefers-reduced-motion`.

Giao diện dùng HTML/CSS/JavaScript thuần, không tải thư viện hoặc phông từ Internet. Ở màn hình rộng, ảnh gốc, ảnh quét và bảng điều khiển nằm cạnh nhau. Ở màn hình vừa và nhỏ, chúng xếp thành hai cột rồi một cột. Trạng thái rỗng, trạng thái đang xử lý, lỗi và kết quả có phản hồi riêng. Các hiệu ứng gồm hover, thông báo ngắn, chấm trạng thái nhấp nháy khi xử lý và vệt quét sau khi tạo ảnh; chúng không đại diện cho tiến độ thuật toán.

## Chạy ứng dụng

Từ thư mục dự án, chạy `run_scanner.cmd` hoặc `run_web.cmd`. Máy chủ lắng nghe `127.0.0.1:8765` và tự mở trình duyệt mặc định. Giữ cửa sổ lệnh trong lúc sử dụng; đóng cửa sổ đó để dừng. Có thể đổi cổng bằng `run_scanner.cmd --port 8766`. Bản Tkinter cũ mở bằng `run_desktop.cmd`.

## Kiến trúc

- `src/web_server.py`: máy chủ HTTP cục bộ từ thư viện chuẩn Python, phục vụ ba tệp tĩnh và hai API. Không phụ thuộc Flask hoặc dịch vụ cloud.
- `web/index.html`, `web/app.css`, `web/app.js`: giao diện responsive, tải ảnh bằng kéo thả hoặc hộp chọn, hiển thị bốn góc, chế độ ảnh, OCR, chủ đề, phóng to, tải PNG/TXT.
- `src/pipeline.py`: tự tìm bốn góc, chỉnh phối cảnh và làm rõ ảnh. `src/ocr_engine.py`: OCR Tesseract cục bộ. Bản web gọi lại hai phần này, không có thuật toán quét thứ hai.
- `POST /api/scan?mode=color|gray|bw`: nhận ảnh JPG/PNG dạng body nhị phân; trả ảnh PNG, bốn góc, cách phát hiện và thông báo. Tham số `corners` chỉ dùng khi người dùng tự chọn bốn góc để sửa ngoại lệ.
- `POST /api/ocr?lang=vie+eng|vie|eng`: nhận bản quét PNG/JPG, trả văn bản và thời gian xử lý.

Máy chủ chỉ bind loopback, kiểm tra Host/Origin, giới hạn ảnh 25 MB, giới hạn số tác vụ đồng thời, dùng tệp tạm tự xóa và không lưu ảnh hoặc văn bản lên máy chủ. Trình duyệt lưu đầu ra khi người dùng bấm tải. Cần kiểm tra văn bản OCR trước khi dùng; chữ viết tay vẫn có thể sai nhiều. Ảnh hiển thị góc theo kích thước đã định hướng EXIF; với vài trình duyệt xử lý EXIF khác, nên đối chiếu góc trên bản xem trước trước khi dùng chỉnh tay.

## Kiểm tra

`python -m unittest discover -s tests -q` bằng `.venv`: 24/24 đạt ngày 21/10/2026. `tests/test_web.py` quét ảnh demo tổng hợp qua adapter web và chạy OCR thật trên ảnh đầu ra. API `/api/scan` đã trả 200 trên hai ảnh bảng/màn chiếu ban đầu bị từ chối. Máy chủ khởi động tại `http://127.0.0.1:8765/`.

Trong lượt triển khai này, công cụ trình duyệt từ chối mở `localhost`; chưa có nghiệm thu trực quan web ở 375/768/1024/1440 px hoặc kiểm tra tương tác bằng trình duyệt. Cần mở bằng trình duyệt trên máy và kiểm tra chọn ảnh, kéo thả, hiển thị góc, tự quét, OCR, tải tệp, chủ đề sáng/tối và các kích thước màn hình trước khi coi là nghiệm thu giao diện hoàn tất.
