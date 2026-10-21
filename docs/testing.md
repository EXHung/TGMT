# Kế hoạch kiểm thử và ghi kết quả

**Trạng thái 21/10/2026:** 24/24 kiểm thử phần mềm đạt. Bộ dò tạo vùng quét trên 9/9 ảnh JPG thật đã khảo sát; hai ảnh bảng và màn chiếu dùng góc ước lượng vì thiếu góc thật trong khung hình. Đây là khả năng tạo vùng cắt, chưa phải phép đo độ chính xác bốn góc hoặc CER/WER. Các ảnh thật thuộc máy phát triển và không có trong repo công khai.

## Dữ liệu đầu vào

Thu thập ảnh thật với quyền sử dụng rõ ràng. Mỗi ảnh có một mã duy nhất, định dạng, kích thước, nguồn, điều kiện chụp và nhóm tình huống. Bộ tối thiểu cần đại diện cho: trang thẳng, xoay nhẹ, méo phối cảnh vừa, ảnh tối, ảnh sáng, bóng nhẹ, nền nhiều cạnh, giấy tương phản thấp, tài liệu tiếng Việt và tài liệu tiếng Anh. Một ảnh có thể thuộc nhiều nhóm. Cần có cả ảnh khó mà hệ thống được phép từ chối.

Tách ảnh **phát triển** dùng để chọn tham số và ảnh **đánh giá cuối** chưa dùng khi điều chỉnh, nếu số lượng ảnh cho phép. Không công bố tỷ lệ thành công nếu bộ ảnh quá ít; luôn ghi cả tử số, mẫu số và danh sách ảnh thất bại.

## Nhãn tham chiếu

Với ảnh nhìn thấy rõ bốn góc, ghi tọa độ pixel theo ảnh gốc và thứ tự: trên trái, trên phải, dưới phải, dưới trái. Nếu góc bị che hoặc không xác định được, đánh dấu **không có nhãn góc đáng tin cậy**; không tự suy đoán để lấp dữ liệu. Ghi văn bản chuẩn UTF-8 cho ảnh dùng đánh giá OCR; giữ dấu tiếng Việt. Bảng/cột cần ghi quy ước thứ tự đọc.

Mẫu dòng danh mục (chưa phải kết quả):

| Mã ảnh | Nhóm | Kích thước | Tập | Nhãn góc | Văn bản chuẩn | Ghi chú |
|---|---|---|---|---|---|---|
| _Điền khi có ảnh_ |  |  | phát triển/đánh giá | có/không | có/không |  |

## Đánh giá theo công đoạn

| Công đoạn | Cách đo hoặc kiểm tra | Cách ghi lỗi |
|---|---|---|
| Phát hiện trang | Số ảnh xác định đúng trang / số ảnh có trang đánh giá được; ghi riêng số ca từ chối | Vùng nền bị chọn làm trang, không có ứng viên, ứng viên sai |
| Bốn góc | Trung bình khoảng cách Euclid của bốn cặp góc cùng thứ tự, chia cho đường chéo ảnh gốc; chỉ tính ảnh có nhãn hợp lệ | Sai góc, sai thứ tự, tứ giác lõm, mép bị cắt |
| Chỉnh phối cảnh | Kiểm tra hướng chữ, bốn mép, chữ sát mép và tỷ lệ trang trên ảnh trước/sau | Lật, méo mạnh, thiếu vùng chữ |
| Tăng cường | So ảnh màu/xám/đen trắng ở cùng vùng chữ nhỏ, dấu và vùng nền; ghi chế độ phù hợp | Mất dấu, nét mảnh, màu chữ hoặc nền loang |
| OCR | CER = số phép sửa ký tự / số ký tự tham chiếu; WER tương tự theo từ, trên văn bản chuẩn đã thống nhất quy tắc khoảng trắng | Thiếu dấu, nhầm ký tự, sai thứ tự đọc, bỏ đoạn |
| Tốc độ | Thời gian phát hiện, chỉnh phối cảnh, tăng cường và OCR riêng; ghi CPU, RAM, kích thước ảnh | Chậm bất thường, GUI không phản hồi |

Không tính ảnh bị từ chối là thành công. Khi so OCR, dùng cùng bộ ảnh và cùng quy tắc chuẩn hóa Unicode, dấu câu, khoảng trắng cho mọi chế độ. Ghi cả văn bản gốc và văn bản nhận dạng để người đọc kiểm tra số CER/WER.

## Phiếu thử cho mỗi ảnh

Ghi mã ảnh, phiên bản mã, cấu hình tham số, ngày chạy, môi trường, trạng thái phát hiện, bốn góc dự đoán nếu có, chế độ ảnh, OCR engine/ngôn ngữ nếu dùng, thời gian từng bước, tên ảnh debug, đánh giá bằng mắt có lý do và lỗi cụ thể. Ảnh đầu ra nằm trong `images/output`; ảnh trung gian trong `images/debug/<mã ảnh>/`. Không sửa riêng tham số cho ảnh đánh giá cuối.

## Điều kiện hoàn tất M0

- Có ảnh thật đại diện cho các nhóm cốt lõi; nguồn và quyền dùng được ghi.
- Quy ước tên, thứ tự góc và văn bản chuẩn thống nhất.
- Tập phát triển và tập đánh giá cuối được chốt nếu dữ liệu đủ.
- Các tiêu chí trên được chấp nhận trước khi tinh chỉnh thuật toán.

## Kết quả kiểm thử phần mềm hiện có

Ngày 26/09/2026, **22/22 kiểm thử unit, ảnh tổng hợp và tích hợp đạt** khi chạy bằng `.venv` Python 3.12 của dự án. Bộ kiểm thử gồm `tests/test_scanner.py`, `tests/test_integration.py`, `tests/test_gui_flow.py` và `tests/test_ocr.py`. Các phép thử kiểm tra: phát hiện và chỉnh phối cảnh trên ảnh tổng hợp, quét với góc thủ công không theo thứ tự, từ chối góc sai/ảnh trống, đọc ghi đường dẫn Unicode, tên tệp dài, giới hạn tệp lớn trước giải mã, lỗi ghi tệp, lưu ảnh bằng luồng nền, GUI hiển thị góc tự phát hiện, không dùng lại góc thủ công cũ khi tự quét và không ép người dùng vào chế độ chọn tay sau lỗi, phương án dự phòng cho ảnh sáng, trạng thái GUI khi đổi chế độ và lỗi OCR qua đối tượng giả lập. Đây là kiểm thử chức năng phần mềm; không thể suy ra độ chính xác bốn góc, OCR hay thời gian xử lý trên ảnh chụp thật từ các phép thử này.

Chạy lại bằng `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` từ thư mục dự án. Môi trường `.venv` có NumPy 2.5.3, OpenCV headless 5.0.0.93, Pillow 12.3.0, pytesseract 0.3.13; `tools/tesseract` có Tesseract 5.5.3.20260724 và mô hình `eng`/`vie` từ tessdata_fast. OCR runtime đã được thử bằng CLI trên ảnh demo. Cần thử tiếp trên ảnh chụp thật có văn bản chuẩn trước khi báo cáo CER/WER.

## Lịch sử khảo sát 9 ảnh chụp thật

Lần thử đầu gồm **9 ảnh JPG**: 5 ảnh vở bị cắt mép, 2 ảnh vở mở hai trang, 1 ảnh màn chiếu có người che và 1 ảnh bảng lớp. Bản thuật toán đầu trả `manual_required` trên cả 9 ảnh trong **0,029–0,073 giây/ảnh**. Sau cập nhật tự căn góc, thuật toán tạo vùng trang trên **7/9 ảnh**; màn chiếu #374 và bảng lớp #521 tiếp tục bị từ chối. Thời gian của bản đầu không được gán cho bản thuật toán mới. Đây là nhóm ảnh khó hoặc ngoài giả định một trang phẳng có đủ viền của MVP. Không dùng 7/9 làm tỷ lệ phát hiện đúng trang trên tập đại diện; chưa có nhãn bốn góc đủ tin cậy để tính sai số góc.

| Mã ảnh | Đánh giá vùng tự động sau cập nhật |
|---|---|
| #426, #475, #497 | Tự tách trang vở bên phải; vùng cắt hữu ích theo rà soát trực quan. #426 còn chữ ở sát mép ngoài ảnh gốc nên không thể khôi phục phần bị mất |
| #350, #451 | Vùng cắt có điều kiện; cần xem lại trước khi dùng |
| #321, #401 | Chỉ ước lượng phần trang nhìn thấy do mất mép; không gọi là tìm đủ bốn góc thật hoặc quét toàn trang |
| #374, #521 | Từ chối phù hợp với nội dung màn chiếu/bảng lớp của bộ khảo sát |

Thuật toán có phương án `visible_page_estimate` cho vùng trang thấy được và `open_notebook_right_page` cho trang bên phải của vở mở; cả hai đều kiểm tra hình học bốn góc trước khi chỉnh phối cảnh. Nếu ứng viên contour có điểm quá thấp, thuật toán thử các phương án này trước khi từ chối. Hai tên này mô tả **ước lượng vùng cắt**, không xác nhận đã khôi phục phần giấy nằm ngoài ảnh. Xem ảnh overlay tại `images/debug/photo_audit/contact_sheet.jpg`; đánh giá trên chỉ là nhận xét trực quan, chưa phải nhãn chuẩn hay thước đo định lượng. Khi cần chạy lại khảo sát, đặt script tại `tests/evaluate_photos.py` và ghi rõ phiên bản mã, danh sách ảnh cùng cấu hình; không coi script là phép đo góc nếu chưa có nhãn chuẩn.

Trên ảnh vở đầu tiên, GUI đã quét được bằng **chọn bốn góc thủ công**. Bản màu và thang xám giữ được chữ trong quan sát trực quan; chế độ đen trắng của bản trước khi sửa làm đen một vùng bóng lớn. Sau thay đổi nhị phân hóa, AI Engineer kiểm tra ảnh #06: mảng tối che chữ đã biến mất, thời gian xử lý chế độ đen trắng khoảng **0,017 giây** cho ảnh này; ảnh so sánh được lưu tại `images/debug/photo_audit/bw_compare_06.jpg`. Đây là một ca kiểm tra, chưa chứng minh chế độ mới ổn định trên mọi điều kiện bóng và nét chữ. Với bản đã sửa, GUI mở lại ảnh #01, chọn góc, đổi sang Đen trắng và thấy vùng bóng không còn thành mảng đen; GUI lưu thành công `images/output/anh_that_01_den_trang.png` (139.304 byte) và báo đúng đường dẫn sau khi hoàn tất. Tên tệp dài được rút gọn trên phần đầu giao diện, vẫn giữ đuôi `.jpg`. OCR đã chạy trên ảnh demo tổng hợp, nhưng chưa đo CER/WER trên ảnh vở hoặc tài liệu chụp thật.

### Ưu tiên kiểm chứng tiếp theo

1. Thu thập ảnh **một tờ giấy phẳng, bốn mép nhìn rõ, nền tương phản, ánh sáng đủ**, chừa khoảng nền quanh trang và tránh vật che; tách tập chỉnh tham số và tập đánh giá cuối. Gắn nhãn góc trước khi kết luận về tự động phát hiện chính xác.
2. Chạy lại các ảnh có trang phù hợp sau thay đổi nhị phân hóa; so cùng vùng chữ và bóng giữa màu, xám, đen trắng. Giữ ảnh #06 làm ví dụ trước/sau, nhưng cần thêm ca bóng và chữ mảnh để kiểm tra khả năng tổng quát. Ghi phiên bản mã và tham số để tránh nhầm bản cũ với bản mới.
3. Computer Use đã mở GUI từ `run_scanner.cmd`, tự căn bốn góc ảnh demo và ảnh vở #426 mà không chọn góc thủ công, chạy OCR bằng nút **Nhận dạng chữ** và lưu văn bản UTF-8 từ giao diện. Trên ảnh demo, chữ in Việt/Anh đọc được nhưng còn sai dấu ở dòng ngày; trên ảnh vở #426, chữ viết tay sai nhiều. Cần thử thêm #497 và trường hợp tên tệp Unicode/trùng tên khi có bộ ảnh nghiệm thu.
4. Dùng bộ OCR đã cài trong dự án để thử ảnh chụp thật có văn bản chuẩn UTF-8; đo CER/WER riêng cho tiếng Việt, tiếng Anh và văn bản trộn. Đánh giá chữ viết tay riêng vì ảnh demo hiện chỉ có chữ in.

### Điều kiện nghiệm thu trên ảnh thật

- Có danh mục ảnh đủ điều kiện MVP và ảnh ngoài phạm vi, kèm nguồn, kích thước và nhãn khi gắn được; không trộn hai nhóm trong cùng mẫu số.
- Mỗi ảnh đủ điều kiện có trạng thái tự động, bốn góc dự đoán/nhãn, ảnh quét, thời gian và nguyên nhân lỗi; trường hợp từ chối được ghi riêng.
- Chế độ ảnh được so trên chữ nhỏ, dấu tiếng Việt và vùng bóng; bản đen trắng không làm mất vùng chữ quan trọng trên tập nghiệm thu.
- GUI lưu và mở lại được ảnh/văn bản đúng tên, đúng phiên bản đang xem; không để kết quả cũ được lưu như kết quả mới.
- OCR chạy với Tesseract thật và dữ liệu ngôn ngữ đã kiểm tra; CER/WER chỉ báo cáo sau khi có văn bản chuẩn.

**Kết luận hiện tại:** Tự căn góc là luồng chính; GUI không tự chuyển sang chọn góc tay khi phát hiện thất bại và nút tự căn không dùng lại bốn điểm thủ công cũ; bản mới tạo vùng trang trên 7 ảnh vở của bộ khảo sát và từ chối 2 ảnh không phải tài liệu. Một số vùng chỉ là phần trang nhìn thấy, chưa thể gọi là bốn góc chính xác hoặc toàn trang. Chọn góc thủ công vẫn là phương án cứu hộ tùy chọn. OCR chạy được trên ảnh demo chữ in Việt/Anh; chưa đủ bằng chứng để kết luận độ chính xác tự động hoặc chất lượng OCR trên ảnh tài liệu chụp thật.

## Kết quả ảnh demo tổng hợp

### OCR cục bộ trên ảnh demo

CLI đã quét và nhận dạng `images/input/demo_tong_hop_vi_en.png` bằng `.venv` và Tesseract 5.5.3.20260724 trong `tools/tesseract`, sử dụng mô hình `vie`/`eng` từ tessdata_fast. Văn bản UTF-8 lưu tại `images/output/demo_ocr_local.txt` chứa đúng “TÀI LIỆU MẪU”, “Đồ án Thị giác máy tính” và câu tiếng Anh của ảnh mẫu. Một số dấu tiếng Việt còn sai, ví dụ “nhận dang” thay vì “nhận dạng”. Đây là kiểm tra luồng OCR trên ảnh dựng, chưa tính CER/WER và không đại diện cho ảnh chụp thật hoặc chữ viết tay.

Ảnh `images/input/demo_tong_hop_vi_en.png` có kích thước 1350×1150 px, được tạo có chủ ý bằng `tests/generate_demo.py`; bốn góc chuẩn nằm trong `tests/data/demo_tong_hop_vi_en.json`. Ngày 26/09/2026, lệnh `python -m src.main --input images/input/demo_tong_hop_vi_en.png --mode gray --debug` đã tìm trang bằng cấu hình `clahe_closed`, lưu ảnh sau chỉnh phối cảnh và ảnh trung gian. Kiểm tra trực quan: trang được kéo thẳng và phần chữ trong ảnh mẫu còn nguyên. Sai số bốn góc trung bình **0,603 px**, lớn nhất **0,858 px** so với nhãn tổng hợp. Điểm đánh giá ứng viên 1,0 là điểm xếp hạng nội bộ, không phải xác suất đúng.

Đo 20 lượt quét cùng ảnh đã nạp vào bộ nhớ, không lưu debug, bằng Python 3.12 bundled với OpenCV tạm: trung vị **0,017 giây**, P95 theo nearest rank **0,019 giây**, lớn nhất **0,027 giây**. Cách đo: `python -m tests.benchmark_demo`. Các số này chỉ mô tả ảnh tổng hợp trên môi trường kiểm tra hiện tại; không suy ra tốc độ ảnh thật, OCR hay thời gian phản hồi toàn bộ giao diện. Khi có ảnh thật và máy đích, đo lại theo mục “Đánh giá theo công đoạn”.
