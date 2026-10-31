# Synthetic macOS H264 producer

Uses installed macOS VideoToolbox/CoreVideo/CoreGraphics/CoreText. No camera,
asset download, ffmpeg, media file replay or SDK dependency. The generated
moving inspection scene is labelled `SYNTHETIC LIVE` in every rendered frame.

Build: `python3 native/betastability02/host-source/build.py` from repo root.
The script requires20GiB and removes its own `.swift-cache` after compilation.
The executable is `native/betastability02/host-source/aeris-native-source`.

Protocol: persistent process; stdout is binary only. Every packet is8bytes of
big-endian uint32 JSON length then uint32 H264 length, UTF-8 JSON then encoded
bytes. JSON<=65536bytes; encoded bytes<=2MiB. Initial `kind:hello` has zero data
and reports actual `hardwareAccelerated` from VideoToolbox, or null on unknown.
Stderr is diagnostics, never protocol. No automatic restart is implemented.

Stdin is newline-delimited JSON<=4096bytes per request. Request has only
`frameId` (nonnegative integral strictly increasing), `timestampUs` (nonnegative
integral strictly increasing), optional `forceKey` (actual JSON Boolean).
First frameId/timestampUs may0. Limits: frameId<=100million, timestampUs<=9e12,
150000frames/process. `timestampUs` is caller PTS echoed into the packet and
H264 encoder, **not a native/host clock calibration or physical exposure**.
Parent must mark source-request time before submitting request and retain clock
bounds. One request at a time avoids introducing an unbounded input queue.

Each successful response: `kind:frame`, same IDs/PTS, `type:key|delta`,
`renderMs`, `encodeMs`, `nativeTotalMs`, `sourceKind:SYNTHETIC`, actual
hardware property. Durations use `DispatchTime.uptimeNanoseconds`.
`renderMs` includes pixel-buffer allocation+CoreGraphics rendering;
`encodeMs` covers submission through encoded callback+AnnexB conversion;
`nativeTotalMs` ends before JSON packet serialization/stdout write. Parent
request-to-complete-packet span includes IPC, native stages, serialization and
pipe delivery. Neither this nor canvas time is photon latency.

Profile is fixed1280x72030FPS, H264 Baseline3.1 `avc1.42001f`,4Mbps target,
real-time, no reorder, keyframe<=30frames/1second or force-key. This source does
not schedule30FPS by itself: the parent must pace requests without hidden skips.
SPS+PPS are prepended to each key packet and every NAL uses AnnexB start codes.

Malformed/unknown/oversize/order/type/truncated input fails closed with one
`kind:error` packet and exit2. Codec error/2second callback timeout also exits2.
