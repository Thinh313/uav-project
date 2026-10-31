# COCKPITVIDEO04 Builder handover

22 October 2026. **Combined milestone: NOT READY.** Production source is frozen; this handover authorizes no new execution, retry, signing or source modification.

## Delivered architecture

The isolated cockpit retains mission planning, preflight, upload/readback, Fly and review while Android receives and decodes video. Encoding occurs only in the explicit host Chrome publisher at `http://127.0.0.1:8873/publisher`; the Android panel does not instantiate a publisher, encoder iframe or local codec probe. Video remains synthetic, not a camera exposure or radiometric measurement.

- `pilot/cockpitvideo04/app.mjs`: curated integration, existing API contracts, readonly lease observation and immutable report-sidecar response. Generation02 changes exactly one import from frozen Flight02 to isolated Flight03.
- `bootstrap.js`, `ui.mjs`, `ui.css`: existing native companion lifecycle, cockpit integration, truthful frame freshness and capture receipt propagation. Foreground/restart never restores authority automatically.
- `media-panel.mjs`, `media-panel.css`: receive/decode only, explicit start/stop, one measurement per document, retained failed results, snapshot/onCapture, AP identity latched when measurement begins. Capture success requires `SYNTHETIC_REFERENCE_COMMITTED`, not an authority-ended receipt.
- `evidence.mjs`: bounded durable hash-chain journal, complete-write/failure poisoning, raw report SHA and source identity binding, conservative same-host monotonic flight/payload point overlap. Host-source visibility remains a separate observation; overlap does not certify continuous airborne execution.
- `resource.mjs`: 28 GiB runtime guard, 250 ms observations and 15 s decline forecast; no threshold waiver. `stage.py` assembles only curated derived assets, not a project copy.
- `flight/flight03.mjs`, `flight/runtime03.py`: isolated generation02 admission and pin wiring. Control, Home/freshness, authority, fault, physics and speedup=1 behavior remain inherited/frozen. Original cap9 and original pins are unchanged. New cap11 admits only ordinals10/11 and rejects12 before allocation; admission is not a promise to execute.
- `fixture-generation02.mjs`, `pins-generation02.mjs` and corresponding tests: already executed exclusive preparation. Do not rerun over their existing evidence or fixture.

## Frozen source and data

`evidence/field02/cockpitvideo04/generation02-flight-pins.json` SHA256:
`677ddc00cf02dcdacdbd9a8ccff0bb49a684b2ec3b1875f6b2000c5e1a2c92df`.

The 13,418-byte canonical manifest binds101 files, all nine prior SITL request identities, all57 original flight pins and13 archived generation01 source files. Its bytes independently match frozen `stable()+newline` serialization used by the runtime gate. No historical manifest was overwritten.

`evidence/field02/cockpitvideo04/builder-source-freeze02.json` SHA256:
`5f092f5b3183306be250ca8b960ec09cdaddc06a8847c8b18f9a42d5db506d3d`.

It records19 own source files,101 zero-drift pins and93 unchanged prior source files at freeze time. Exact source hashes are in that artifact. Generation01 files are retained under `generation01-source/` with `generation01-source-archive.json`.

Workspace02 is a14-file data-only fork with one valid appended workspace revision. Three horizontal KML offsets are exactly3× around unchanged Home; altitude10 m, speed2 m/s, camera/commands and other mission semantics are unchanged. Existing compiler result:80.686704 m /40.343352 s nominal, **not a200 s guarantee**. Model SHA `4439435070abf9f78f81946741e4f14e82bdd10f9ce7dffad5cce6235bff546e`; plan SHA `9112c3b2bc739eac39862c66239dca3e4beec6ee200d052ec6860a07bc9bf049`.

## Historical launch recipe, not an instruction to rerun

From the repository root, a separately authorized future run would first check disk/admission and assemble the derived stage only if absent:

```sh
python3 -B pilot/cockpitvideo04/stage.py
node pilot/cockpitvideo04/app.mjs evidence/field02/cockpitvideo04/NEW_EXCLUSIVE_OUT --allow-sitl '--workspace=/Users/os/Downloads/AI technique/aeris/evidence/field02/cockpitvideo04/workspace02'
```

The actual generation02 CLI used reserved `host-app03`/`host-app03-admitted` outputs. Never reuse those names or create a new session from this document. The derived `.stage` is final-cleanup material; Contractor removes it at closure. Its presence in the historical source-freeze snapshot does not mean it is retained as a deliverable. The source recipe is retained. Fixed control/media ports are8872/8873, matching the unchanged development APK. No APK/native build or signature was produced by this task.

## Executed Builder mock commands and recorded results

These are the historical checks, **not a rerun list**. Their exclusive `wx` result paths already exist. Paths below are relative to the repository root; all evidence is under `evidence/field02/cockpitvideo04/`.

| Executed command | Result artifact | Result |
|---|---|---|
| `node pilot/field02/host-tests.mjs evidence/field02/cockpitvideo04/builder-frozen-contract01.json` | `builder-frozen-contract01.json` |11/11 lifecycle, false-confirmation and operation-context mock checks |
| `node pilot/cockpitvideo04/helper-tests.mjs` | `builder-helper-mock01.json` |5/5 initial helper/UI-function checks |
| `node pilot/cockpitvideo04/helper-tests02.mjs` | `builder-helper-mock02.json` |6/6 final helper/UI checks, including strict position/context freshness |
| `node pilot/cockpitvideo04/panel-tests.mjs` | `builder-panel-mock01.json` |5/5 receiver lifecycle, measurement and capture mock checks |
| `node pilot/cockpitvideo04/http-tests.mjs evidence/field02/cockpitvideo04/builder-http01` | `builder-http01/results.json` |10/10 actual localhost HTTP protocol-mock checks; only mock record `mf04a83aa57c6445d8c91`, closed accepted as MOCK |
| `node pilot/cockpitvideo04/generation02-tests.mjs` | `builder-generation02-mock01.json` |6/6 exact source normalization, cap/confirmation, fixture and old-pin checks |
| `node pilot/cockpitvideo04/generation02-real-pins-tests.mjs` | `builder-generation02-real-pins01.json` |3/3 real module readonly pin/serialization/inheritance checks, no connect or process launch |

Data preparation used `node pilot/cockpitvideo04/fixture-generation02.mjs` and `node pilot/cockpitvideo04/pins-generation02.mjs`; receipts are `builder-generation02-fixture01.json`, `builder-generation02-pins-receipt01.json` and `builder-generation02-pin-serialization.json`. Curated stage assembly and syntax/AST checks are recorded in the two Builder source-freeze artifacts. These are preparation/structural checks, not flight tests. The HTTP rehearsal preceded the final targeted freshness/sidecar-flush repairs; the final targeted helper and independent QA checks cover those repairs, not a second full HTTP rehearsal.

Independent QA: generation02 static5/5 and emitted-pin pre-runtime4/4 pass in `qa-generation02-static01.json` and `qa-generation02-pre-runtime-gate01.json`. Earlier integrated helper8/8 and capture4/4 checks passed. Neither mock counts nor pin verification confer combined runtime acceptance.

## Actual outcomes and remaining gap

Contractor-owned generation01 nominal `s48d15d007cba435b87c9` completed the mission with accepted flight evidence and Android host-video29.8982 FPS, P95 upper59.2769 ms and start-to-fresh261.1 ms. There was **no qualified airborne payload point inside the measured AUTO window**; the relay interruption was outside that window. In-window recovery is NOT CHECKED.

Generation01 attempt02 `s087098073574424eaf7d` landed before the airborne guard; capture was refused and the retained flight is accepted:false. **No actual AP reboot with an unexpired payload lease was demonstrated.**

Generation02 had two emulator admissions refused `UNSTABLE_DISK_TREND` before launch intent or AP allocation. The sandbox `host-app03` EPERM incident remains preserved. `host-app03-admitted` was cleanly closed. No generation02 AP flight or combined payload/video/fault acceptance is claimed. Resource admission refusal is not a product PASS or a substitute runtime scenario.

Remaining required proof is one qualified airborne payload/capture point during the measured video window, recovery interruption inside that window, and a distinct actual AP reboot while a payload lease is unexpired followed by durable invalidation and rejection of old authority. Missing scenarios stay NOT_CHECKED; this handover grants no extra budget or automatic retry. No Hera/Phase One/real-camera/radiometry, production signing or physical controller compatibility is certified. Root owns final process/port closure, preservation and cleanup attestations. Original source/candidate, ENDURE, FIELD02, HOSTVIDEO03 and native history were not modified by this Builder.
