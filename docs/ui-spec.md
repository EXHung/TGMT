# Đặc tả giao diện bản đầu

**Trạng thái:** Giao diện Tkinter mức đầu đã được triển khai trong `src/gui.py`. Bộ 17/17 kiểm thử unit, ảnh tổng hợp và tích hợp đạt trên môi trường tạm; chưa nghiệm thu thao tác trực quan trên máy đích, ảnh chụp thật hoặc chương trình Tesseract.

## Luồng sử dụng

1. Người dùng chọn một ảnh JPG hoặc PNG. Giao diện hiển thị ảnh gốc và xóa kết quả cũ.
2. Người dùng có thể đánh dấu **Lưu ảnh từng bước**, rồi chọn **Quét tài liệu**. Ứng dụng hiển thị trạng thái đang xử lý, rồi đưa ra ảnh quét hoặc lý do thất bại. Khi bật tùy chọn, mỗi lần quét lưu ảnh trung gian vào một thư mục riêng trong `images/debug`.
3. Nếu không xác định được bốn góc đáng tin cậy, giao diện đưa người dùng vào chế độ chọn lại bốn góc trên ảnh gốc. Người dùng cũng có thể bấm **Chọn lại bốn góc** chủ động. Sau khi chọn đủ bốn điểm, bấm **Quét tài liệu** lần nữa. Không hiển thị ảnh quét lỗi như kết quả thành công.
4. Người dùng chuyển giữa **Màu**, **Thang xám**, **Đen trắng** để xem bản phù hợp. Giá trị mặc định hiện tại là **Màu**; cần đánh giá trên ảnh thật trước khi đổi mặc định.
5. Người dùng chọn **Nhận dạng chữ**, xem và sao chép văn bản; sau đó lưu ảnh quét hoặc văn bản vào đường dẫn đã chọn.

## Bố cục

Giao diện hiện có nút **Chọn ảnh** ở đầu cửa sổ; ảnh gốc và ảnh quét đặt cạnh nhau. Cột bên phải chứa **Quét tài liệu**, **Chọn lại bốn góc**, chế độ ảnh, ô **Lưu ảnh từng bước**, ngôn ngữ OCR, **Nhận dạng chữ**, **Hủy xử lý**, vùng văn bản và các nút lưu/sao chép. Mỗi ảnh có nút **Vừa khung**; bánh xe chuột phóng to, chuột phải kéo ảnh khi đã phóng to. Thanh trạng thái và chỉ báo tiến trình ở dưới cùng. Các chức năng chưa thể dùng ở trạng thái hiện tại được vô hiệu hóa.

Quét, đổi chế độ ảnh và OCR được gửi tới tác vụ nền để vòng lặp giao diện tiếp tục phản hồi; chưa đo độ phản hồi trên ảnh lớn. Nút **Hủy xử lý** bỏ kết quả khi tác vụ trả về, không dừng cưỡng bức tác vụ nền. Hủy hộp thoại chọn hoặc lưu tệp không phải lỗi. Khi chọn ảnh mới, chọn lại góc hoặc đổi chế độ, kết quả OCR cũ bị xóa.

## Nhãn và thông báo tiếng Việt

| Tình huống | Nội dung hiển thị |
|---|---|
| Chưa chọn ảnh | “Hãy chọn ảnh tài liệu trước.” |
| Ảnh không đọc được | “Không đọc được ảnh. Hãy chọn tệp JPG hoặc PNG hợp lệ.” |
| Đang xử lý | “Đang tìm trang tài liệu…” / “Đang chỉnh phối cảnh…” / “Đang nhận dạng chữ…” |
| Không tìm được trang | “Chưa xác định được bốn góc trang. Hãy chọn bốn góc thủ công hoặc dùng ảnh khác.” |
| Đang chọn góc | “Chọn lần lượt bốn góc trang trên ảnh gốc, rồi chọn Quét tài liệu.” |
| OCR chưa sẵn sàng | “Không thể nhận dạng chữ. Hãy kiểm tra cài đặt Tesseract và dữ liệu ngôn ngữ.” |
| OCR không có chữ | “Không nhận dạng được chữ trong ảnh này. Bạn có thể thử chế độ ảnh khác.” |
| Lưu thành công | “Đã lưu ảnh quét tại: …” / “Đã lưu văn bản tại: …” |
| Lưu thất bại | “Không thể lưu tệp. Hãy chọn thư mục khác và thử lại.” |

Khi lỗi kỹ thuật có mã hoặc đường dẫn hữu ích, lưu chi tiết trong nhật ký để debug; thông báo chính dùng từ người dùng hiểu được. Không khẳng định đã lưu hoặc nhận dạng thành công trước khi tệp được ghi và kiểm tra.

## Kiểm tra nghiệm thu giao diện

- Thử chọn ảnh hợp lệ, tệp sai định dạng, ảnh bị hỏng và đường dẫn có dấu tiếng Việt.
- Thử hủy hộp thoại chọn/lưu tệp; dữ liệu hiện có không bị thay ngoài ý muốn.
- Thử quét thất bại, OCR lỗi/thiếu `vie`, văn bản rỗng và thao tác liên tiếp.
- Xác nhận kết quả cũ được xóa khi chọn ảnh mới và nút luôn phản ánh trạng thái hợp lệ.
- Kiểm tra ảnh gốc, ảnh quét và chữ ở kích thước cửa sổ nhỏ; không mất nút quan trọng.
