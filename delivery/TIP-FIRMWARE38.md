# FIRMWARE38 — pinned mock firmware/capability, typed params and safety mapping

14/10/2026. User authorizes isolated mock/replay preparation, not APK/SITL/emulator/signing. Create pilot/firmware38, evidence/firmware38, ADR-051 and completion/roadmap supplement; old modules/candidates/source/ENDURE/canonical SOT immutable. Existing Node/Python stdlib only. No transport or parameter/flight writes. Check >=20GiB plus 16MiB headroom before artifacts; new namespace <=8MiB. No large builds/copies/installs.

| REQ | Acceptance criterion |
|---|---|
| R1 | Versioned contract binds exact local source bundle, synthetic target/session/boot/link and announced AUTOPILOT_VERSION identity/version/custom bytes/UID/capabilities; missing, stale, mismatched or conflicting encoding signals refuse admission. UID/version are not authenticated hardware evidence. |
| R2 | Add isolated binary AUTOPILOT_VERSION codec; compare with existing upstream generator/parser and preserve uint64 capability precision. Old MAVFLIGHT37 stays intact. |
| R3 | Read-only PARAM_VALUE supports typed 8/16/32-bit integers and REAL32, C-cast and bytewise semantics; decode bytewise raw bits even when float bits encode NaN. Reject unrepresentable/ambiguous C-cast large integers, 64-bit classic params, unknown types/encoding and invalid names. |
| R4 | Pinned legacy PARAM_FLOAT requires exact source-backed exception, never a generic fallback. Named index65535 is permitted; other index/count/name/type conflicts remain unverified. Bounded one-pass mock readback/journal, invalidation on change/loss/stale/writer uncertainty, no resumed authority. |
| R5 | Preserve Copter-specific GCS/RC/battery/EKF/fence action graphs/options/context, disabled thresholds and battery mAh-vs-Wh distinction. Include strict GCS timeout/equality/latch, AUTO/Guided/landing/pilot/disarm exceptions, fallback possibilities and unknown inputs; execution always unproven. |
| R6 | Fence altitude/type/options/autoenable/margins map without confusing Location::AltFrame with MAV_FRAME; bounded, datum- and boot-bound Home/Origin/Terrain references, unsupported/unknown/mixed references and floor activation remain explicit. No silent source datum conversion. |
| R7 | Corpus replay and semantic tamper bites cover positive/negative contracts/typed params/safety/altitude; cold separate replay and upstream byte oracle agree. Replay original 41 MAVFLIGHT37 and 33 APFLIGHT36 cases into new evidence only. |
| R8 | SHA-check all prior protected bytes including MAVFLIGHT37 and restoration manifests before/after; retain failures/attempts, source pins and current-source receipts. Resource/operational flags verified. |

Single-agent specification, implementation then separate verification; no independent review claim. User already authorized this concrete isolated scope. Exact local source version is reference-only and is not assigned to the existing SITL binary or Hera. Contract data remains synthetic; no promotion into canonical facts or ENDURE acceptance.
