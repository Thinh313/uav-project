# Controlled Android restart and CPU diagnostic

The original owned emulator uses two virtual CPU cores and 2 GiB RAM. Android report app05/media/report-01 measured 23.48 displayed fps against a 24 fps target; p95 source-to-canvas upper bound178.26 ms met the300 ms target. There were705 consecutive measured encoded frames with no receiver loss. Publisher stage evidence points to production/encode/credit scheduling, not missing received frames.

Use the already-budgeted second emulator launch only after the current corridor mission closes and emulator01 records a clean explicit stop. Reuse the same AVD userdata and cached image, keep2 GiB RAM, 720p30 VP8, queue caps and host source unchanged, allocate four virtual CPU cores for one declared hardware diagnostic. Preserve both configurations and reports. The admission remains31 samples at29 GiB, guard21 GiB and floor20 GiB; each launch remains bounded toone hour. No image download or additional AVD copy. This also supplies an actual Android restart persistence check.

A changed CPU allocation is not an algorithm improvement and cannot qualify Hera/Xiaomi hardware. A faster result is evidence for this emulator configuration only. Host load and thermal conditions are not fully controlled, so do not claim a causal CPU-only benchmark from one pair. No additional APK build or production signature is authorized or needed.
