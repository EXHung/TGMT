# Nhật ký quyết định kỹ thuật

**Trạng thái:** Quyết định thiết kế và triển khai phiên bản đầu. Đã kiểm thử phần mềm trên ảnh tổng hợp; chưa có kết quả ảnh chụp thật hoặc OCR thực.

| Mã | Quyết định | Lý do | Điểm cần kiểm chứng |
|---|---|---|---|
| D01 | Bản đầu xử lý một trang phẳng, có biên nhìn thấy tương đối rõ | Giữ bài toán đủ hẹp để kiểm tra phát hiện, bốn góc và phép chiếu xạ | Tỷ lệ phát hiện đúng trên ảnh MVP |
| D02 | Dò trang trên ảnh thu nhỏ, chỉnh phối cảnh trên ảnh gốc | Giảm thời gian dò mà vẫn giữ độ phân giải đầu ra | Tọa độ quy đổi chính xác, thời gian và chất lượng ảnh |
| D03 | Thử Canny → nhiều contour ứng viên → `approxPolyDP` làm phương pháp chính | Dễ quan sát, giải thích và phù hợp trang có viền rõ | Ảnh nền phức tạp, biên yếu và mép sát rìa |
| D04 | Kiểm tra tứ giác lồi, diện tích, thứ tự góc trước khi `warpPerspective` | Tránh lật, cắt và kéo giãn do điểm sai | Ca bốn góc sai hoặc gần trùng nhau bị từ chối |
| D05 | Thử ba cấu hình biên có giới hạn: Canny, Canny + phép đóng, CLAHE + Canny + phép đóng; nếu thiếu góc thì yêu cầu chọn tay | Giảm nguy cơ biến vùng nền thành ảnh quét có vẻ hợp lệ; `minAreaRect` chưa dùng vì chưa có ảnh thật chứng minh giá trị | Tỷ lệ từ chối đúng và ảnh khó được cứu |
| D06 | Giữ ảnh màu và xám; thử đen trắng theo từng loại tài liệu | Ngưỡng có thể xóa dấu tiếng Việt và chữ mảnh | So sánh vùng chữ và CER sau M5 |
| D07 | Tách OCR khỏi pipeline quét; thử Tesseract qua `pytesseract` đầu tiên | Chạy cục bộ, dễ thay engine, hỗ trợ dữ liệu ngôn ngữ riêng | Cài đặt `vie`/`eng`, độ chính xác và thời gian CPU trên dữ liệu thật |
| D08 | GUI Tkinter gọi pipeline trên luồng nền và làm mới kết quả theo trạng thái ảnh | Giao diện vẫn phản hồi khi quét; không lưu ảnh/chữ cũ sau khi đổi ảnh, góc hoặc chế độ | Thao tác liên tục, hủy tác vụ, lỗi OCR, phản hồi trên ảnh lớn |

## Quy tắc cập nhật

Với mỗi thay đổi, ghi ngày, phiên bản mã, quyết định cũ/mới, ảnh hoặc phép đo làm bằng chứng, tác động lên ảnh khó và ảnh thường. Nếu một phương pháp chỉ cải thiện một ảnh nhưng làm hỏng các ảnh khác, không đổi mặc định mà chưa đánh giá trên tập phát triển. Không viết kết luận hiệu năng khi chưa có kết quả.

## Mẫu quyết định mới

**Mã/ngày:**  
**Vấn đề quan sát:**  
**Các lựa chọn:**  
**Bằng chứng (mã ảnh, cấu hình, số đo):**  
**Quyết định và lý do:**  
**Rủi ro còn lại:**  
