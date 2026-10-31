# FIRMWARE38 — completion and verification

14/10/2026. **DONE in the scoped mock/replay preparation.** Verdict: `MOCK_CONTRACT_VERIFIED`. Specification, implementation and separate cold verification were performed by one agent, with a separate upstream serializer/parser; this is not independent review or real firmware/hardware acceptance.

Delivered a versioned firmware/capability contract, typed readonly parameter reader, Copter-specific failsafe/fallback graphs and explicit Home/Origin/Terrain/AMSL altitude mapping. The reference source says ArduCopter 4.7.1; its 20 source/schema files are pinned. No association of this source with the existing SITL binary or Hera is claimed. Announced UID/board/custom bytes are explicitly synthetic; no actual device identity was discovered.

The contract rejects stale/wrong identity/source/build/capabilities and contradictory encoding flags. Modern C-cast/bytewise signals are distinct. The exact-source legacy PARAM_FLOAT exception is explicit and cannot be borrowed by unknown/generic firmware. Classic parameter integer types and REAL32 are decoded from raw bytes; full 32-bit bytewise values preserve their bits, while ambiguous C-cast integers and classic 64-bit containers are refused. Named read index65535 is handled, with type/range/count consistency and fresh one-pass process-local witnesses.

Mapping preserves separate GCS/RC/battery actions and fallback candidates, FS_OPTIONS/context branches, AP-side guest clocks and strict timeout boundaries. Battery thresholds stay in mAh/V; no fabricated Wh or real trigger/execution is produced. Altitude uses AP Location::AltFrame, reviewed datum/reference IDs/elevations/points, uncertainty and separate active floor/ceiling masks. Mixed frames convert explicitly; changed Home, missing/stale reference or a terrain value at another point remains unknown. The assessment is altitude-only and does not certify complete geofence enforcement.

| Requirement | Coverage | Result |
|---|---|---|
| R1 contract/identity/capability/source admission | Exact announcement, source-bound legacy exception, conflict/stale/build/UID/board/boot negative cases | PASS mock |
| R2 AUTOPILOT_VERSION codec | Upstream pack/decode/CRC and uint64 precision vectors | PASS mock |
| R3 typed parameter semantics | Integer/REAL32 C-cast/bytewise, NaN-shaped bits, precision/refusal/type tests | PASS mock |
| R4 readonly lifecycle | 28 typed values, index65535/count consistency, partial/change/firmware update/loss/stale/writer/live-proof gates | PASS mock |
| R5 failsafe/action/options/units | GCS strict equality/trigger/latch; RC/AUTO/Guided/ground/landing/battery/EKF branches and preserved fallback graphs | PASS mock |
| R6 altitude/reference/activation | Home/Origin/Terrain/AMSL/mixed bands, review/datum/clock/uncertainty/floor and wrong-domain cases | PASS mock |
| R7 corpus/oracle/regression | Semantic tamper bites, cold replay and original 41+33 exact outcomes | PASS mock |
| R8 integrity/resources/history | All prior protected SHA and ENDURE inventory, disk/budget/import/directory checks | PASS |

**8/8 requirements** met within the explicit offline scope. Runtime/device conformance is deferred, not included in this percentage.

Current-source results:

- `logic3.json`: **96/96** checks pass. This includes codec/type/precision/witness/lifecycle/source-branch tests and two aggregate regression checks.
- `replay4.json` + `corpus4.json`: **54/54** scenarios match, **7/7** semantic/hash tamper bites rejected. Separate cold replay reproduces the full receipt exactly.
- `oracle-check2.json`: **41/41** upstream/independent raw-byte checks pass: 8 firmware/version vectors and 33 typed-parameter vectors. These overlap logic tests and are not additional flight scenarios.
- MAVFLIGHT37 **41/41** and APFLIGHT36 **33/33** cases reproduce their original replay receipts exactly, into the new namespace only.
- `verification1.json`: **14/14** verification gates pass; JavaScript syntax checks pass with zero errors. APK/build/typecheck/lint/SITL/emulator/device acceptance is NOT_CHECKED.

**13,551/13,551 protected paths retain their expected SHA; zero deltas or missing files** in that inventoried scope. ENDURE's 5,051-file inventory is unchanged. This includes RESTORE41 history and MAVFLIGHT37 artifacts/manifests. Prior missing-path incidents and failed ENDURE verdicts remain historical and byte-identical; no interval is recombined or promoted to 24-hour acceptance. No continuous original-path presence is asserted.

At verification the new namespace occupied **7.71 MiB**, within the scoped 8 MiB budget, and free disk was approximately **27.16 GiB**, above the 20 GiB floor. No dependency install, project copy, scratch/cache/build directory or temporary output requiring removal was created. Bounded test oracles/receipts are retained; no user data was deleted. Final artifact fingerprint verification also checks the namespace budget/floor.

No frozen source/candidate/trust/canonical SOT edit, native/Fly integration, actual transport send, APK/software build, SITL/emulator launch, signing or ENDURE restart occurred. Outgoing buffers contain named PARAM_REQUEST_READ only. Physical execution, real identity, firmware association and authentication remain unproven.

The first corpus/replay receipt failed a wrong-build test because its fixture announcement and reviewed contract shared an array. Deep cloning now changes only the announced fixture; `corpus1.json`/`replay1.json` remain intact. Earlier pass receipts precede the final framed-announcement and warning/landing branch fixes; they are not substituted for the current source-bound receipts.

Limitations: frame-boundary API (one unsigned frame, not a new mixed-stream transport); conservative 1500ms binding/readback window; primary analog-current battery profile; generic bytewise protocol does not inherit AP policy; unsupported classic 64-bit params; source interpretation does not model all firmware scheduling/backends/build features or multi-failsafe interactions. Mode-switch/fallback/conditional-gripper/terminate outcomes remain possibilities, never proven effects. No equivalent APFLIGHT36 Wh-based normalized config is fabricated.

Next gate: an isolated adapter/framer and read-only discovery test against the actual pinned AP binary, including announcement/source association, parameter encoding/type/index and altitude/failsafe contexts. Live/SITL/native work requires its own user authorization; no automatic rollout/signing follows from this result. See `delivery/ROADMAP-FIRMWARE38.md`.

Artifacts: TIP and ADR-051; source under `pilot/firmware38`; source pins/interpretation, append-attempt corpus/replay/logic/oracle and cold verification under `evidence/firmware38`. `artifact-fingerprints.json` binds all new artifacts, while old manifests remain untouched. Current checks: `node pilot/firmware38/tests.mjs`, `node pilot/firmware38/replay.mjs`, `python3 -B pilot/firmware38/oracle.py js-vectors3.json`, `python3 -B pilot/firmware38/verify.py`. Receipts append; verification binds the accepted logic3/replay4/oracle-check2 inputs and does not silently select a changed source or newest unreviewed run. Preparation refuses existing generated references instead of overwriting them.
