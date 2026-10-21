# Rà soát độc lập

## Phạm vi

Đánh giá tính đúng, xử lý lỗi và khả năng nghiệm thu của mã quét tài liệu. Bộ kiểm thử độc lập nằm ở `tests/test_integration.py`. Các ảnh tổng hợp trong kiểm thử chỉ kiểm tra hợp đồng phần mềm, không được dùng làm kết quả thực nghiệm của đồ án.

## Ưu tiên kiểm tra

1. Điểm chạy `python -m src.main` và chạy từ Spyder phải dùng cùng pipeline, hoạt động khi thư mục làm việc khác thư mục dự án.
2. Ảnh hỏng, quá nhỏ, quá lớn, không có trang và bốn góc sai phải trả lỗi rõ ràng; không xuất ảnh quét như một kết quả thành công.
3. Đường dẫn tiếng Việt có dấu, ảnh xám và ảnh màu phải đọc/ghi đúng; lưu thất bại không được báo thành công.
4. Khi GUI xuất hiện, kiểm tra kết quả của tác vụ cũ đến muộn không ghi đè lên ảnh mới; đổi ảnh, góc hoặc chế độ phải vô hiệu hóa ảnh quét/OCR cũ và nút lưu tương ứng.
5. Quét/OCR dài không chặn vòng lặp giao diện; chỉ luồng chính cập nhật widget. Bấm liên tục không xếp hàng tác vụ nặng vô hạn.
6. Thử chuỗi 20 ảnh, tác vụ hủy, OCR thiếu cài đặt, ảnh hỏng và lưu lỗi; ứng dụng vẫn sẵn sàng cho lần xử lý tiếp theo.

## Trạng thái

Ngày 26/09/2026: đã chạy **17/17 kiểm thử đạt** bằng Python bundled của Codex với OpenCV cài tạm vào thư mục làm việc. Đã chạy lệnh quét toàn bộ trên ảnh demo tổng hợp, xem ảnh đầu ra và chụp giao diện tại 1200×760 và 880×600. `python`, `conda`, `tesseract` chưa có trên PATH của máy kiểm tra; cần chạy lại trong môi trường Anaconda theo `environment.yml` và kiểm tra OCR thực tế.

### Phát hiện cần sửa trước demo

- ✅ `ScannerApp._start_manual()` xóa ảnh quét/OCR cũ và tăng phiên bản ảnh; kiểm thử hồi quy đã đạt.
- ✅ Trong `ScannerApp._poll()`, nhánh quét thất bại xóa kết quả phụ thuộc. Bài thử lỗi ảnh thật vẫn còn cần thực hiện.
- ✅ `ScannerApp._change_mode()` chạy tăng cường ảnh trên luồng nền; bài thử luồng giao diện đã đạt. Cần đo độ phản hồi trên ảnh chụp lớn ở máy đích.
- ✅ `image_io.load_image()` đã kiểm tra dung lượng tệp và số điểm ảnh qua metadata Pillow trước khi giải mã; pipeline kiểm tra lại sau giải mã. Cần thử thêm ảnh chụp thật có EXIF xoay và ảnh lớn trên máy đích.

Lỗi import package của `src.pipeline` được phát hiện trong bản đầu và đã được nhóm sửa bằng relative imports trước khi chạy được kiểm thử thực tế.
