# Bản đồ kiến trúc và trách nhiệm

## Ba đường không được trộn

1. **Workbench web lịch sử**: `npm start`, loopback 8788, planner/Plan-Fly-Review.
2. **Đường native tích hợp hiện tại**: Android WebView/Java bridge, Node companion
   trên 8896, RootWire MAVLink, ArduPilot SITL và physics backend.
3. **Viewer/nguồn media**: publisher trên 8895, canvas/WebCodecs, qualified receiver
   và review. Nguồn tổng hợp không phải camera gắn trên UAV.

```text
Android cockpit / native bridge
          | public UI + lifecycle + storage
          v
Node companion (8896) ---- payload/operator authority
          | RootWire, durable intent, actual RX
          v
MAVLink routing ---- ArduPilot SITL 4.7.1 ---- physics/sensor backend
                                                |
                                      qualified scene/clock
                                                v
Host publisher (8895) ---- decoder/warm-frame proof ---- Android viewer
          |
     journal / review / export / independent receiver
```

Trong lượt kiểm này, TCP native/direct thuộc Node RootWire. APK thực hiện UI,
HTTP bridge, input và lưu trữ; không suy ra APK đã có driver radio/MCU thực.
MAVLink ACK, mission readback, mode transition và ảnh camera là các bằng chứng khác nhau.

## Entry hiện tại

- `planning/vidlife12/runtime/root-owner-vidlife12.py`: owner cho candidate S01.
- `scenario-app09.py`: driver public Android UI, wait navigation 30 giây của S01.
- `root-owner-vidlife12-r02.py`, `scenario-app09-r02.py`: revision thử tiếp,
  wait navigation 60 giây; chưa có candidate/lượt SITL R02 được chấp nhận.
- `runtime/source/aeris_runtime/`: package 117 file của source hiện tại.
- `product/`, `product-companion-codec09.mjs`, `root-wire-media09c.mjs`:
  client/server lifecycle, media và routing.
- `assets/product-input-closure.json`: 154 input pins; mã/asset và fixture cần đúng byte.
- `assets/pipeline-writer-pins.json`: 200 writer sites, 14 owners,
  future reserve 60.686.336 B; không thêm writer ngoài contract.

## Guard và clock

Freshness clock/input/scene 250 ms; HostHealth 100 ms; UI/lease 200 ms;
client lifecycle deadline 1000 ms; flight freshness 1500 ms; hard heartbeat 3000 ms.
Speedup 1, catch-up cap 500 ms; fsync trước sensor/TX, không bỏ frame để đạt pacing.
Wait startup 60 giây là ngân sách chờ khởi tạo, không kéo dài tuổi hợp lệ của telemetry.

Node hrtime, Python monotonic, Android elapsed time và browser performance không
được so trực tiếp. Cần context/session/boot/frame và clock mapping đã đủ điều kiện.
Wall time, AP boot time và elapsed của test phải được báo riêng.

## Vòng đời quyền và hồ sơ

Cấp quyền cần nguồn/session đúng, input tươi và review/preflight hợp lệ. Mất link,
background, reboot hoặc quyền hết hạn phải thu hồi, không tự khôi phục quyền sau restart.
Khôi phục workspace và đọc hồ sơ cũ không cấp lại flight/payload authority.

Journal cần causal intent, durability, TX/sensor boundary, closure và receiver
verification. Raw prefix có CRC/SHA đúng vẫn có thể incomplete; không chèn footer
để biến prefix thành một recording được nghiệm thu.
