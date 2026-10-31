# SITLDISCOVERY41 — actual AP full-stream discovery / loss / reboot

14/10/2026. **DONE within isolated disarmed readonly SITL scope.** Verdict: `SCOPED_REAL_SITL_VERIFIED_WITH_LEGACY_COMPATIBILITY_GAPS`. Sequential specification/build/verify by one agent; cold replay/upstream tools are separate invocations, not independent review. No frozen app/candidate/ENDURE edit or software signing.

## Actual result

The existing official static Linux x86_64 ArduCopter binary was executed in one resource-bounded owned Docker container on this Mac. Binary SHA256 is `011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482`; observed AUTOPILOT_VERSION is4.7.1 / numeric67568127 / official type255, custom commit `dbe79216`. This matches retained official download metadata and full commit `dbe792162d06cab66c3475fd5556bf7a120f119e`. Association is between observed announcement, locally owned binary/process, banner and captured metadata; no cryptographic attestation or bit-reproducible source build is claimed.

Three actual TCP sessions completed on loopback5794 with system42/component1: initial discovery, manual reconnect to the same AP process, and discovery after actual owned Docker/AP restart. Each session sent one GCS heartbeat, one REQUEST_MESSAGE512 for148 and eight named PARAM_REQUEST_READ requests. **24 actual typed parameter reads**, no PARAM_SET/ARM/mode/mission/reboot command. Reboot was performed by restarting only the verified owned container; PID/start changed while container/binary remained the same. No SDK/Hera or physical payload was involved.

TCP close revoked the previous process-local readonly witness; the old instance could no longer produce heartbeat/discovery/read output. Manual reconnect and post-reboot created new instances and explicitly repeated discovery/readback. A deliberately injected wrong-sender version was quarantined at the parser seam and could not replace firmware; this was **fault injection**, not an actual second aircraft/network responder. Old-process-context refusal is tested in unit fault scope.

Observed parameter examples(not recommended aircraft settings): MAV_SYSID42(type4), SERIAL0_PROTOCOL2(type2), FS_GCS_ENABLE0(type2), FS_GCS_TIMEOUT5(type9), FENCE_ENABLE0(type2), FENCE_TYPE7(type2), BATT_MONITOR4(type2), FS_OPTIONS16(type6). All replies reported1369 parameters and named-read index65535. Encoding is C-cast via the exact source-bound legacy PARAM_FLOAT capability; remainingWh and actual failsafe/enforcement are not inferred. Failsafe/geofence enable defaults were disabled in these disarmed tests; no enforcement/airborne safety acceptance is claimed.

## Compatibility gaps found and isolated handling

1. UART/TCP emits startup ASCII before MAVLink. First actual capture contained107-byte `Init ArduCopter V4.7.1 (dbe79216)`/boot text; AP40's strict64-noise-byte framer rejected it with NOISE_BOUND. That raw failure remains. New41 only permits a bounded1024-byte printable initial preamble in the pinned owned-SITL scope, retaining exact bytes; a nonempty prefix must contain the reviewed banner before the first MAVLink marker. It then passes unmodified MAVLink bytes into the old full framer. This is not a generic noise tolerance or hardware identity check.
2. Actual firmware announces UID0, board/vendor/product0, UID2 containing the container hostname bytes, capabilities64495. Source GCS_Common explicitly sets the64-bit UID to0. The original F38/AP40 mock contract refuses UID0; an offline projection of exact actual version bytes independently reproduces `FIRMWARE_CONTRACT:unknown UID`. Historical guard/source stays unchanged. New41 admits this zero-UID announcement only under the owned-disarmed simulator manifest(binary/CID/PID/start/context). UID2 is an observation, not a hardware serial/authentication credential.

Actual network bytes have outer `OBSERVED_OWNED_SITL` provenance. The older framer's internal mock origin label is not promoted to actual evidence alone; TCP TX/RX/write-return logs and container metadata supply the actual path. Offline AP40 projection is explicitly labeled and was never sent. Parameter snapshots are historical readonly observations, not operationally valid preflight configuration or restored authority.

## Evidence / verification

| Check | Result | Evidence |
|---|---:|---|
| Actual network/loss/reboot checks |7/7 PASS |`run03/attempt02/qa.json` |
| Sessions / actual parameter reads |3 /24 |Three raw JSONL and snapshots |
| Cold actual raw replay |113 capture rows /94 decoded AP frames, matching bytes/types/values |`raw-replay1.json`; three sessions exactly reproduced in verification |
| Readonly TX whitelist |30 actual packet writes:3heartbeat+3version requests+24parameter reads |Raw TX intents/write returns; cold reserialization |
| Unit/fault checks |19/19 PASS |`unit1.json`; manifest/UID scope, preamble bounds, stale/loss/oldcontext/build/armed refusal |
| Original36/37/38/39/40 corpora |33/33,41/41,54/54,40/40,44/44 exact |No old output write |
| Verification gates |24/24 PASS |`verification1.json` |
| Syntax |5JS +3Python valid |No build/install/lint/typecheck/full CI claim |
| Preserved historical scope |13,660 protected paths,0missing/changed SHA; ENDURE5,051-file inventory unchanged |Before/verification/final preservation |

R41-01..07 implemented/verified7/7 within named owned-SITL scope. Counts are not independent flight trials, product readiness percentages or Ragas/DJI comparisons. Readonly simulator discovery is now observed; full F38 policy/preflight/fence upload/enforcement, physical payload/video/input, Android/Hera, flight and production release remain NOT_CHECKED. AP40 source itself remains mock-only and rejects the observed preamble/UID0; its old READY scope is not rewritten.

## Failures / incidents preserved

Launch run01 exited125 before AP ran; its stderr was not retained by the initial helper, so the exact original reason is UNKNOWN. Run02 retained actual daemon error: compressed logging cannot use max-file1. A harmless /bin/true platform probe succeeded; no architecture-cause claim is made from it. Corrected run03 used two2MiB log files(total4MiB) and launched the pinned binary/image; no image pull or rebuild.

First QA stopped before connecting due argv parsing in lifecycle inspect; its failure receipt remains. The following QA connected and recorded the107-byte startup preamble before NOISE_BOUND. New attempt02 has separate raw/snapshot files and passed after the narrow preamble handling. There was no automatic retry of a failed MAVLink transaction; new test attempts were explicit scoped harness invocations and failed receipts were not overwritten.

Final `docker stop` succeeded; immediate auto-remove assertion raced daemon removal. Readonly follow-up confirmed removal, then a separate finalize receipt performed required image prune without another stop/restart. Original failure result remains. No other container/volume was stopped, removed or pruned.

## Resources / closure / limits

Owned simulator: exact imageID`sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55`, CPU1/RAM256MiB, cap-dropALL/no-new-privileges, readonly source/defaults mounts, isolated EEPROM state, loopback5794, speedup1 argument and bounded logs. Existing image metadata is arm64; the actual executable is static x86_64 and ran under Docker Desktop's emulation. No Hera performance or1× pacing result follows from these tests.

At cold verification host free23.00GiB, above20GiB. New code/evidence allocated2.69MiB, under32MiB; owned runtime state16KiB, under128MiB. Earlier before gate had24.57GiB. Do not attribute all host free-space change to this small module; other host activity was not measured. Final floor/fingerprint receipt accompanies delivery.

Owned container stopped/auto-removed, TCP5794 closed, all test sockets/processes ended. Docker image prune receipt is retained. No whole-project copy, scratch dependency/SDK/emulator/APK/Next/build artifact, tmp install, software signature or persistent preview was created. Tiny isolated runtime state is intentionally retained in the project as evidence; no user data deleted. ENDURE and old failed intervals/history remain immutable; no launch/retry/selection/24h acceptance.

File-based preservation is endpoint integrity, not continuous original-path presence across earlier restoration incidents. Fsync raw receipt success is not physical power-loss durability. Unsigned loopback/source ownership is not radio authentication; matching request/response has no on-wire nonce and does not prove cryptographic causality. AP guest time and local Node receipt time are not scaled/merged. Receipt clocks are local observations, not one-way latency measurements.

Files: `pilot/sitldiscovery41`, `evidence/sitldiscovery41`, TIP/ADR054/this report/roadmap supplement. Canonical frozen SOT/roadmap/app/candidate/trust not reconciled. Next is separately scoped actual preflight/typed fence/failsafe validation or native integration preparation; no automatic Fly integration/signing or flight authority.
