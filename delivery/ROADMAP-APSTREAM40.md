# APSTREAM40 roadmap supplement

14/10/2026; new supplement only, frozen canonical roadmap/SOT/source/candidate/ENDURE unchanged.

| Area | Current verified preparation | Next gate |
|---|---|---|
| Full protocol stream |Pinned299-message dialect/all layouts/CRC/vector/split checks; auxiliary sequence bridge, signed/opaque quarantine |Actual firmware/binary/dialect association; real traffic/rates/signing/authentication; unknown custom dialect policy |
| Firmware discovery |Fresh selected heartbeat, explicit one-shot REQUEST_MESSAGE, version/capability/source/UID mock checks; ACK diagnostic |Actual pinned AP announcement/request response and parameter encoding/count/read duration; recorded unsigned/signing policy |
| Recovery/routing |Wrongtarget, loss, boot/context change, duplicate conflicts, stale/writer/concurrency revoke; explicit new mock instance/readback |Actual disconnect/reboot/clock behavior and HIL routing/authentication; no implicit resume |
| Flight safety |Readonly typed config + separate incomplete preflight/rich failsafe/altitude |Actual AP-side state/cause/activation and typed fence upload/readback/enforcement contract; no Wh invention |
| Native/product |No Fly/native/app/candidate changes or new signatures |Android runtime/persistence/input/video then Hera bench/HIL/controlled survey; separate resource gates |
| Endurance |Prior ENDURE failure/evidence immutable |Separately authorized continuous campaign and independent raw acceptance; no aggregation |

Can continue bounded mock preparation without SDK. Actual SITL/emulator/build/signing remains outside current authorization. Preserve20GiB floor and all prior receipts; runtime gate requires fresh budget and explicit scope. Mock completion is not field-alpha/release or Ragas/DJI superiority.
