# HeraHub bench preparation — no hardware present

Current intake intentionally contains UNKNOWN/null. Run `python3 native/native88/bench/validate.py native/native88/bench/intake.json`; exit2 means missing inputs, not product failure and not a request to invent values. No software here sends to a physical vehicle. Complete controller/aircraft/radio/payload identities and agree budgets with RtR before bench. Android33/internal quad values are references, not Hera specifications.

| Gate | Setup / observation | PASS evidence required | Stop / FAIL condition |
|---|---|---|---|
| BH01 installation | Supported HeraHub OS/viewport, approved development APK | Installed SHA/certificate/permissions; source and SDK/firmware inventory | Unsupported API; missing identity; production claim from emulator |
| BH02 readonly | Bench safety configuration approved by RtR; no propellers for nonflight tests | Actual target/firmware/commit/typed parameters/Home/MSL and time/boot identity raw | Wrong target, stale data or changed boot; no automatic writes |
| BH03 input | MCU/HID/SDK channel, calibration revision | Neutral/deadzone/endpoints/inversion/button mapping trace; measured input latency against agreed budget | Stuck axis, lost focus/link or stale sequence must revoke; no automatic control restoration |
| BH04 video | One real camera stream and monotonic source timestamps | Codec/resolution/rate, frame age, decode/display latency and p95 budget; reconnect/rotation/background behavior | Frozen frame represented as live; unbounded queue/RAM; unknown time basis |
| BH05 single payload | Exact Phase One model/firmware/lens/SDK + gimbal | Discovery/capability; settings/gimbal commands target raw; exposure event and original file SHA/time/GNSS association | ACK called a photo; unsupported camera silently mapped; wrong-target action |
| BH06 two operators | Two stations, identity, agreed emergency/loss policy | Exclusive ownership, explicit consent, contested handover, disconnect/reboot, receiver-side enforcement | Two owners; stale grants restored; emergency policy unspecified |
| BH07 combinations | Qualify each payload alone before approved combinations | Electrical/power/link/thermal/mass/CG configuration supplied by RtR and same routing/media tests | Advertise four payloads from mock capability; target/slot ambiguity |
| BH08 HIL/field | Separate approved safety plan and pilots | Configuration-specific geofence/failsafe/return reserve/timestamp/real media and flight logs | Simulation presented as flight validation; missing calibration/reserve criteria |
| BH09 recipient | Exact exported bytes/recipient/nonce | Independent SHA/semantic receipt, raw control+passive stream, mission/session/closure; wrong file/replay rejected | Receipt from missing/tampered file or only review hashes |

Record per case: gate ID, configuration SHA, firmware/SDK versions, physical serials, operator/site, UTC+monotonic time basis, measured value/unit, agreed limit/version, raw artifact SHA, outcome PASS/FAIL/NOT_CHECKED and reason. Source declaration alone is not device attestation. Customer/flight acceptance remains outside this preparation.

Recommended order: installation→readonly→input and video→one payload→two stations→approved combinations→HIL/field→customer acceptance. No schedule, physical performance, model compatibility or NDAA claim is inferred.
