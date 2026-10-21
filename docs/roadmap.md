# Lộ trình phát triển đồ án quét tài liệu bằng thị giác máy tính

**Thư mục dự án:** Thư mục gốc của repo `TGMT`.  
**Trạng thái 21/10/2026:** Lõi quét tạo vùng cắt trên 9/9 ảnh JPG thật đã khảo sát, gồm 2 vùng bảng/màn chiếu được ước lượng; 24/24 kiểm thử phần mềm đạt. Chưa có tập ảnh với nhãn góc và văn bản chuẩn để đo độ chính xác/CER/WER. Các mốc và số liệu cũ bên dưới là lịch sử phát triển.  
**Môi trường mục tiêu:** Python, OpenCV, NumPy, Anaconda, Spyder; OCR tích hợp sau khi lõi quét ổn định.

## 1. Mục tiêu và bài toán

Ứng dụng nhận một ảnh chụp có tờ tài liệu, xác định vùng trang và bốn góc, biến đổi phối cảnh để tạo ảnh nhìn thẳng, tăng khả năng đọc, rồi nhận dạng và xuất văn bản. Đầu ra cuối gồm ảnh quét và tệp văn bản. Đồ án cần thể hiện rõ các bước thị giác máy tính, ảnh trung gian, phương pháp đánh giá và giới hạn thực tế.

Các bài toán tách biệt:

1. **Phát hiện trang:** phân biệt biên trang với cạnh bàn, bóng, khung ảnh và vật thể nền.
2. **Ước lượng bốn góc:** tạo một tứ giác đúng, lồi và có thứ tự nhất quán.
3. **Chỉnh phối cảnh:** ánh xạ tứ giác về hình chữ nhật mà không lật, cắt chữ hay kéo giãn sai.
4. **Cải thiện ảnh:** tăng độ đọc được mà vẫn giữ dấu tiếng Việt và nét chữ mảnh.
5. **OCR:** chọn ảnh đầu vào phù hợp, nhận dạng tiếng Việt/Anh và đo sai số thật.
6. **Xử lý thất bại:** nhận biết khi kết quả không đáng tin cậy thay vì âm thầm xuất bản scan sai.

## 2. Phạm vi

### MVP bắt buộc

- Một ảnh chứa một trang tài liệu phẳng, gần hình chữ nhật.
- Hầu hết đường viền trang nằm trong ảnh và tương đối nhìn thấy được.
- Độ nghiêng phối cảnh vừa phải; ảnh đủ nét; ánh sáng tương đối đều.
- Tự phát hiện trang và bốn góc, chỉnh phối cảnh trên ảnh gốc.
- Xuất ít nhất ảnh màu và ảnh xám; bổ sung ảnh đen trắng sau khi so sánh chất lượng.
- Lưu ảnh trung gian có thể kiểm tra trong Spyder.
- Khi không tìm được trang đáng tin cậy, trả trạng thái và lý do rõ ràng.

### Tăng độ bền sau MVP

- Thử các cấu hình tiền xử lý có kiểm soát và xét nhiều contour ứng viên.
- Xử lý tương phản thấp, bóng nhẹ, nền nhiều cạnh và trang sát mép ảnh.
- Chọn bốn góc thủ công khi tự động thất bại.
- OCR Việt/Anh và đánh giá bằng văn bản chuẩn.

### Ngoài phạm vi phiên bản đầu

Giấy cong hoặc gấp mạnh, nhiều trang trong một ảnh, mép bị che khuất đáng kể, ảnh quá mờ, bóng đổ nặng, phản quang mạnh, văn bản viết tay, tự sửa biến dạng phi phẳng, quét thời gian thực và mô hình học sâu phát hiện tài liệu.

## 3. Cấu trúc dự án

```text
D:\Study\TGMT\
├── docs\
│   ├── roadmap.md             # Tài liệu này
│   ├── decisions.md           # Lý do chọn thuật toán và tham số; tạo khi triển khai
│   ├── testing.md             # Danh mục ảnh, nhãn và kết quả đo; tạo ở M0
│   └── report-outline.md      # Dàn ý báo cáo; tạo khi chuẩn bị báo cáo
├── images\
│   ├── input\                # Ảnh do nhóm thu thập; không tự tạo kết quả giả
│   ├── debug\                # Ảnh trung gian theo từng ảnh đầu vào
│   └── output\               # Ảnh quét và văn bản OCR
├── src\                      # Các module Python; bắt đầu tạo từ M1
├── tests\
│   └── data\                 # Dữ liệu/nhãn kiểm thử, khi được cung cấp
├── README.md                 # Hướng dẫn chạy trong Spyder; tạo khi có bản chạy được
└── environment.yml           # Môi trường Anaconda; tạo khi chốt phụ thuộc
```

Các module dự kiến trong `src`: `main.py` là điểm chạy, `config.py` quản lý tham số, `document_detector.py` tìm ứng viên/bốn góc, `perspective.py` biến đổi phối cảnh, `enhancement.py` tạo các chế độ ảnh, `ocr_engine.py` nhận dạng chữ, `debug_utils.py` lưu ảnh trung gian. Thiết kế giao diện và trạng thái được chốt trên giấy từ M0; chỉ lập trình giao diện ở M6. Mỗi module có chức năng nhỏ, dễ chạy từng bước trong Spyder; đường dẫn đầu vào và đầu ra được cấu hình tập trung.

Khi triển khai, bổ sung `image_io.py` cho đọc/ghi ảnh và đường dẫn Unicode; `pipeline.py` điều phối các bước mà không phụ thuộc giao diện. Giao diện và Spyder dùng chung pipeline. `gui.py` quản lý hiển thị và thao tác, không chứa thuật toán xử lý ảnh. Tài liệu thiết kế giao diện có thể tách thành `docs/ui-spec.md` khi triển khai; đặc tả ban đầu nằm ở mục 11–12 của tài liệu này.

Thư mục `images/debug` tổ chức theo tên ảnh và mã lần chạy để tránh ghi đè khi chạy lại hoặc gặp tên ảnh trùng nhau. Tên bước dự kiến: `01_original`, `02_resized`, `03_gray`, `04_blur`, `05_edges`, `06_candidates`, `07_corners`, `08_warped`, `09_enhanced`. Chỉ lưu những bước thật sự dùng trong lần chạy; tên và tham số sẽ được ghi lại. Cho phép tắt lưu ảnh trung gian khi đo hiệu năng; báo cáo phải nêu chế độ này.

## 4. Pipeline kỹ thuật đề xuất

| Bước | Lý do và vị trí | Tham số quan trọng | Rủi ro và cách kiểm tra |
|---|---|---|---|
| Đọc ảnh, kiểm tra kích thước/định dạng | Loại đầu vào lỗi trước xử lý; giữ ảnh gốc để xuất chất lượng cao | Độ phân giải tối thiểu, chiều ảnh | Ảnh không đọc được, quá nhỏ hoặc xoay theo metadata |
| Thu nhỏ giữ tỷ lệ | Giảm thời gian dò biên; ghi hệ số để quy điểm về ảnh gốc | Cạnh dài mục tiêu | Quên quy đổi tọa độ sẽ làm sai vùng quét |
| Grayscale và Gaussian blur nhẹ | Giảm nhiễu trước Canny mà không tăng chi phí lớn | Kích thước kernel, độ lệch chuẩn | Lọc quá mạnh làm mất viền mảnh |
| Canny | Tạo bản đồ cạnh dễ quan sát, phù hợp trang có viền rõ | Hai ngưỡng Canny | Viền đứt do tương phản thấp; cạnh nền quá mạnh |
| Morphology nhẹ khi cần | Nối đoạn biên đứt ngắn | Kernel, số vòng lặp | Nối nhầm cạnh nền với trang; không bật mặc định mọi ảnh |
| `findContours` và lọc ứng viên | Xét nhiều đường viền thay vì lấy contour lớn nhất | Diện tích tối thiểu, số ứng viên | Bàn hoặc khung ảnh có thể lớn hơn trang |
| `approxPolyDP` và kiểm tra tứ giác | Tìm bốn góc dễ giải thích trong báo cáo | Sai số theo chu vi, độ lồi, diện tích | Cho 3/5 góc, góc giả hoặc tứ giác lõm |
| Sắp xếp và kiểm tra bốn góc | Bảo đảm thứ tự trên-trái, trên-phải, dưới-phải, dưới-trái và hình học hợp lệ | Diện tích, tỷ lệ cạnh, khoảng cách điểm | Lật ảnh hoặc biến dạng khi điểm trùng/sai thứ tự |
| `getPerspectiveTransform` và `warpPerspective` | Đưa mặt phẳng trang về hình chữ nhật | Kích thước đích, nội suy | Cắt chữ, tỷ lệ trang không hợp lý; thực hiện trên ảnh gốc |
| Tạo chế độ màu/xám/đen trắng | Phục vụ nhiều loại tài liệu | Otsu; adaptive khi nền không đều; CLAHE khi cần | Nhị phân hóa có thể xóa dấu, chữ mảnh hoặc chữ màu |
| OCR sau khi lõi quét ổn định | Xuất văn bản nhưng vẫn thay được engine | Ngôn ngữ, chế độ phân trang, loại ảnh đầu vào | Sai dấu tiếng Việt, chữ nhỏ, cột/bảng phức tạp |

Phương pháp chính là Canny + contour + `approxPolyDP`: đơn giản, có ảnh trung gian để giải thích và phù hợp giả định MVP. Không cố định `minAreaRect` làm kết quả chính vì hình chữ nhật bao quanh có thể không khớp bốn góc thực của trang nghiêng phối cảnh. Hough line chỉ cân nhắc nếu tập thử chứng minh lỗi biên đứt thường xuyên và fallback đơn giản không đủ.

## 5. Fallback và xử lý lỗi

1. **Không có contour hợp lệ:** lưu bản đồ cạnh, thử một vài cấu hình ngưỡng/độ tương phản đã định trước; không tăng tham số ngẫu nhiên cho từng ảnh.
2. **Có nhiều ứng viên:** xếp hạng theo diện tích tương đối, độ lồi, chất lượng tứ giác và vị trí; kiểm tra ứng viên tiếp theo nếu ứng viên đầu không hợp lệ.
3. **Không có đúng bốn góc:** thử sai số xấp xỉ trong dải giới hạn; `minAreaRect` chỉ là gợi ý và phải qua kiểm tra hình học. Không tự coi hình chữ nhật bao là trang chắc chắn.
4. **Biên yếu hoặc nền rối:** thử CLAHE/morphology nhẹ có ghi lại cấu hình đã dùng. Đánh giá liệu cải thiện trên cả tập thử hay chỉ một ảnh.
5. **Tự động không đủ tin cậy:** cho chọn tay bốn điểm ở giai đoạn tăng độ bền. Nếu chưa có GUI, giao diện chọn bằng OpenCV hoặc cách nhập tọa độ đơn giản có thể dùng cho thử nghiệm.
6. **Vẫn thất bại:** trả trạng thái, lý do và ảnh gốc; không lưu bản scan như một kết quả thành công.

Trước mọi phép warp, xác nhận bốn điểm khác nhau, tứ giác lồi, diện tích không quá nhỏ, các cạnh/đường chéo hợp lý và tọa độ nằm trong ảnh. Nếu phép kiểm tra thất bại, dừng bước đó và ghi nguyên nhân để debug.

## 6. Roadmap theo milestone

### M0 — Chốt dữ liệu, tiêu chí và môi trường

- **Mục tiêu:** tạo bộ ảnh thử nhỏ, nhất quán; chốt phạm vi và thước đo trước khi điều chỉnh thuật toán.
- **Kiến thức CV:** nhãn tọa độ, độ phân giải, ảnh tham chiếu và sai số đo.
- **Thuật toán:** chưa triển khai xử lý; chuẩn hóa quy ước bốn góc và cách ghi văn bản chuẩn.
- **Đầu vào:** ảnh thật do nhóm chụp/cung cấp, yêu cầu môn học, phiên bản Python/Anaconda trên máy dùng chạy.
- **Đầu ra:** danh mục ảnh theo nhóm tình huống, nhãn bốn góc khi có thể, văn bản chuẩn cho ảnh OCR, quy tắc đặt tên.
- **Tệp:** `docs/testing.md`, `docs/decisions.md`, `environment.yml` khi xác nhận phụ thuộc.
- **Kiểm thử:** mở được mọi ảnh; nhãn góc theo một thứ tự; văn bản chuẩn giữ Unicode tiếng Việt.
- **Lỗi có thể gặp:** ảnh quá nhỏ/mờ, nhãn không nhất quán, chưa có quyền dùng ảnh, dữ liệu quá ít hoặc chỉ có ảnh dễ.
- **Hoàn tất khi:** có đủ nhóm ảnh cốt lõi và tiêu chí đo rõ; chưa tuyên bố hiệu năng nào.

### M1 — Phát hiện trang và bốn góc

- **Mục tiêu:** trả tứ giác của trang trên các ảnh MVP; ảnh debug cho từng bước.
- **Kiến thức CV:** grayscale, lọc nhiễu, biên, contour, chu vi, diện tích, xấp xỉ đa giác.
- **Thuật toán:** resize giữ tỷ lệ → Gaussian blur → Canny → tìm nhiều contour → `approxPolyDP` → kiểm tra tứ giác.
- **Đầu vào:** ảnh chụp một trang từ `images/input`.
- **Đầu ra:** bốn góc theo quy ước, điểm đánh giá ứng viên và lý do lựa chọn, hoặc trạng thái thất bại. Điểm đánh giá không được hiển thị như xác suất chính xác khi chưa được hiệu chuẩn.
- **Tệp:** `src/document_detector.py`, `src/config.py`, `src/debug_utils.py`, các ảnh trong `images/debug`.
- **Kiểm thử:** ảnh thẳng, xoay nhẹ, nghiêng vừa; so góc dự đoán với nhãn, xem ảnh contour/corners.
- **Lỗi có thể gặp:** contour bàn lớn hơn trang, cạnh đứt, trang cùng màu nền, tứ giác bị lõm hoặc sai góc.
- **Hoàn tất khi:** tập MVP có kết quả hợp lệ và các trường hợp không phát hiện được được ghi nhận rõ; không phụ thuộc vào thao tác sửa riêng từng ảnh.

### M2 — Chỉnh phối cảnh

- **Mục tiêu:** tạo ảnh trang nhìn thẳng ở độ phân giải phù hợp từ bốn góc hợp lệ.
- **Kiến thức CV:** thứ tự điểm, phép biến đổi phối cảnh giữa hai mặt phẳng (homography), nội suy ảnh.
- **Thuật toán:** quy tọa độ về ảnh gốc → sắp bốn góc → xác định kích thước đích → `getPerspectiveTransform` → `warpPerspective`.
- **Đầu vào:** ảnh gốc và bốn góc từ M1 hoặc nhãn kiểm thử.
- **Đầu ra:** ảnh trang đã chỉnh phối cảnh.
- **Tệp:** `src/perspective.py`, bản chạy điều phối tối giản trong `src/main.py`.
- **Kiểm thử:** góc nghiêng trái/phải, xoay 90/180 độ nếu thuộc dữ liệu; kiểm tra chữ không lật, mép không bị cắt, tỷ lệ không kỳ lạ.
- **Lỗi có thể gặp:** thứ tự góc sai, chiều rộng/cao bằng 0, sai tỷ lệ do ảnh resize, kéo giãn mạnh.
- **Hoàn tất khi:** các ảnh MVP cho kết quả đúng hướng và biên trang hợp lý; đầu vào góc sai bị từ chối.

### M3 — Tăng cường ảnh và xuất ảnh

- **Mục tiêu:** tạo bản scan phù hợp tài liệu màu, chữ thông thường và trang có nền không đều nhẹ.
- **Kiến thức CV:** mức xám, histogram, ngưỡng toàn cục và cục bộ, tương phản.
- **Thuật toán:** giữ màu; grayscale; Otsu cho nền tương đối đều; thử adaptive threshold hoặc CLAHE khi có bằng chứng cần thiết.
- **Đầu vào:** ảnh sau M2.
- **Đầu ra:** ảnh màu, xám, đen trắng; lựa chọn một chế độ mặc định dựa trên thử nghiệm.
- **Tệp:** `src/enhancement.py`, `images/output`.
- **Kiểm thử:** chữ mảnh, dấu tiếng Việt, dấu mực màu, vùng bóng nhẹ; so trực quan có tiêu chí và chuẩn bị so CER khi có OCR.
- **Lỗi có thể gặp:** mất nét, mất dấu, nền loang, chữ màu biến mất sau nhị phân hóa.
- **Hoàn tất khi:** ba chế độ có ích rõ ràng, tham số tập trung và ảnh đầu ra lưu được đúng định dạng.

### M4 — Độ bền, fallback và đánh giá phần quét

- **Mục tiêu:** xử lý hợp lý các ca khó vừa phải và xác định giới hạn tự động.
- **Kiến thức CV:** so sánh phương pháp tiền xử lý, chấm contour, đánh giá sai số góc.
- **Thuật toán:** dải cấu hình tiền xử lý giới hạn, nhiều contour, `minAreaRect` có kiểm tra, chọn tay bốn góc khi cần.
- **Đầu vào:** ảnh tối/sáng, nền rối, trang sát mép, bóng nhẹ, tương phản thấp.
- **Đầu ra:** kết quả hợp lệ hoặc thông báo cần can thiệp; bảng thử nghiệm có nguyên nhân lỗi.
- **Tệp:** cập nhật detector/debug; `docs/testing.md`, `docs/decisions.md`.
- **Kiểm thử:** tỷ lệ phát hiện đúng, tỷ lệ từ chối đúng, sai số góc chuẩn hóa theo kích thước ảnh, thời gian xử lý.
- **Lỗi có thể gặp:** fallback chọn nhầm vùng nhưng ảnh vẫn trông đẹp; quá nhiều cấu hình làm thời gian tăng.
- **Hoàn tất khi:** không âm thầm trả bản scan sai cho ca chưa chắc chắn và các ngưỡng được chốt từ tập thử thay vì từng ảnh.

### M5 — OCR Việt/Anh

- **Mục tiêu:** xuất văn bản có thể đọc/sửa từ ảnh quét.
- **Kiến thức CV/OCR:** ảnh đầu vào cho OCR, phân vùng trang, lỗi ký tự và lỗi từ.
- **Thuật toán:** thử Pytesseract với dữ liệu `vie`/`eng` trước; so với EasyOCR nếu kết quả hoặc cài đặt thực tế cho thấy cần thay. OCR độc lập khỏi scanner.
- **Đầu vào:** ảnh màu/xám/đen trắng từ M3; văn bản chuẩn từ M0.
- **Đầu ra:** văn bản Unicode `.txt`, thông tin engine và cấu hình đã dùng.
- **Tệp:** `src/ocr_engine.py`, `images/output`, cập nhật `environment.yml` và hướng dẫn cài đặt.
- **Kiểm thử:** văn bản Việt/Anh riêng và trộn, CER/WER trên cùng ảnh đầu vào, thời gian CPU; giữ nguyên dấu để tính lỗi.
- **Lỗi có thể gặp:** thiếu gói ngôn ngữ, sai phân trang, chữ nhỏ, dấu bị mất do threshold, bảng/cột đọc sai thứ tự.
- **Hoàn tất khi:** chạy được hai ngôn ngữ ở mức khả dụng và có số đo thật; không tuyên bố OCR hoàn hảo.

### M6 — Giao diện gọn, rõ và phản hồi tốt

- **Mục tiêu:** thao tác được toàn bộ luồng mà không cần sửa mã để đổi ảnh.
- **Kiến thức:** giao diện và xử lý trạng thái; phần CV đã hoàn thành trước.
- **Thuật toán:** không thêm thuật toán CV mới; gọi các module đã kiểm thử.
- **Đầu vào:** ảnh do người dùng chọn và chế độ scan/OCR.
- **Đầu ra:** xem ảnh gốc, ảnh scan, văn bản; lưu kết quả.
- **Tệp:** `src/gui.py`, cập nhật `README.md`.
- **Kiểm thử:** chọn ảnh hợp lệ/không hợp lệ, lỗi OCR, hủy chọn tệp, lưu tệp, chọn góc; thực hiện đầy đủ bảng nghiệm thu tại mục 13.
- **Lỗi có thể gặp:** giao diện đứng khi OCR chạy, trạng thái cũ còn hiển thị sau lỗi, đường dẫn có Unicode.
- **Hoàn tất khi:** luồng thao tác cơ bản ổn định, đạt tiêu chí phản hồi và hiển thị tại mục 11–13, thông báo tiếng Việt rõ ràng, không hiển thị kết quả cũ như kết quả của ảnh mới.

### M7 — Báo cáo, demo và đóng gói

- **Mục tiêu:** trình bày đầy đủ cơ sở kỹ thuật, quá trình thử và hạn chế.
- **Kiến thức CV:** giải thích các bước đã thực sự dùng và phép biến đổi phối cảnh.
- **Thuật toán:** tổng hợp quyết định; không thêm kỹ thuật chỉ để báo cáo dài hơn.
- **Đầu vào:** mã đã chạy, ảnh debug, bảng kết quả và nhật ký quyết định.
- **Đầu ra:** dàn ý/bản báo cáo, sơ đồ khối, ảnh trước/sau, hướng dẫn demo Spyder.
- **Tệp:** `docs/report-outline.md`, `README.md`, hoàn thiện `docs/testing.md`.
- **Kiểm thử:** cài đặt lại theo README, chạy demo bằng ảnh chưa dùng khi chỉnh tham số, kiểm tra số liệu khớp log.
- **Lỗi có thể gặp:** hình minh họa không khớp bản mã cuối, số liệu thiếu nguồn, phụ thuộc cài đặt không tái tạo được.
- **Hoàn tất khi:** người khác làm theo hướng dẫn và tạo được kết quả; báo cáo mô tả đúng cả ưu điểm lẫn giới hạn.

## 7. Bộ kiểm thử và cách đo

Bộ ảnh tối thiểu cần có các nhóm: trang thẳng, xoay nhẹ, méo phối cảnh, ảnh tối, ảnh sáng, bóng trên trang, nền phức tạp, giấy tương phản thấp, tài liệu Việt và tài liệu Anh. Một ảnh có thể thuộc nhiều nhóm, nhưng mỗi nhóm cần được ghi rõ và có ít nhất một trường hợp đại diện. Tách ảnh dùng để điều chỉnh tham số khỏi ảnh kiểm tra cuối nếu số lượng cho phép.

| Hạng mục | Cách đánh giá | Lưu ý |
|---|---|---|
| Phát hiện trang | Đúng/sai trên từng ảnh; đếm ca từ chối thay vì bỏ qua | Không tính vùng nền được crop đẹp là đúng |
| Bốn góc | Khoảng cách giữa góc dự đoán và góc nhãn, chuẩn hóa theo đường chéo ảnh | Ghi rõ thứ tự và ảnh có/không có nhãn |
| Chỉnh phối cảnh | Cạnh trang, chiều chữ, vùng chữ bị cắt; có thể đối chiếu vùng nhãn | Ảnh mẫu trước/sau kèm nhận xét cụ thể |
| Độ đọc | So màu/xám/đen trắng trên chữ nhỏ, dấu và nền | Không mặc định ảnh đen trắng tốt nhất |
| OCR | CER và WER với văn bản chuẩn tiếng Việt/Anh | Dùng cùng tập ảnh và cùng quy tắc chuẩn hóa văn bản |
| Tốc độ | Thời gian phát hiện, warp, tăng cường và OCR riêng | Ghi cấu hình máy/CPU khi báo cáo |

Phân biệt mục tiêu nghiệm thu với kết quả đã đo. M0 phải chốt ngưỡng phát hiện đúng, sai số góc, CER/WER và thời gian trên cấu hình máy cụ thể trước khi điều chỉnh thuật toán; ghi mẫu số và nhóm ảnh áp dụng. Giữ riêng tập kiểm tra cuối, không điều chỉnh ngưỡng theo kết quả của tập đó. Nếu đổi mục tiêu, ghi lý do và phiên bản. Các ngưỡng phản hồi giao diện đề xuất tại mục 13 cũng là mục tiêu cần kiểm chứng. Mỗi mốc chỉ qua khi có đầu ra, cách tái hiện, kết quả kiểm thử và lỗi còn lại được ghi lại.

## 8. Tài liệu và báo cáo

Với mỗi kỹ thuật thực sự dùng, ghi: mục đích, nguyên lý, ý tưởng toán học khi cần, vị trí trong pipeline, tham số, ưu điểm, hạn chế và trường hợp thất bại. Báo cáo cuối dự kiến gồm: giới thiệu và phạm vi; cơ sở lý thuyết; kiến trúc/sơ đồ khối; thiết kế và cài đặt; dữ liệu và thước đo; kết quả thực nghiệm có ảnh từng bước; phân tích lỗi; kết luận và hướng phát triển; phụ lục cách chạy/tham số.

Ba vai trò được dùng ở các mốc: **AI Engineer** thiết kế và triển khai pipeline/đánh giá; **Code Reviewer** kiểm tra tính đúng, xử lý lỗi và bằng chứng kiểm thử; **Technical Writer** giữ tài liệu và báo cáo nhất quán với kết quả thực. Không dùng số liệu hoặc ảnh kết quả chưa thực sự tạo ra.

## 9. Thứ tự và điều kiện bắt đầu

Thứ tự ưu tiên: **lõi quét đơn giản, ổn định → đánh giá và tăng độ bền → OCR → GUI → báo cáo/demo**. Người dùng đã yêu cầu thực hiện roadmap; trạng thái thực tế của từng mốc được ghi tại mục 14.

## 10. Kết quả rà soát thiết kế phiên bản 1.1

Mục này ghi lại các thiếu sót được tìm thấy khi rà soát bản thiết kế 1.1. Kết quả triển khai và kiểm thử sau đó được cập nhật ở mục 14; chất lượng trên ảnh chụp thật chưa được xác nhận.

| Thiếu sót của bản đầu | Điều chỉnh | Mốc chịu trách nhiệm |
|---|---|---|
| “Mượt” chưa có thước đo | Bổ sung mục tiêu độ phản hồi, tác vụ nền, bài thử liên tiếp | M0 chốt máy đo; M6 kiểm chứng |
| Giao diện chưa có bố cục và quy chuẩn | Đặc tả bố cục, kiểu chữ, màu, trạng thái, phóng to ảnh | M0 duyệt thiết kế; M6 hiện thực |
| Chưa xử lý kết quả đến muộn | Mã tác vụ, phiên bản ảnh/tham số và quy tắc vô hiệu hóa kết quả cũ | M2 thiết kế dữ liệu; M6 tích hợp |
| Đọc/ghi ảnh và dữ liệu OCR chưa đủ rõ | Unicode, hướng ảnh, giới hạn kích thước, lưu an toàn, thiếu OCR vẫn quét được | M0/M3/M5 |
| Ngưỡng nghiệm thu chưa có hạn chốt | Chốt tại M0 trước điều chỉnh; lưu tập kiểm tra cuối riêng | M0/M4/M7 |
| Thuật ngữ kỹ thuật lẫn vào giao diện | Bộ nhãn và thông báo tiếng Việt thống nhất | M6/M7 |

## 11. Thiết kế giao diện và độ phản hồi

### Bố cục và hình thức

- Thanh trên: tên ứng dụng **Quét tài liệu**, nút **Chọn ảnh**, tên ảnh đang mở.
- Vùng trung tâm dành phần lớn diện tích cho ảnh. Hai thẻ **Ảnh gốc** và **Ảnh quét** dùng chung khung xem; thêm chế độ **So sánh** đặt hai ảnh cạnh nhau khi cửa sổ đủ rộng.
- Bảng thao tác bên phải: **Điều chỉnh góc** → **Quét tài liệu** → chọn chế độ **Màu / Thang xám / Đen trắng** → **Nhận dạng chữ** → các nút lưu. Vùng **Văn bản nhận dạng** có thể chỉnh sửa và sao chép.
- Thanh dưới hiển thị trạng thái và bước đang xử lý. Không hiển thị phần trăm giả; nếu không đo được tiến độ, dùng chỉ báo đang hoạt động và tên bước.
- Nền sáng trung tính, màu nhấn xanh, một kiểu chữ hỗ trợ đầy đủ tiếng Việt như Segoe UI; cỡ chữ nội dung mục tiêu 11–12 pt. Khoảng cách theo các mức 8/16/24 px, chiều cao nút mục tiêu từ 36 px trước quy đổi DPI. Không dùng biểu tượng làm nhãn duy nhất.
- Chỉ một hành động chính được nhấn mạnh ở mỗi trạng thái. Lỗi có chữ giải thích và hướng khắc phục, không chỉ đổi màu đỏ.
- Ảnh giữ đúng tỷ lệ, hỗ trợ **Vừa khung**, phóng to/thu nhỏ và kéo xem. Kiểm tra tại 1366×768 và tỷ lệ hiển thị Windows 100%, 125%, 150%; khi thiếu chỗ, bảng điều khiển cuộn được, không che nút lưu.
- Chốt bản phác giao diện ở M0; M6 dùng giao diện thực để kiểm tra khoảng cách, chữ có dấu và sự nhất quán. Giữ một bộ công cụ GUI cho toàn ứng dụng, ưu tiên thử Tkinter/ttk theo phạm vi môn học; chỉ đổi sang PyQt nếu bản thử chứng minh có yêu cầu không đáp ứng được.

### Tác vụ và trạng thái

- Quét ảnh và OCR chạy ngoài luồng giao diện; chỉ luồng chính được cập nhật thành phần hiển thị. Trong lúc chạy, cửa sổ vẫn có thể di chuyển và vẽ lại.
- Mỗi lần xử lý có mã riêng gắn với ảnh và bộ tham số. Kết quả cũ đến muộn không được ghi lên ảnh mới. Giới hạn một tác vụ nặng đang chạy để tránh xếp hàng do bấm liên tục.
- Các trạng thái tối thiểu: **Chưa chọn ảnh → Sẵn sàng → Đang quét → Cần điều chỉnh góc / Đã quét → Đang nhận dạng chữ → Hoàn tất**; lỗi đưa về trạng thái có thể thử lại.
- Nút chỉ hoạt động khi có dữ liệu cần thiết. **Lưu ảnh quét** cần ảnh quét hợp lệ; **Lưu văn bản** cần văn bản của đúng ảnh hiện tại. Đổi ảnh, đổi góc hoặc đổi chế độ làm kết quả phụ thuộc trở thành chưa cập nhật; không được lưu nhầm như kết quả mới.
- Khi hủy tác vụ, giao diện báo **Đang hủy…**. Với phép gọi không ngắt được tức thì, bỏ kết quả khi hoàn tất và chỉ cho chạy lại sau khi tài nguyên được giải phóng; không hứa hủy ngay. Xác định giới hạn thời gian OCR ở M5.
- Xem trước dùng bản ảnh thu nhỏ; xuất ảnh dùng dữ liệu gốc. Đổi chế độ ảnh tái sử dụng ảnh đã chỉnh phối cảnh, không chạy lại phát hiện trang. Kéo góc chỉ cập nhật lớp vẽ; chạy lại khi người dùng xác nhận.

### Độ ổn định dữ liệu và môi trường

- Chuẩn hóa hướng ảnh trước khi gán tọa độ; ảnh xem trước, ảnh gốc và bốn góc dùng cùng quy ước. Không coi chỉnh phối cảnh là tự xoay văn bản về chiều đọc; cung cấp xoay 90° khi cần và làm mới OCR sau xoay.
- Hỗ trợ JPG/PNG trước; kiểm tra tệp hỏng, phần mở rộng không khớp nội dung, ảnh rất lớn và ảnh có kênh trong suốt. Chốt giới hạn số điểm ảnh/kích thước ảnh đích tại M0 để tránh cạn bộ nhớ; báo rõ khi phải giảm độ phân giải.
- Đọc/ghi đường dẫn tiếng Việt có dấu và khoảng trắng trên Windows. Văn bản lưu UTF-8; chuẩn hóa Unicode NFC khi tính CER/WER, không bỏ dấu để làm điểm số tốt hơn.
- Không sửa ảnh đầu vào. Khi lưu, xác nhận ghi đè nếu tệp đã tồn tại; chỉ báo thành công sau khi ghi xong. Nếu ghi thất bại, giữ kết quả trong ứng dụng để người dùng chọn nơi khác.
- Thiếu Tesseract, dữ liệu ngôn ngữ hoặc mô hình OCR không được chặn chức năng quét và lưu ảnh. Kiểm tra OCR riêng, thông báo thành phần thiếu cụ thể. Chuẩn bị dữ liệu OCR trước buổi demo và kiểm tra chạy ngoại tuyến.
- Ghi phiên bản Python, OpenCV, thư viện OCR và cấu hình máy đã kiểm thử. Hướng dẫn Spyder phải chọn đúng môi trường và chạy được khi thư mục làm việc khác thư mục chứa script.

## 12. Quy ước tiếng Việt trên giao diện

Tài liệu kỹ thuật có thể giữ tên thuật toán và API. Giao diện dùng câu ngắn, động từ rõ, xưng hô nhất quán và không đưa traceback hoặc tên hàm vào thông báo thông thường. Chi tiết kỹ thuật ghi trong nhật ký.

| Mục đích | Nội dung hiển thị |
|---|---|
| Mở ảnh | Chọn ảnh |
| Chỉnh vùng trang | Điều chỉnh góc; hướng dẫn: Kéo bốn điểm vào bốn góc trang, rồi chọn Xác nhận |
| Xử lý chính | Quét tài liệu |
| Chế độ ảnh | Màu; Thang xám; Đen trắng |
| OCR | Nhận dạng chữ; ngôn ngữ: Tiếng Việt / Tiếng Anh / Tiếng Việt và tiếng Anh |
| Xuất kết quả | Lưu ảnh quét; Lưu văn bản; Sao chép văn bản |
| Ảnh không đọc được | Không mở được ảnh. Hãy chọn tệp JPG hoặc PNG hợp lệ |
| Không tìm được trang | Chưa xác định được vùng tài liệu. Hãy điều chỉnh bốn góc hoặc chọn ảnh khác |
| Không có chữ | Chưa nhận dạng được chữ. Hãy thử chế độ ảnh khác hoặc chọn ảnh rõ hơn |
| Thiếu dữ liệu tiếng Việt | Chưa có dữ liệu nhận dạng tiếng Việt. Bạn vẫn có thể quét và lưu ảnh |
| Lỗi ghi tệp | Không lưu được tệp tại vị trí này. Hãy chọn thư mục khác và thử lại |
| Lưu thành công | Đã lưu ảnh quét / Đã lưu văn bản, kèm đường dẫn thực tế |
| Hủy tác vụ | Đang hủy… / Đã hủy xử lý |

Trong phần giải thích cho người dùng, dùng **ảnh quét** thay cho “bản scan”, **phương án dự phòng** thay cho “fallback”, **chỉnh phối cảnh** thay cho “warp”, **khả năng đọc** thay cho “độ đọc”. Không dịch tên API hoặc thay tên tệp chỉ để Việt hóa.

## 13. Tiêu chí nghiệm thu giao diện và trải nghiệm

Các con số dưới đây là **mục tiêu thiết kế**, chưa phải kết quả đo. Tại M0, ghi cấu hình máy, kích thước ảnh đầu vào và thống nhất ngân sách thời gian quét/OCR. Đo lần khởi động đầu và các lần chạy sau riêng; báo trung vị và P95 với số mẫu đủ lớn, nếu ít mẫu thì báo toàn bộ số đo và giá trị lớn nhất.

| Bài kiểm thử | Kết quả cần đạt |
|---|---|
| Nhấn nút quét/OCR | Trong 200 ms xuất hiện trạng thái đang xử lý trên máy thử; không chờ tính xong mới phản hồi |
| Quét hoặc OCR kéo dài | Có thể di chuyển/vẽ lại cửa sổ; trạng thái không gây hiểu nhầm; không cập nhật UI từ luồng nền |
| Nhấn nút xử lý liên tiếp | Chỉ một tác vụ nặng được thực hiện; không sinh hàng đợi vô hạn |
| Hủy và xử lý lại | Kết quả đã hủy không xuất hiện trở lại; tác vụ mới chỉ chạy khi đủ điều kiện |
| Mở lần lượt 20 ảnh | Không văng ứng dụng, không giữ ảnh/kết quả cũ sai ngữ cảnh; đo bộ nhớ để phát hiện tích lũy sau khi giải phóng ảnh |
| Đổi góc/chế độ sau OCR | Văn bản cũ được đánh dấu chưa cập nhật hoặc xóa có thông báo; không lưu nhầm văn bản của cấu hình cũ |
| Ảnh lớn, tệp hỏng, thiếu OCR | Thông báo phù hợp, có thể chọn ảnh khác và tiếp tục dùng chức năng còn khả dụng |
| Tên tệp “Tài liệu tiếng Việt 01.png” | Mở ảnh, lưu ảnh và văn bản, mở lại được; dấu tiếng Việt không hỏng |
| Lưu trùng tên hoặc không đủ quyền | Hỏi ghi đè đúng lúc; không mất kết quả đang xem; không báo lưu thành công khi thất bại |
| Màn hình và DPI | Không cắt chữ, chồng nút hoặc kéo méo ảnh tại các cấu hình ở mục 11; thao tác bàn phím có chỉ báo tiêu điểm |
| Chuỗi thao tác đầy đủ | Chọn ảnh → tự căn và quét → kiểm tra bản quét → chọn chế độ → nhận dạng → sửa chữ → lưu → mở lại; kết quả khớp ảnh và chế độ hiện tại. Sửa góc chỉ khi kết quả tự động cần điều chỉnh |
| Demo ngoại tuyến | Quét và OCR chạy được với dữ liệu đã chuẩn bị; README đủ để khởi động lại trong môi trường đã kiểm thử |

Chỉ xác nhận ứng dụng hoạt động mượt và giao diện đạt yêu cầu trên máy đích khi các bài thử trên có bằng chứng. Các lỗi bắt buộc sửa trước demo: giao diện treo, sai ảnh/kết quả, mất dữ liệu khi lưu, lỗi dấu tiếng Việt, nút không truy cập được và lỗi làm ứng dụng văng.

## 14. Tiến độ thực hiện và việc còn cần kiểm chứng

| Mốc | Trạng thái ngày 26/09/2026 | Bằng chứng / việc còn lại |
|---|---|---|
| M0 | Đã chốt cấu trúc và phương pháp đo; có 9 ảnh JPG khảo sát nhưng chưa có tập MVP có nhãn | 5 ảnh vở cắt mép, 2 ảnh vở mở hai trang, 1 màn chiếu có người che, 1 bảng lớp; cần ảnh một trang đủ viền và văn bản chuẩn |
| M1–M2 | Đã bổ sung tự căn vùng trang và chỉnh phối cảnh; chưa nghiệm thu bốn góc chính xác trên ảnh MVP thật | Bản đầu từ chối 9/9 ảnh khảo sát trong 0,029–0,073 giây/ảnh; bản mới tạo vùng trang trên 7/9. #426/#475/#497 hữu ích; #350/#451 có điều kiện; #321/#401 chỉ phần trang đang thấy. #374/#521 bị từ chối. Không dùng 7/9 làm tỷ lệ thành công đại diện |
| M3 | Đã triển khai màu, xám, đen trắng; đã cải thiện nhị phân hóa cho ảnh thử #06 | GUI quét thủ công ảnh vở đầu: màu/xám giữ chữ. Bản đen trắng cũ làm đen vùng bóng lớn; trên ảnh #06 sau sửa, mảng tối che chữ biến mất, xử lý khoảng 0,017 giây. Cần thử thêm ảnh có bóng và chữ mảnh |
| M4 | Đã triển khai phương án `visible_page_estimate`, `open_notebook_right_page` và chọn bốn góc thủ công | Tự động là luồng chính; chọn tay là cứu hộ tùy chọn và chỉ được dùng khi người dùng bấm nút sửa góc. Hai phương án ước lượng tạo vùng cắt khi thiếu mép, không khôi phục đủ trang ngoài khung hình. Cần đánh giá ca đủ viền và ca ngoài phạm vi riêng |
| M5 | Đã tích hợp OCR Việt/Anh, Tesseract cục bộ và xuất UTF-8 | `.venv` có pytesseract 0.3.13; `tools/tesseract` có Tesseract 5.5.3.20260724 và mô hình `vie`/`eng`. CLI OCR ảnh demo thành công, nhận đúng tiêu đề Việt và câu Anh nhưng còn sai một số dấu. Chưa đo CER/WER trên ảnh thật |
| M6 | Đã triển khai GUI tiếng Việt, xử lý nền, hủy tác vụ, zoom, lưu ảnh/văn bản và hiển thị góc tự phát hiện | Nút chính là Tự căn và quét; thất bại không ép chọn góc tay, lần tự quét mới không dùng lại góc tay cũ. Kiểm thử Tk và nghiệm thu trực quan qua Computer Use đạt trên ảnh demo và ảnh vở #426; đã chạy OCR và lưu văn bản từ GUI. Cần thử tiếp trường hợp trùng tên |
| M7 | Đã có README, dàn ý báo cáo, nhật ký quyết định và kết quả phần mềm | Có kết quả OCR demo tại `images/output/demo_ocr_local.txt`; cần thí nghiệm ảnh thật, CER/WER và đánh giá chữ viết tay riêng |

Bộ **22/22 kiểm thử** phần mềm đã đạt với `.venv` Python 3.12 của dự án. CLI đã quét và OCR ảnh demo tổng hợp bằng Tesseract cục bộ; kết quả UTF-8 ở `images/output/demo_ocr_local.txt` nhận đúng các cụm Việt/Anh chính, còn sai một số dấu tiếng Việt. Ảnh demo 1350×1150 px có sai số bốn góc trung bình 0,603 px; quét 20 lượt trước đó có trung vị 0,017 giây và P95 0,019 giây trên Python bundled/OpenCV tạm. Đây là phép đo trên ảnh dựng và môi trường cũ, không dùng làm bằng chứng độ chính xác hoặc tốc độ với ảnh chụp thật. Bản tự căn góc mới tạo vùng trang trên 7/9 ảnh JPG thật khảo sát; hai ảnh màn chiếu/bảng bị từ chối. Một số vùng cắt chỉ có phần trang nhìn thấy. Xem ảnh overlay `images/debug/photo_audit/contact_sheet.jpg`; script đánh giá có thể đặt tại `tests/evaluate_photos.py`. Bản đen trắng sau sửa đã loại mảng tối che chữ trên ảnh #06 trong khoảng 0,017 giây, nhưng chưa đánh giá trên tập đủ điều kiện MVP. **22/22 là kết quả kiểm thử phần mềm, không phải tỷ lệ góc được phát hiện chính xác.** Ưu tiên tiếp theo là thu ảnh một trang đủ viền có nhãn góc, thử thêm ảnh bóng/chữ mảnh, nghiệm thu GUI và đo CER/WER trên ảnh thật. Điều kiện nghiệm thu chi tiết ở `docs/testing.md`.

## 15. Bản web cục bộ (21/10/2026)

Giao diện web đã được thêm vào `web/` và `src/web_server.py`. Luồng chính vẫn tự căn bốn góc; chọn góc bằng tay chỉ là phương án sửa ngoại lệ. `run_scanner.cmd` nay mở bản web tại `http://127.0.0.1:8765/`; `run_desktop.cmd` giữ bản Tkinter cũ. Bản web hỗ trợ kéo thả, ba chế độ ảnh, hiển thị góc, OCR Việt/Anh, tải PNG/TXT, chủ đề sáng/tối và bố cục responsive. Xem `docs/web-app.md` để biết kiến trúc và giới hạn.

Bộ kiểm thử hiện tại đạt **23/23**, gồm kiểm thử adapter web quét ảnh demo và OCR thật trên bản quét; `node --check web/app.js` đạt. Máy chủ đã khởi động thành công. Công cụ trình duyệt từ chối mở `localhost` trong lượt này, nên kiểm tra trực quan tại 375/768/1024/1440 px và thao tác kéo thả/tải tệp trong trình duyệt vẫn là mục nghiệm thu tiếp theo. Kết quả kiểm thử API không thay thế đánh giá giao diện hoặc phép đo CER/WER trên ảnh thật.
