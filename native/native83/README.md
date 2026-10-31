# NATIVE83 · isolated Android / owned ArduPilot SITL

Accepted development APK05 and evidence are indexed by `delivery/NATIVE83-LATEST.json`. This is an engineering cockpit inside the reviewed native shell, not physical Hera acceptance or final commercial Fly/map/history UX. No RAGAS source is used.

## Paths and trust boundary

- `src/.../Workspaces.java`: native SAF bundle/retained generations. Immutable DraftStore chains, manifest SHA, bounded import, stage→semantic check→explicit activate. No cleanup/authority restoration.
- `ShellActivity.java`: offline WebView + fixed allowlisted Java loopback API. Each Activity instance has a new nonce; no restored grants. SAF Activity results are handled natively.
- `bridge.mjs`: local127.0.0.1:8846, secret published only after listen, native nonce and foreground lease, no configurable hardware target. Fixed simulator TCP5883/sysid42/compid1.
- `runtime.py`: task-owned pinned Docker/binary/config, internal quad speedup1, no image pull/build at launch, bounded lifetime/storage, owned closure only. Exact firmware4.7.1/dbe79216 qualified; no source-build attestation/Hera calibration.
- `link83.mjs`/`takeoff83.mjs`: immutable qualified43/63 adapters plus separate geometric TAKEOFF witness. Full mission includes pre/postarm readback/Home confirmation. ACK never execution or photos.
- `raw_verify_final.mjs`: separate raw/CRC/chain/mission/geometric review verification, not trust in online summary. Three semantic receipt mutations are refused.

## Operation

One local bridge at a time: `node native/native83/bridge.mjs sitl`, from project root. Existing token or occupied port refuses startup; do not remove a live/stale token blindly. Only owned emulator5582 can be reverse-mapped to8846. Explicit development launch supplies current ephemeral token via intent; do not publish that token. Native recreation/background/AP loss revokes grants; restart needs a fresh inspected session. No physical USB/HID/radio route exists here.

Android emulator/runtime was closed and its downloaded SDK/ZIP/chunks removed after acceptance; AVD, all data and receipts remain in `.local/native83-android/avd`. Initial provisioning/launch/build and acceptance drivers are single-attempt audit harnesses with exclusive outputs. Do not rerun them over existing receipts/AVD; use a new reviewed evidence overlay to resume the retained AVD. Host bridge has an8-attempt actual-SITL budget in this acceptance namespace. No automatic failed-transaction/campaign retry.

## Resource and archive scope

Host floor20GiB; Android admission30–32GiB and monitoring stop21GiB. OwnedAP admission21.25GiB; bounded journal16MiB/run. Android body256KiB,512records/64MiB per journal,8MiB archive input/expanded bound,16 retained generations and new-generation quota admission. No automatic evidence deletion. SAF returned-byte readback does not prove arbitrary provider powerloss durability. Android archive contains mock +SITL plan/review journals; host raw/APstate are separate referenced evidence.

Actual faults in this task were disarmed process/socket/reboot tests, not in-flight physical failsafe. Real HeraHub/MCU/HID/video/radio/PhaseOne/multi-payload/dualoperator/HIL/flight, renderer performance, SIM32 pacing and ENDURE remain separate gates.
