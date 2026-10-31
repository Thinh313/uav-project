# Kế hoạch sản phẩm giả lập bay AERIS phục vụ hội đồng đánh giá

Ngày 15/10/2026. Ưu tiên mới nhất của chủ việc: tập trung tối đa vào simulator có 3D cao cấp, cảm giác bay có cơ sở vật lý và đủ manual, bán tự động, tự động để cạnh tranh lựa chọn sản phẩm. Hội đồng xem qua màn hình lớn hoặc máy chiếu nối laptop; cần có bản trình diễn càng sớm càng tốt.

**Đầu ra mục tiêu là một phiên live 18 phút:** người điều khiển bay thật trong simulator, hội đồng yêu cầu đổi điểm đến hoặc seed gió, hệ thống phản ứng qua autopilot và vật lý, sau đó mở được hồ sơ bài tập. Chất lượng được đánh giá đồng thời ở trải nghiệm, độ đúng, đồ họa, âm thanh và khả năng giải thích kết quả.

Đây là kế hoạch triển khai. Các mục tiêu và lịch dưới đây chưa phải kết quả chạy hoặc ngày giao được cam kết. Trong lượt này chỉ tạo tài liệu và trang trình bày; không cài stack, khởi động SITL, thay phần mềm vận hành hoặc ký bản mới.

## 0. Mục tiêu và người sử dụng

Mục tiêu của bản hội đồng: (1) cả ba nhóm manual/assisted/AUTO có minh chứng live; (2) tải/gió làm thay đổi đáp ứng có thể giải thích bằng trace; (3) một nhiệm vụ tạo được ảnh mô phỏng và review, không chỉ drone đi trên tuyến; (4) chất lượng hình/âm đạt rubric và ngân sách trên đúng máy chiếu; (5) ba tổng duyệt liên tiếp không critical fail. Tất cả là tiêu chí mục tiêu, chưa có kết quả SIMTRAIN52.

- Là học viên/operator, tôi muốn dùng input quen thuộc và biết mode/quyền hiện tại để tập thao tác và tiếp quản đúng.
- Là giáo viên, tôi muốn chọn điều kiện/chèn lỗi và xem bằng chứng để giải thích lỗi, không chỉ cho một điểm tổng.
- Là thành viên hội đồng, tôi muốn yêu cầu điểm đến/seed mới và kiểm review để phân biệt khả năng vận hành với video trình diễn.
- Là kỹ sư tích hợp, tôi muốn profile/clock/transport được pin để tái lập lỗi và thêm HeraHub/payload theo contract.
- Là khách hàng ở xa (P1), tôi muốn luyện trên PC local và nhận hướng dẫn có quyền qua mạng mà không phụ thuộc WAN cho vòng điều khiển bên trong.

Chỉ số sớm: số gate P0 có evidence, defect nghiêm trọng còn mở, kết quả pacing và visual review, số rehearsal đủ hành trình. Chỉ số sau: tỷ lệ hoàn thành bài và lỗi thao tác của học viên, nhu cầu hỗ trợ và hiệu quả chuyển giao; baseline/cỡ mẫu phải chốt trước user study, chưa đặt phần trăm cải thiện tùy ý. Kết quả chọn thầu/hội đồng là outcome kinh doanh, không suy ra từ test count.

## 1. Phạm vi ưu tiên và cách tạo bản cạnh tranh sớm

Bản hội đồng đầu chạy **offline trên laptop có GPU**, xuất hình ra máy chiếu. Dùng gamepad/joystick hiện có nếu có; bàn phím là phương án thay thế có nhãn. HeraHub và đào tạo qua WAN là nhánh tích hợp sau, không nằm trên đường găng của buổi demo laptop. Người dùng không cần cung cấp SDK để bắt đầu phần này.

Giữ đủ ba cách điều khiển ngay trong bản đầu. Thu gọn số bối cảnh xuống **một khu luyện tập đẹp, nhất quán**, có bãi đáp, tuyến đường và vùng khảo sát; không thu gọn thành animation hoặc chỉ phát lại mission. Chưa mở rộng sang thành phố, nhiều máy bay, CFD đầy đủ hoặc LiDAR thương mại để tránh chia nhỏ nỗ lực.

| Phải đạt cho bản hội đồng | Làm sau khi bản lõi đạt |
|---|---|
| Manual, Guided/assisted, AUTO; tiếp quản có xác nhận | HeraHub MCU/native và dual-operator trên thiết bị thật |
| Không tải/có tải/tải lệch, gió/gust có seed | Hiệu chỉnh Hera theo dữ liệu thực ngoài tập fit |
| Một scene PBR đẹp, camera follow/payload, RPM audio | Nhiều vùng địa lý, scan/splat và cảnh chuyên ngành |
| Camera scene, ảnh/metadata, survey/corridor và review | Pipeline photogrammetry nặng và LiDAR/thermal có model riêng |
| Giáo viên chèn lỗi, học viên xử lý, timeline và điểm | Đào tạo từ xa có auth/role, đo mạng và vận hành nhiều lớp |
| Cold start offline, máy chiếu, trace và backup có nhãn | Chứng minh chuyển giao kỹ năng sang bay thực và so sánh đối thủ |

Không sửa roadmap/SOT lịch sử: ưu tiên mới được ghi ở kế hoạch này. Các việc lưu trữ, native và payload đã làm được tái sử dụng theo contract; chỉ sửa chúng khi có bằng chứng là dependency chặn simulator.

## 2. Kiến trúc sản phẩm

```text
Gamepad/keyboard hoặc HeraHub về sau
              │ input + calibration + owner/session
              ▼
       AERIS Training Workspace
              │ adapter chỉ dành cho simulator
              ▼
          ArduPilot SITL ─── actuator outputs ───► Physics 6DOF
              ▲                                    │
              └──────── virtual sensors ────────────┘
              │ telemetry                          │ timestamped truth
              ▼                                    ▼
        Cockpit người học                   3D scene + audio
                                                   │
                                           virtual camera/gimbal
                                                   │
                                     ảnh/video + metadata + inventory
                                                   ▼
                                        review / refly proposal
```

Instructor service đưa tải trước phiên, disturbance và fault vào đúng boundary đã định nghĩa; không dịch chuyển drone để làm cảnh. Recorder thu input, request, observed mode, physics, sensor, camera và fault. Presentation camera là observer; không cấp lệnh bay. Simulation truth, reported sensor và rendering interpolation là ba lớp riêng.

**Một nguồn trạng thái vật lý duy nhất.** Renderer nhận timestamped snapshots, có thể nội suy hình ảnh với giới hạn tuổi dữ liệu nhưng không tạo thêm bước vật lý hoặc thay pose nguồn. Khi snapshot stale, hiển thị mất dữ liệu và thu hồi input theo policy; không kéo drone dọc đường waypoint để che giật.

Adapter mới đọc các thành phần SIM32/JOURNAL04/MAPPING51 đã đóng băng. Chưa có việc “cắm thẳng” MAPPING51 vào Fly production: cần compiler mapping rõ giữa AOI, Home/AGL, mission và camera; upload/readback cùng capability của binary được pin.

## 3. Ba cách điều khiển phải trình bày được

| Nhóm | Hành động người dùng | Tự động hóa bên trong | Điều hội đồng quan sát |
|---|---|---|---|
| Bay tay có hỗ trợ nhập môn | Stick điều hướng, tăng/giảm cao, yaw; thả stick giữ vị trí ở Loiter khi hợp lệ | Autopilot giữ attitude/position theo mode, không phải physics do UI tự đặt | Input overlay, observed mode, quán tính, phản ứng gió và motor |
| Bay tay nâng cao | Stabilize hoặc AltHold theo bài; đổi orientation, tiếp cận và hạ cánh | Mức giữ cao/vị trí khác nhau theo mode | Không coi Stabilize/AltHold/Loiter là một manual mode giống nhau |
| Bán tự động | Guided takeoff, chọn điểm đến, đổi cao/yaw, hold, RTL | AP đi tới setpoint, người điều khiển vẫn giám sát và tiếp quản | Marker điểm yêu cầu, đường đi thực, mode/ownership và giới hạn |
| Tự động | Nhập KML vùng/tuyến, preflight, upload/readback, AUTO | AP thực hiện mission và trigger theo contract | Planned vs executed path, capture, mission progress và outcome |

Ba nhóm sản phẩm là manual, assisted và autonomous; hàng manual nâng cao là mức đào tạo trong cùng nhóm. Tài liệu ArduPilot chỉ là tham chiếu ý nghĩa mode; support/mapping của binary pin hiện tại phải được kiểm trước khi bật nút.

AUTO→manual phải có neutral-first, quyền điều khiển và observed mode; không snap vị trí. Resume cần người học xem vị trí, mission sequence và phần chưa thu. Sau lỗi terminal/restart không khôi phục quyền từ lịch sử. Giáo viên có quyền abort bài; nếu đã chạy, reset tạo session mới và giữ kết quả cũ.

## 4. Vật lý và mức độ giống Hera

Mô hình tối thiểu gồm rigid body 6DOF, quaternion, trọng lực, thrust/torque rotor, motor lag/saturation, drag theo vận tốc tương đối, pin/điện áp và khối lượng–trọng tâm–tensor quán tính tổng. Payload đổi các đại lượng liên quan; không chỉ nhân hệ số để drone “ì”. PID có thể tăng ga bù tải, nên cần quan sát cả gia tốc, stopping distance, hover power và actuator headroom.

**Đổi payload giữa hai lượt fresh**, giữ firmware, controller tuning, input chuẩn và seed môi trường. Trong buổi live, cho hội đồng điều khiển ngắn để cảm nhận; phép so định lượng dùng cùng input profile đã khai báo, không lấy hai người lái khác nhau làm đối chứng duy nhất. Không đổi CG tức thời giữa chuyến để diễn hiệu ứng, trừ khi có bài payload release riêng đã kiểm.

| Mức profile | Có thể tuyên bố | Điều kiện |
|---|---|---|
| Reference simulator | Vòng kín hoạt động và các định luật/model đã kiểm | Mô hình quad-X hiện có và analytic/oracle; chưa là Hera |
| Hera engineering profile | Hình học/mixer/số rotor đúng cấu hình, tham số còn ước tính có nguồn | Xác minh cấu hình lắp thực, mass/CG và layout; nhãn chưa hiệu chỉnh |
| Hera calibrated profile | Đáp ứng phù hợp dữ liệu đo trong miền đã khai báo | Thrust/lag/drag/battery/inertia được fit và validation trên dữ liệu riêng |
| Training validation | Bài tập giúp kỹ năng mục tiêu với giới hạn rõ | Operator/học viên thử, đối chiếu và chuyên gia đánh giá; không suy từ FPS |

Mesh số rotor, hướng quay, actuator channels và mixer phải cùng một cấu hình. Không đặt mesh Hera nhiều rotor lên physics quad-X rồi gọi là mô phỏng Hera hoàn chỉnh. CAD/BOM/render chỉ giúp hình học; không tự cung cấp thrust curve hoặc độ đúng động lực học.

Gió gồm nền, gust và nhiễu động có seed, hệ tọa độ và đơn vị. Gió tác động vật lý độc lập với hạt/cây chuyển động trên màn hình. Mưa/sương bản đầu gồm visibility/lighting/lens/sensor effects có contract; tác động wet-prop, nước vào điện hoặc khí động mưa nặng để unsupported đến khi có model/dữ liệu. Không giả vờ mô phỏng tất cả thời tiết chỉ vì có rain particles.

Tiếp đất, collider và crash có phép kiểm. Mặt đất và vật cản nhìn thấy phải khai báo collision status. Không dùng DEM thô làm bằng chứng dây điện/cành cây đã có. Ground effect, propwash và tải treo là work package mở rộng; không bịa hệ số để tạo cảm giác.

## 5. Art direction 3D và âm thanh

**Tạo một cảnh thực tế có chủ đích thay vì nhiều cảnh sơ sài.** Bối cảnh đầu đề xuất là khu huấn luyện khoảng 1×1km: bãi đáp có kích thước thật, mặt đường cho corridor, thảm thực vật và công trình tạo mốc độ cao/khoảng cách, một vùng khảo sát phẳng phù hợp compiler hiện có. Khóa phạm vi bay được kiểm; cảnh nền xa không được ngầm coi là vùng collision/terrain đã kiểm.

Chất lượng thị giác: Hera/reference mesh đúng tỷ lệ, silhouette rõ; vật liệu PBR có roughness/normal hợp lý; ánh sáng, contact shadow, ambient occlusion tiết chế; bóng không nhấp nháy; LOD và instancing giữ mật độ cảnh. Rotor hiển thị theo RPM/time và motion blur thích hợp, tránh aliasing tạo cảm giác rotor đứng yên. Không phủ HUD hoặc glow làm mất khả năng nhìn hướng máy bay.

Ba camera bắt buộc: pilot ground view để luyện định hướng, follow/orbit để hội đồng hiểu chuyển động, payload view đúng gimbal/lens. Cinematic camera chỉ phục vụ quan sát hoặc đoạn giới thiệu có nhãn, không che fault hoặc dùng để điều khiển drone ngoài contract.

**Lựa chọn công nghệ đề xuất:** giữ Three.js hiện có để tạo vertical slice sớm; đánh giá WebGPURenderer với WebGL2 fallback bằng một scene/workload pin. Không viết lại cả engine chỉ để dùng tên WebGPU. Cần kiểm migration material/shader và GPU/driver/browser thật. Physics ở process riêng, không phụ thuộc WebGPU compute hay render FPS. Nếu sau benchmark laptop không đủ scene mục tiêu, giảm chi phí trang trí theo tier đã công bố; không âm thầm giảm fidelity camera kiểm thử hoặc bỏ physics frame.

Asset phải có quyền dùng và phân phối offline. Ưu tiên CAD/ảnh RtR được phép, asset tự tạo và bộ có license phù hợp. URL public hoặc “miễn phí xem” không đồng nghĩa được cache/chiếu/phân phối. Splat/photogrammetry có thể dùng cho cảnh cận tĩnh về sau, nhưng không tự là collision mesh, dynamic foliage hoặc model ánh sáng mọi thời tiết. Không phóng đại địa hình trong miền physics.

Âm thanh tổng hợp theo RPM từng rotor, blade-pass/harmonics, khoảng cách, góc nhìn và môi trường. Hỗ trợ mute/limiter và kiểm loa máy chiếu. Động cơ yếu/tải lệch có âm tương ứng với RPM model, không loop âm có sẵn theo thanh ga UI. Chỉ gọi “âm Hera đã hiệu chỉnh” sau khi có bản ghi tham chiếu đúng cấu hình; volume loa không phải SPL vật lý.

## 6. Camera và mapping đầu cuối

Camera phải là sensor trong scene, có pose/gimbal/FOV, thời điểm phơi, độ phân giải và capture index. Scene truth là ground truth của bài test; reported GNSS có thể được thêm bias/noise/delay tách riêng. Mỗi ảnh có session/aircraft/camera/profile/time/pose/source và hash. Preview video tương tác khác tập ảnh sensor lưu; ghi cadence/resolution/drop/age rõ, không dùng ảnh thumbnail làm bằng chứng full-resolution capture.

Bản đầu có shutter/blur/readout model ở mức hỗ trợ đã kiểm. Rolling shutter cần đúng thời gian các dòng hoặc approximation có miền hiệu lực; chỉ thêm hiệu ứng blur bằng hậu kỳ không được gọi là camera vật lý đầy đủ. Gimbal attitude theo observed/control state, không luôn mặc định nadir.

KML→readiness→mission→AUTO→camera→review phải đi qua cùng session. Tách planned route, executed route, trigger, exposure và file. Review hiển thị vùng dự kiến/quan sát, ảnh bị thiếu/nhòe và đề nghị refly; người học duyệt mission mới. Chất lượng dataset mô phỏng kiểm với truth của scene, không chứng minh accuracy đo đạc của camera Hera ngoài thực địa. Engine xử lý ảnh nặng là adapter/workstation phase sau, chưa đưa vào handset.

## 7. Cockpit, giáo viên và màn hình hội đồng

- **Màn hội đồng:** ưu tiên world view lớn, mode thực/quyền/input source, telemetry thiết yếu, minimap/route và một cảnh báo ưu tiên. Nhãn simulation/profile mức hiệu chỉnh luôn thấy nhưng không phủ kín màn. Các chi tiết raw/engineering nằm trong diagnostic drawer.
- **Màn laptop:** khi extended display có sẵn, người trình bày dùng cockpit và instructor panel; màn chiếu là observer view cùng session. Khi mirror, có một layout tập trung và phím chuyển panel. Không phụ thuộc mở hai cửa sổ khác session.
- **Giáo viên:** chọn bài/tải trước phiên, thay gió/fault theo policy, đánh dấu sự kiện và chấm rubric. Không sửa pose hoặc xóa lỗi khỏi lịch sử. Authority transfer có quyền và xác nhận.
- **Review:** timeline input/mode/fault/trajectory/camera đồng bộ, đối chiếu kỳ vọng và hành động; scoring có lý do, confidence/unknown và human override được ghi. Có thể scrub replay nhưng mọi panel phải báo replay.

Branding trắng/đen, vàng làm nhấn hành động hoặc selected path; đỏ chỉ cho cảnh báo đúng mức. Text và control thiết kế cho máy chiếu 1080p, kiểm thực từ cuối phòng; không ép mật độ cockpit kỹ sư lên màn hội đồng. Touch/native dp có gate riêng, không suy từ CSS.

## 8. Hiệu suất và nghiệm thu

Mục tiêu định lượng trong `plan.json` là **đề xuất**, chưa đo hoặc được chủ việc duyệt từng con số. G0 khóa laptop/GPU/OS/browser/driver/power mode/projector, scene, weather, mode, payload, camera resolution/cadence và compiler/firmware. Mọi thay đổi workload phải được ghi, không so hai cấu hình khác nhau rồi gọi tối ưu.

Nhịp vật lý là đường găng: SIM32-PIPE03 ghi 0/6 capture đạt RTF≥1, JOURNAL04 mới kiểm mock. Không cộng các lần này thành thành công của simulator mới. Phải kiểm 1× và full-cost AP/backend/logging trên derivative mới trước nghiệm thu live. Giữ speedup1, cap bù nhịp500ms và precision/oracle đang có; mọi thay đổi phải có ADR/phép đối chứng, không thay ngầm.

Rendering có thể nội suy hoặc chọn sample hiển thị với tuổi dữ liệu được đo; physics/control/WAL không được bỏ frame để làm đẹp FPS. Throttle UI debug/overlay và LOD visual là tối ưu khác, phải công bố. Software rendering/headless chỉ kiểm chức năng/ảnh bố cục, không chứng minh GPU performance.

Các lớp kiểm: analytic và convergence; raw/oracle trace; fault/authority; camera ground truth; GPU/workload; visual rubric bởi người; đào tạo/user walkthrough; rehearsal projector offline. Plan coverage không phải phần trăm hoàn thành sản phẩm.

## 8A Hợp đồng dữ liệu và clock

| Seam | Trường bắt buộc | Invariant |
|---|---|---|
| Scenario/profile | schema/version, aircraft/payload/rotor layout, SI units, frames, seed, provenance, source hash | Khóa trước phiên; thay mass/CG giữa phiên chỉ qua model có kiểm |
| Input/authority | session/boot/owner, sequence, clock domain, axes mapping, neutral state, expiry | Một owner; lệnh cũ/sai phiên không thành actuator input |
| AP/physics | pin firmware/config, servo frame counter/rate/PWM, dt, raw SHA, virtual sensors | NED/FRD/quaternion quy ước rõ; không tích phân lại duplicate hoặc đổi dt theo FPS |
| Render/audio | physics source sequence, sim timestamp, host receive time, interpolation/age | Presentation không ghi vào flight state; stale/focus policy rõ |
| Camera/media | camera/gimbal ID, intrinsics/profile, exposure/clock/pose, file/hash/index | Preview, captured output và physical capture là các provenance khác nhau |
| Fault/scoring | actor/role, boundary/time, parameters, event ID, expected response, evidence references | Seed/fault có thể tái lập, missing evidence không tự thành điểm đạt |

Clock host, AP/guest và sim có domain riêng; so qua bracket/uncertainty. Không biến API response hoặc clock offset ước tính thành latency một chiều đã biết. Sensor frame, capture exposure và audio/RPM có cùng tham chiếu sim time nhưng phải lưu thời điểm nhận/publish riêng.

## 8B Ngân sách tài nguyên cần chốt trước chạy

Lập kế hoạch chỉ tốn vài MiB. Chạy simulator/camera/recording có peak khác hẳn; số free hiện tại không phải giấy phép tải hoặc chạy mọi workload.

Ví dụ sizing, chưa đo: 1200Hz ×18phút = **1.296.000 physics frame**. Raw record trung bình512/2048/4096byte tương ứng0,66/2,65/5,31GB decimal, chưa cộng WAL hoặc bản sao. Video8Mbit/s trong18phút thêm1,08GB;200 ảnh6MB thêm1,20GB. Không giả định raw thực có kích thước trên hoặc gzip sẽ cứu được capacity. G0 phải đo bytes/frame và tính worst-case/cap rõ.

Admission = assets/runtime chưa có + peak raw/WAL/archive cùng tồn tại + video/ảnh + export/staging + host margin + **sàn20GiB**. Không cộng cap của các bản ghi làm capacity đã dùng, nhưng phải đủ cho peak đã khai báo. Có thể dùng laptop thử nghiệm/volume riêng đã kiểm khi host hiện không đủ; không tự xóa source/evidence hoặc chuyển chúng vào tmp. Chưa có cấu hình máy thì chưa đưa ra một sốGiB tải an toàn chung.

Nhật ký JOURNAL04 có bound mock; phải xây contract/quota mới đủ18phút và kiểm overflow trước khi reuse, không chỉ tăng lifetime. Để vẫn giữ thứ tự và bytes, có thể chunk/rotate theo manifest có seal, không auto prune. No frame loss cho control/raw canonical; frame hiển thị và camera cadence được khai báo, drops hiển thị riêng. CPU/GPU/RAM/VRAM/SSD peak được đo đồng thời với render và media.

## 9. Lịch mục tiêu để có bản trình diễn sớm

**Mục tiêu đề xuất: 7–10 ngày làm việc sau G0**, với ba kỹ sư có kinh nghiệm phụ trách physics/control, 3D/audio, integration/QA; operator/chuyên gia hỗ trợ duyệt. Đây là ước lượng độ tin cậy thấp trước G0, không phải lời hứa lịch. Không áp lịch đội ba người cho một người. Người chịu trách nhiệm cụ thể chưa được phân công.

Vertical slice 48 giờ đầu chỉ là mốc nội bộ nếu pacing có hướng giải quyết: một cảnh, một input, một mode và trace. Nó chưa thay bản hội đồng đủ ba nhóm mode và fault/review.

G0 trong phiên làm việc đầu chốt máy, asset, cấu hình Hera/reference và baseline. Nếu pacing chưa có hướng đạt hoặc asset/driver thiếu, cập nhật critical path và báo ngày lại; không hạ gate để giữ lịch. Asset/look development có thể làm trên scene tĩnh/song song sau G0, nhưng chỉ được nghiệm thu flight feel/live sau G1. Không tự spawn hay giao việc cho bên khác trong lượt lập kế hoạch này.

Trình tự thực hiện: G0→G1→G2/G3; G4 chuẩn bị art theo dữ liệu G0; ghép G2+G3+G4 vào G5→G6→G7. Chi tiết work package và exit gate trong phụ lục được sinh từ contract.

## 10. Kịch bản hội đồng và tổng duyệt

Kịch bản 18 phút có 8 phần trong `COUNCIL-RUNBOOK.md`. Mission ngắn được thiết kế để bay xong ở tốc độ1×; không tăng tốc thời gian để vừa slot. Chỉ chọn một fault trọng tâm để lời trình bày rõ, còn matrix lỗi mở trong Q&A.

Chuẩn bị ba tổng duyệt liên tiếp trên đúng máy/cáp/loa/projector: một cold offline, một challenge target/seed mới và một thử layout/màn hình. Tất cả giữ trace và kết quả, kể cả fail. Chưa qua rehearsal không ghi DEMO_READY.

Nếu live hỏng: ngừng phiên theo runbook, giữ incomplete và nói rõ lỗi; có thể mở recording đã nghiệm thu với nhãn “Bản ghi dự phòng”. Không đổi sang video âm thầm hoặc chấm recording thành live. Sau buổi có bundle logs/metrics/scoring và mô tả giới hạn profile để hội đồng kiểm lại.

## 11. Nguồn và quyết định còn mở

Nguồn nội bộ: AERIS-PRODUCT-QUALITY-STANDARD, completion SIM32/PIPE03/JOURNAL04/MAPPING51, hardware HeraHub và nghiên cứu demo Research Partner. Chỉ dùng để xác định nền hiện có và gap, không suy đã nghiệm thu Hera.

Tham chiếu hãng: [ArduPilot flight modes](https://ardupilot.org/copter/docs/flight-modes.html), [JSON physics interface](https://ardupilot.org/dev/docs/sitl-with-JSON.html), [Three.js WebGPURenderer](https://threejs.org/manual/pages/webgpurenderer). Chúng mô tả công nghệ/mode hiện có, không chứng minh integration trên binary/GPU của dự án.

Các quyết định mở có owner và thời điểm:

| Quyết định | Owner đề xuất | Chốt trước |
|---|---|---|
| Ngày và thời lượng thực hội đồng | Chủ việc | G0/G7 |
| Laptop/GPU, projector resolution và input hiện có | Lead + operator | G0 |
| Cấu hình rotor/mixer, mesh Hera có quyền và mức fidelity được trình bày | RtR hardware + physics/3D | G0/G1 |
| Dung sai pacing và latency/camera budget theo workload | Physics + QA | G1/G6 |
| Dữ liệu hiệu chỉnh Hera và tiêu chí sai số | Chuyên gia bay/trắc địa | Trước claim calibrated |
| Tên người phụ trách và khả năng chạy các nhánh song song | Chủ việc + lead | Trước nhận lịch7–10ngày |

Giữ sàn host20GiB. Lập kế hoạch hiện chỉ cần vài MiB; tương lai phải tính peak engine/assets/trace/build cache, RAM/VRAM và reserve trước chạy. Không tải Unreal/scene lớn/emulator trên máy hiện tại chỉ vì kế hoạch có nhắc tới chúng. Không xóa bằng chứng để lấy chỗ.

## Phụ lục A Yêu cầu và tiêu chí quan sát

### R01 Cô lập simulator (P0)

Chỉ kết nối instance SITL được nhận diện và cấp quyền; không dò hoặc fallback sang radio/drone thật.

Nghiệm thu: Thử endpoint sai, instance cũ và restart: lệnh bị từ chối; raw trace không có đích ngoài allowlist.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R02 Bay bằng tay (P0)

Gamepad/joystick với calibration, dead zone, expo, invert và sơ đồ kênh; bàn phím chỉ là đầu vào thay thế có nhãn.

Nghiệm thu: Axis sweep, held/repeat, mất focus, hot unplug và neutral-first; xem stick overlay cùng phản ứng autopilot/physics.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R03 Mode thực và mode yêu cầu (P0)

Training manual gồm Loiter/AltHold cho nhập môn, Stabilize cho nâng cao khi firmware hỗ trợ; không gọi tất cả là cùng một manual mode.

Nghiệm thu: Yêu cầu mode và heartbeat mode quan sát riêng; sai capability/GNSS/ownership thì từ chối, không hiện thành công từ ACK.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R04 Bay bán tự động (P0)

Guided takeoff, click-to-go, đổi cao độ/yaw, dừng giữ vị trí và RTL theo capability.

Nghiệm thu: Command→wire→mode/setpoint→pose; tốc độ/độ cao được giới hạn và có người giữ quyền rõ ràng.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R05 Bay tự động (P0)

Survey/corridor từ KML, upload/readback, AUTO, tiến độ thu nhận, kết thúc và review.

Nghiệm thu: Plan SHA/source/firmware/Home đúng; quan sát tuyến thực từ physics, không chạy animation theo waypoint.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R06 Tiếp quản và tiếp tục (P0)

Chuyển AUTO↔manual/assisted qua máy trạng thái; tiếp tục nhiệm vụ phải xác nhận vị trí và phần còn lại.

Nghiệm thu: Thử chuyển khi có gió, neutral sai, lệnh cũ và reconnect; không nhảy pose hoặc tự phát lại lệnh.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R07 Động lực học có tải (P0)

6DOF, mass/CG/inertia, actuator lag/saturation, thrust/torque, drag và pin có đơn vị/version.

Nghiệm thu: Analytic, convergence và A/B cùng profile/seed/firmware; đo gia tốc, dừng, hover power, motor headroom thay vì gán chậm tùy ý.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R08 Hiệu chỉnh Hera (P1)

Tách reference aircraft khỏi Hera đã đo; profile nguồn gốc CAD, mass/CG/inertia và flight log có version.

Nghiệm thu: So đáp ứng với dữ liệu độc lập theo miền hiệu lực; ngưỡng sai số phải được chuyên gia chốt trước collection.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R09 Gió và thời tiết (P0)

Gió nền/gust theo seed tác động lực; mưa/sương/ánh sáng tác động nhìn và camera ở miền đã công bố.

Nghiệm thu: Cùng seed tái lập disturbance; tắt VFX không thay lực; chưa có model wet-prop/electrical thì ghi unsupported.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R10 Mặt đất và va chạm (P0)

Mặt đất/collider đúng mét, tiếp đất và tiếp xúc cơ bản; vật thể nhìn thấy phải có trạng thái collision rõ.

Nghiệm thu: Probe xuyên đất/đồ vật, tunneling và hạ cánh; crash kết thúc bài hoặc tạo sự kiện có chính sách, không tự bay xuyên để diễn tiếp.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R11 3D cao cấp (P0)

Hera có tỷ lệ và silhouette được duyệt; PBR, ánh sáng/bóng, vật liệu, LOD, cảnh có chiều sâu và mốc khoảng cách.

Nghiệm thu: Duyệt 6 góc/3 ánh sáng/3 khoảng cách và camera payload trên GPU thật; rubric visual không có mục critical fail.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R12 Laptop và máy chiếu (P0)

Bố trí màn hội đồng sạch, operator/instructor panel riêng khi có extended display; mirror fallback một màn.

Nghiệm thu: Diễn tập đúng laptop/projector/cáp/resolution, kiểm từ hàng cuối; mất màn phụ không làm mất quyền hoặc focus input nguy hiểm.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R13 Âm thanh động cơ (P0)

Âm tổng hợp theo RPM từng rotor, harmonics, tải, khoảng cách và góc nhìn; limiter/mute rõ.

Nghiệm thu: So envelope âm với RPM/thời gian, motor không đồng loạt khi physics khác; speaker volume không được coi là SPL Hera đã đo.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R14 Camera mô phỏng (P0)

Gimbal/FOV/lens/clock/exposure/capture; tạo ảnh từ scene cùng timestamp/pose và metadata.

Nghiệm thu: Tách preview chất lượng tương tác với sensor output; biết ground truth, hash/index/file, dropped frames và exposure timing.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R15 Kiểm mapping đầu cuối (P0)

MAPPING51 làm nguồn AOI/profile/readiness; nối qua adapter mới tới simulator, không sửa module cũ.

Nghiệm thu: Route executed, trigger, exposure và file riêng; review ảnh thiếu/nhòe/footprint, đưa ra đề nghị refly có xác nhận.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R16 Bàn giáo viên (P0)

Chọn bài/tải/gió và fault; theo dõi input, sai lệch, quyền và sự kiện; chấm theo rubric.

Nghiệm thu: Chèn gió/mất video/CORS stale có timestamp; điểm có lý do, missing evidence không được chấm đạt.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R17 Đào tạo từ xa (P1)

Host simulator trên PC của học viên; giáo viên quan sát/chèn bài có quyền qua đường mạng riêng.

Nghiệm thu: Auth/role, latency/jitter/outage, revoke và session isolation; WAN không nằm trên inner control loop hoặc khiến stale input bị giữ vô hạn.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R18 Hồ sơ và phát lại (P0)

Giữ input/mode/setpoint/physics/telemetry/camera/audio/fault cùng clock domain và provenance.

Nghiệm thu: Replay chỉ đọc, tìm được sai lệch/timing; không lấy replay làm live, không suy cause từ ACK; bundle kiểm hash/semantic.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R19 Nhịp 1× và hiệu suất (P0)

Vật lý/control độc lập render; đo RTF/drift/jitter/frame age và resource ở workload đã khóa.

Nghiệm thu: Đạt gate pacing 1× kế thừa, không hạ speedup/cap500ms/precision hoặc bỏ physics frame; GPU thật đo visual budget.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R20 Quá tải và restart (P0)

Queue/storage có giới hạn, giữ raw và trạng thái incomplete; restart không tự nối quyền hoặc tiếp tục chuyến.

Nghiệm thu: Fault injection/process kill/low-space; dừng có chủ đích, không xóa bằng chứng hoặc báo hoàn tất giả.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R21 Cockpit dễ vận hành (P0)

Trắng/đen, vàng là nhấn phụ; vị trí mode/quyền/cảnh báo ổn định; thao tác chính ít bước.

Nghiệm thu: Walkthrough Plan→Preflight→Fly→Review; focus/keyboard/gamepad, tỷ lệ màn hình, cảnh báo không che điều khiển.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R22 Live trước hội đồng (P0)

Ba cách điều khiển, A/B tải/gió, một fault và post-flight review trong kịch bản 18 phút.

Nghiệm thu: Hội đồng chọn target hoặc seed mới; hành động truy được vào trace; bản ghi dự phòng có nhãn rõ và không tính live PASS.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R23 Asset và tỷ lệ (P0)

Mesh/collider/camera/terrain có hệ tọa độ, đơn vị, nguồn và quyền dùng; visual mesh không tự là collision model.

Nghiệm thu: Kiểm license/offline redistribution, datum và scale; không phóng đại địa hình trên đường physics hoặc hứa quyền cache từ URL public.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R24 Gói offline (P0)

Tất cả dependency/asset cần cho hội đồng được pin và lưu hợp lệ; không cần CDN/login/network khi demo.

Nghiệm thu: Cold start không Internet, cache empty phù hợp, không request ngoài; launch/diagnostic/stop có runbook và budget.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

### R25 Payload và sensor mở rộng (P1)

Chuẩn bị contract EO/IR/LiDAR, nhiễu/delay/bias và nhiều payload; chỉ bật module có model/test tương ứng.

Nghiệm thu: Mỗi sensor có ground truth và reported observation riêng; không biến RGB giả màu thành thermal radiometry hoặc LiDAR đã hiệu chỉnh.

Trạng thái: PLANNED / NOT_CHECKED cho SIMTRAIN52.

## Phụ lục B Work package và dependency

### G0 Khóa máy và workload

Phụ thuộc: Không. Vai trò: Lead + QA. Ước lượng: 0,5 ngày mục tiêu.

Đầu ra: Reference laptop/GPU/projector, profile reference, versions, scene và resource budget; đo lại baseline pacing.

Exit gate: Không có hardware/budget hoặc pacing chưa định lượng thì chưa chốt ngày demo.

### G1 Vòng kín 1× và hồ sơ

Phụ thuộc: G0. Vai trò: Physics/control. Ước lượng: 1–2 ngày, rủi ro cao.

Đầu ra: Chọn derivative mới qua oracle; manual input→AP→physics có trace và managed shutdown.

Exit gate: Không đạt 1× đúng workload thì dừng gate; sửa hoặc đổi cấu hình có benchmark lại, không chuyển sang animation.

### G2 Manual, assisted và tiếp quản

Phụ thuộc: G1. Vai trò: Integration/control. Ước lượng: 1 ngày.

Đầu ra: Loiter/AltHold/Stabilize theo capability; Guided, hold/RTL; state machine quyền và hot unplug.

Exit gate: Quan sát mode thực, no stale/duplicate authority; bài nhập môn hoàn thành từ đầu vào người dùng.

### G3 Mission và camera

Phụ thuộc: G1. Vai trò: Integration + sensor. Ước lượng: 1–2 ngày.

Đầu ra: MAPPING51 adapter, survey/corridor, gimbal, ảnh scene+metadata và review.

Exit gate: Upload/readback/AUTO/land/disarm/capture/file trace đầy đủ; bỏ ảnh được phát hiện.

### G4 Art direction và âm thanh

Phụ thuộc: G0. Vai trò: 3D/audio. Ước lượng: 2–3 ngày, có thể làm asset song song.

Đầu ra: Một bối cảnh luyện tập đẹp, Hera mesh, ánh sáng/LOD, shadow, camera follow/payload, RPM audio.

Exit gate: Offline art review có thể trước G1; ghép live và performance gate chỉ sau G1, không claim scene-preview là bay thật.

### G5 Giáo viên và lỗi

Phụ thuộc: G2, G3, G4. Vai trò: Integration + QA. Ước lượng: 1 ngày.

Đầu ra: Gió/tải A/B, fault CORS/video/input, scoring và replay.

Exit gate: Fault không che lỗi physics; điểm và incomplete có bằng chứng, không tự resume.

### G6 Nghiệm thu tích hợp

Phụ thuộc: G5. Vai trò: QA + lead. Ước lượng: 1–2 ngày.

Đầu ra: Functional/fault matrix, workload/GPU thật, offline cold start, dual-display và visual review.

Exit gate: Tất cả P0 của bản hội đồng đạt, không critical fail; Hera fidelity và remote P1 vẫn có nhãn đúng.

### G7 Tổng duyệt hội đồng

Phụ thuộc: G6. Vai trò: Operator + presenter. Ước lượng: 0,5–1 ngày.

Đầu ra: Ba rehearsal liên tiếp trên laptop/projector đúng; bản ghi dự phòng, launch/stop/review runbook.

Exit gate: Ba lượt đều đầy đủ trace và không critical fault; một lượt challenge target/seed mới.

## Phụ lục C Ngân sách nghiệm thu đề xuất

**M01 Vật lý và pacing:** Khả năng tính ≥1×; pacing wall-clock1×; kế thừa gate cũ, không tự giảm ngưỡng.

Cách đo: RTF, phase/drift, per-frame gaps/duplicates, cap clips và jitter theo cửa sổ/whole run. Điều kiện: P0 G0/G1 phải chốt cửa sổ/dung sai cùng reference; hiện gate cũ chưa đạt. Trạng thái PROPOSED / NOT_MEASURED.

**M02 Đồ họa:** Đề xuất60FPS ở1920×1080 output; p95≤16,7ms, p99≤33,3ms.

Cách đo: GPU thật, active camera+mission+weather/audio; shader warmup và cold start tách riêng. Điều kiện: Không áp số GPU headless; kiểm thêm1280×800 fallback công bố. Trạng thái PROPOSED / NOT_MEASURED.

**M03 Phản hồi UI:** Đề xuất p95≤100ms local input→feedback nhận thao tác.

Cách đo: Instrument input/action/render, không gọi API roundtrip hay ACK là control response. Điều kiện: Stick→pose/sensor và end-to-end video cần budget riêng sau G0. Trạng thái PROPOSED / NOT_MEASURED.

**M04 Camera và video:** Timestamp/index/pose/hash đầy đủ; actual/synthetic provenance đúng100%.

Cách đo: Ground truth camera pose và file inventory; publish frame age/drop counters. Điều kiện: Cadence/resolution/codec được chốt theo máy và profile, không âm thầm giảm để lấy FPS. Trạng thái PROPOSED / NOT_MEASURED.

**M05 Visual quality:** Không critical fail về scale, rotor, shadow, clipping, HUD; mục tiêu trung vị≥4/5 theo rubric.

Cách đo: Ít nhất3 người gồm operator và visual reviewer,6 góc/3 ánh sáng/3 khoảng cách. Điều kiện: Đây là target đề xuất, không chứng minh mô hình vật lý hoặc superiority. Trạng thái PROPOSED / NOT_MEASURED.

**M06 Rehearsal:** 3 phiên18phút liên tiếp, đủ manual/assisted/AUTO/fault/review.

Cách đo: Có1 lượt challenge mới,1 cold offline,1 đổi cấu hình màn hình; giữ cả fail. Điều kiện: Không dùng khoảng thời gian này thay ENDURE24h. Trạng thái PROPOSED / NOT_MEASURED.

**M07 Độ giống Hera:** Miền model và error tolerance được chốt trước validation.

Cách đo: Mass/CG/inertia/thrust/lag/drag/battery, dữ liệu tham chiếu ngoài tập fit. Điều kiện: Chưa có dữ liệu thì chỉ nghiệm thu reference simulator, không gán Hera-calibrated. Trạng thái PROPOSED / NOT_MEASURED.

**M08 Học viên:** Hoàn thành mục tiêu và xử lý lỗi đúng rubric, không có thao tác critical.

Cách đo: Checklist/trajectory/event/human review, thử với học viên chưa quen và operator. Điều kiện: Không suy hiệu quả chuyển giao bay thực từ điểm trong simulator. Trạng thái PROPOSED / NOT_MEASURED.


## Phụ lục D Sau bản hội đồng

**F1 Hiệu chỉnh và kiểm HeraHub** — yêu cầu R08; sau G7. Owner đề xuất: RtR hardware/physics/native; chưa gán người.

Profile Hera đã đo và adapter input/video trên thiết bị thật; giữ label engineering đến khi validation đạt. Trạng thái: kế hoạch, chưa triển khai.

**F2 Đào tạo từ xa** — yêu cầu R17; sau G7. Owner đề xuất: Network/security/training; chưa gán người.

Auth/role/session, instructor quyền hạn và đo latency/jitter/outage; simulator inner loop chạy local. Trạng thái: kế hoạch, chưa triển khai.

**F3 Sensor và payload nâng cao** — yêu cầu R25; sau G7. Owner đề xuất: Sensor/mapping; chưa gán người.

EO/IR/LiDAR có model riêng, ground truth và evidence; không đổi giả màu thành radiometry. Trạng thái: kế hoạch, chưa triển khai.


## Phụ lục E Rủi ro và cách ra quyết định

| Rủi ro | Tín hiệu kiểm sớm | Owner đề xuất và xử lý |
|---|---|---|
| Pacing AP–backend chưa đạt1× | G0 trace cả run, raw/clock và budget logging | Physics/QA: cô lập scheduling/transport/full-cost, giữ oracle/cap; cập nhật lịch nếu chưa quaG1 |
| Máy GPU/projector khác môi trường QA | Adapter/browser/driver/mode nguồn và resolution thực |3D/QA/operator: benchmark đúng máy, thử mirror/extend và loa; không lấy headless làmPASS |
| Asset Hera hoặc mixer không khớp | So CAD/render/layout với cấu hình AP/rotor channels | RtR hardware/3D: xác minh hoặc giữ label reference; không ngụy trang model |
| Dữ liệu hiệu chỉnh thiếu | Profile ghi provenance/calibration status | Physics/chuyên gia: nghiệm thu reference/engineering trước, không claim calibrated |
| Tràn trace/media/disk | Worksheet peak và thử quota trên root riêng | Integration/QA: admission/chunk/seal, capacity đủ và dừng giữ incomplete; không auto xóa |
| Live fault/lỗi mất focus trên máy chiếu | Rehearsal input, display hotplug và fault boundary | Operator/QA: abort/reconcile, backup có nhãn, không che failure hoặc tự resume |
| Làm quá nhiều scene/AI/sensor cùng lúc | P0 chưa có vertical slice nhưng backlog art/service mở rộng | Lead/chủ việc: bảo vệ ba mode + một scene + camera/review trước cácP1 |
| Kỳ vọng1× hoặc “như Hera thật” bị hiểu sai | KPI/model level trên cockpit và báo cáo | Lead/presenter: nói đúng miền hiệu lực, công bố benchmark/reference và claim cụ thể |

