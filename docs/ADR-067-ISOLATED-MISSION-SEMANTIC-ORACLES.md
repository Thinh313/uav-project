# ADR067 · Đối chiếu nhiệm vụ trong module cô lập

Accepted for offline engineering scope,15/10/2026. Phục vụ RAGAS54 B1/B2 và yêu cầu mở rộng corpus; không thay stack triển khai đóng băng.

Chọn module Python đọc Plan và replay JSON độc lập với `app/core/qgc.mjs`; oracle toán JS cùng nguồn expected analytic/GeographicLib có pin. Giữ rõ header/Home, editable ComplexItem và executable cached items. So sánh phải nêu khác biệt cả ba; không regenerate Survey và không hứa semantic equivalence cho schema/extension chưa hiểu. Không dùng roundtrip exporter/importer chung implementation làm oracle duy nhất.

Default strict: null khác0, frame khác nhau là diff, doJumpId có ảnh hưởng DO_JUMP không được bỏ qua. Mọi canonicalization của readback phải được whitelist theo command/field/firmware và ghi vào report. `MISSION_ITEM_INT.target_*` trên readback chỉ receiver GCS; không nhầm nó với camera target hoặc source AP. Session/source/receiver thuộc envelope replay, phải kiểm riêng. Chi tiết report không cấp flight authority.

Giữ file QGC gốc bằng đường dẫn/SHA; fixtures mới là SYNTHETIC_DERIVATIVE. GeographicLib được dùng như oracle geodesic riêng, không copy thuật toán vào app đóng băng. Numeric synthetic success không chứng minh DEM/datum/camera/field accuracy. Snapshot DEM, Home và observed telemetry phải nêu freshness, session/boot và datum; calc-above-terrain đã bake thành AMSL khác MAV_FRAME terrain-native.

Tất cả writer chỉ tạo đầu ra trong module/evidence/delivery/docs của increment; không network socket hoặc lệnh flight. Kiểm provenance/mutation/retained readback và pin trước/sau. Tích hợp sản phẩm/SITL/A/B thật cần bước nghiệm thu riêng.
