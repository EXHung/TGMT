# Dàn ý báo cáo đồ án

**Trạng thái:** Khung nội dung. Chỉ đưa hình, bảng và số liệu vào bản nộp khi đã tạo và kiểm tra từ mã thực tế.

## 1. Mở đầu

Nêu nhu cầu số hóa tài liệu bằng ảnh chụp, mục tiêu của đồ án, đầu vào/đầu ra và phạm vi một trang phẳng. Phân biệt mục tiêu của phần quét ảnh với mục tiêu nhận dạng chữ.

## 2. Bài toán và dữ liệu

Mô tả điều kiện ảnh bản đầu hỗ trợ, các trường hợp ngoài phạm vi, bộ ảnh thử và cách tạo nhãn bốn góc/văn bản chuẩn. Ghi số lượng ảnh, nguồn, quyền dùng và cách tách tập sau khi có dữ liệu thật.

## 3. Cơ sở lý thuyết

Chỉ trình bày kỹ thuật thực sự được dùng: ảnh xám và lọc nhiễu, Canny, contour và xấp xỉ đa giác, kiểm tra/sắp bốn góc, phép chiếu xạ phẳng, nội suy ảnh, tăng tương phản/ngưỡng và OCR. Với mỗi kỹ thuật, giải thích mục đích, nguyên lý hoặc công thức cần thiết, tham số, ưu điểm, hạn chế và trường hợp thất bại. Giải thích lý do chọn kỹ thuật thay vì liệt kê tên hàm.

## 4. Thiết kế hệ thống

Đưa sơ đồ khối từ ảnh đầu vào đến ảnh quét và văn bản. Mô tả trách nhiệm của từng module, dữ liệu trao đổi, cách lưu ảnh debug và cách trả trạng thái thất bại. Trình bày phương án dự phòng theo thứ tự tăng độ phức tạp.

## 5. Cài đặt

Ghi phiên bản môi trường, cấu hình tham số, cách chạy trong Spyder, định dạng đầu ra và đường dẫn lưu. Minh họa một ảnh qua các bước thật sự chạy: gốc, ảnh thu nhỏ, xám, lọc, biên, ứng viên, bốn góc, ảnh sau chỉnh phối cảnh, các chế độ tăng cường. Ghi rõ mọi tham số xuất hiện trong hình.

## 6. Phương pháp đánh giá

Nêu tập phát triển và tập đánh giá cuối, tiêu chí phát hiện đúng trang, sai số bốn góc chuẩn hóa, chất lượng chỉnh phối cảnh, độ rõ của chữ, CER/WER và thời gian từng bước. Nêu quy tắc xử lý ca không có nhãn hoặc OCR không chạy được. Không loại bỏ ca thất bại khỏi mẫu số mà không giải thích.

## 7. Kết quả thực nghiệm

Đưa bảng từng ảnh và bảng tổng hợp có tử số/mẫu số, cấu hình máy, phiên bản mã. Chọn ví dụ thành công, ví dụ thất bại và so sánh các chế độ ảnh trên cùng vùng chữ. Nếu so engine OCR, dùng cùng bộ ảnh và cùng phép chuẩn hóa văn bản. Mọi hình phải truy được về ảnh gốc và lần chạy.

## 8. Phân tích lỗi và giới hạn

Phân nhóm lỗi: chọn nhầm nền, thiếu biên, sai góc, lật/cắt ảnh, mất dấu khi nhị phân hóa, OCR sai ký tự hoặc thứ tự đọc, xử lý chậm. Phân tích nguyên nhân từ ảnh trung gian và quyết định sửa hoặc chấp nhận giới hạn. Nêu trường hợp cần chọn góc thủ công.

## 9. Kết luận và hướng phát triển

Đối chiếu kết quả với mục tiêu đã đặt bằng số liệu thật. Đề xuất các bước phù hợp tiếp theo, ví dụ cải thiện ảnh khó, giao diện chọn góc, nhiều trang hoặc xử lý tài liệu cong; không trình bày tính năng chưa làm như thành quả.

## Phụ lục

Hướng dẫn cài và chạy offline, danh sách tham số, danh mục ảnh, định nghĩa chỉ số, bảng lỗi chi tiết và nguồn tham khảo cho các thuật toán/thư viện. Dùng tên tệp, đường dẫn tương đối và ảnh chụp màn hình đủ rõ để người chấm có thể tái hiện.
