# Nâng cấp giao diện TGMT Scan Studio

Ngày thực hiện: 08/10/2026.

## Hướng thiết kế

Đã dùng công cụ UI UX Pro Max trong `D:\NEW\New folder\Tool-git\UX-UI` để tra cứu hệ thống thiết kế cho ứng dụng quét tài liệu trên máy tính, phản hồi tiến độ và chuyển động có thể tắt. Kết quả được điều chỉnh cho Tkinter: bố cục rõ thứ tự thao tác, nền xanh slate, màu xanh lam cho hành động chính và xanh ngọc cho góc trang/trạng thái thành công. Hai chủ đề sáng và tối dùng chung thứ bậc chữ và nút.

## Tương tác đã triển khai

- Thanh bốn bước từ nạp ảnh, tự căn và quét, nhận dạng chữ đến xuất kết quả.
- Hai vùng xem ảnh độc lập: phóng to bằng bánh xe hoặc nút, kéo bằng chuột phải, nhấp đúp hoặc bấm **Vừa khung** để khôi phục.
- Trên ảnh gốc, bốn góc tự nhận được vẽ bằng đường và điểm đánh số. Chỉnh góc thủ công chỉ là phương án sửa ngoại lệ.
- Nút có phản hồi khi rê chuột; thông báo nổi sau tác vụ; vệt quét ngắn sau khi xử lý ảnh; thanh tiến trình chỉ xuất hiện khi thực sự đang chạy.
- Tùy chọn **Hiệu ứng** tắt chuyển động; nút **Giao diện sáng/tối** đổi bảng màu.
- Trạng thái rỗng và trạng thái nút theo tiến trình giúp tránh thao tác chưa hợp lệ. Thông báo và nhãn đều viết bằng tiếng Việt.
- Phím tắt cho mở ảnh, quét, OCR, lưu và hủy; có thể tiếp tục dùng bàn phím để chọn nút.

## Giới hạn và kiểm tra

Kích thước cửa sổ tối thiểu là 920 × 720 pixel. Màn hình nhỏ hơn hoặc tỷ lệ thu phóng Windows cao có thể làm không đủ chỗ. Hiệu ứng được giữ ngắn để không kéo dài thời gian quét/OCR; vệt quét là phản hồi giao diện, không phản ánh chính xác thời gian xử lý thuật toán.

Đã thử trực tiếp bằng Computer Use: mở ảnh demo Việt/Anh, tự căn bốn góc và quét, chạy OCR, đổi chủ đề sáng/tối, quan sát trạng thái đang xử lý và kết quả. Sau sửa, OCR không bật cửa sổ dòng lệnh Tesseract. Bộ 22 kiểm thử hiện có và kiểm tra mở giao diện ở kích thước mặc định/tối thiểu đều đạt. Ảnh demo là ảnh tổng hợp; chất lượng nhận dạng trên ảnh chụp thật cần được đo riêng bằng văn bản chuẩn.
