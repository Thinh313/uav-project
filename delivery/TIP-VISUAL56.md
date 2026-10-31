# VISUAL56 · Nâng chất lượng hình ảnh giả lập

15/10/2026. Yêu cầu: hình ảnh sát thực tế, thay UAV primitive bằng model3D chi tiết, không bắt buộc giống Hera. Module mới `pilot/visual56`, không sửa renderer53, physics/controller, source/candidate, SOT/trust/ENDURE hoặc mission55.

Thiết kế: cảnh bay chiếm toàn bộ stage; UAV là chủ thể, HDRI ảnh chụp và nền asphalt PBR; trắng#ffffff/graphite#202326, chữ#17212a, vàng#e7bb35 dưới5% diện tích UI, xanh dữ liệu#59778c. IBM Plex Sans cho toàn bộ UI. Header trắng mỏng, cảnh dưới, thanh thời gian ngang, thông số dễ đọc trên panel giấy nhỏ. Không dashboard nhiều card, không nhãn giả năng lực sản phẩm. ModelAGI/EdMackey CC BY4.0 có texture/normal/metalrough và bốn cánh; scale/orientation có khai báo, không xem là Hera calibrated.

|AC|Nghiệm thu|
|---|---|
|V01|ModelGLB thật +nguồn/license/SHA, attribution trên UI, không primitive fallback âm thầm.|
|V02|Ánh sáng HDRI/PBR, tone mapping/color space đúng, contact shadows, model nhìn rõ cận cảnh/flight.|
|V03|Replay từ snapshot physics giữ lại, provenanceSHA; hoặc inspect tĩnh có nhãn. Không viết lại physics để làm đẹp, không giả telemetry live.|
|V04|Orbit/zoom/reset camera, timeline/play-pause, view lựa chọn; active labels phản ánh hành vi thật.|
|V05|Kiểm browser/screenshot rồi xem và sửa; nhiều viewport, khôngJSerror, không asset network bên ngoài khi chạy; đo frame-time trên host, không gọi là Hera/projector benchmark.|
|V06|Pin trước/sau, sàn20GiB, budgetasset100MiB; không ký, buildAPK, chạySITL mới hoặc sửa bằng chứng cũ.|

Một agent theo pha specification/build/verify. Chất lượng đồ họa không chứng minh fidelity vật lý, camera hay field training acceptance. Màn hình trình chiếu và đánh giá của người xem là gate riêng.
