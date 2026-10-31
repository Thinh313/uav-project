# HeraHub software research · 12/10/2026

Research thủ công từ nguồn công khai, áp dụng Refinery chuyển giao v1.4. Không có một phiên chạy dịch vụ Deep Research riêng. Có 45 yêu cầu capture: 44 thành công, một URL MAVLink RTK trả 404. Hai bản text dẫn xuất có hash và liên kết raw source; tổng 46 bản ghi captured. 59 claim được người triển khai đọc ngữ cảnh và ghi vào `claims.jsonl`; máy chỉ kiểm span/provenance và output. Không tuyên bố đọc toàn bộ Internet hay toàn bộ SDK RtR.

`capture-requests.json` giữ URL; `sources.json` giữ thời điểm UTC, status, SHA-256 và raw bytes. `sources-initial-attempt.json` giữ lỗi DNS của lượt sandbox đầu, không thay bằng bằng chứng giả. Các `.readable.txt` hỗ trợ đọc HTML, không dùng làm snapshot claim. PDF Qualcomm được trích với pypdf; hàng QCS8550 đối chiếu hình trang 2 tại `../../evidence/hera02/qualcomm-selector-page2.png`. Release notes được decode từ manifest JSON, không sửa nội dung.

Tất cả nguồn RtR — website, GitHub release, GitBook — chung `origin_id=rtr`. Tổng năm origin: RtR, Qualcomm, Android, MAVLink, GStreamer. Nhiều trang cùng nhà xuất bản không thành nhiều xác nhận độc lập. Tier A chỉ trong phạm vi tài liệu của bên phát hành; không có kết quả kiểm nghiệm thiết bị. Manual tự ghi 4.0.0 build 4; release mới được xét riêng 4.0.14 build 111. Không nối hai phiên bản để giả định cùng một hành vi.

Registry tách HeraHub nền Intel, HeraHub v2 nền Android, tên HeraLink lịch sử, manual và release. `alias_map={}`; kiểm ambiguity ngăn gộp thế hệ hoặc RtR HeraLink với CubePilot HereLink. Quyết định đổi tên và ưu tiên độ sáng của chủ việc nằm trong SOT nội bộ, không đưa vào Refinery nguồn ngoài.

Không có denominator toàn thị trường; `universe.estimate=null`, `rollup_field=null`. Những trường SDK, channel map, firmware thực, radio lắp, codec trực tiếp, độ trễ đo, API pin controller và signer để null. Null ở entity không liên quan cũng chỉ là ô schema trống; chỉ danh sách unknown trong báo cáo là khoảng trống tích hợp cần xử lý.

Kết quả đọc và quyết định: `../../docs/HERAHUB-SOFTWARE-RESEARCH.md`. Work packages: `../../docs/HERAHUB-INTEGRATION-BACKLOG.md`. Capture raw không đồng nghĩa đã phân tích hết mọi trang: brochure payload lịch sử, index, README và một số trang tổng quan dùng để định vị nguồn; claim chỉ được chọn từ phần có liên quan.

Không tải APK ~295MB hay DEB ~197MB, không chạy/cài binary, không quét IP controller, không gửi tài liệu nội bộ lên web. Chỉ đọc manifest và release metadata công khai; SHA-256 APK là giá trị nhà phát hành khai báo, chưa đối chiếu byte APK.
