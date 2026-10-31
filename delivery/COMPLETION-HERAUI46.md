# HERAUI46 completion · 2026-10-15

STATUS: DONE within host UI/mock/replay scope. OVERALL: READY for host engineering review. Actual HeraHub/USB/SDK/Android/emulator, real calibration, control latency and physical flight NOT_CHECKED. Single-agent specification/build/verify, not independent review.

Delivered independent localhost console for diagnostics, nine-group calibration, two-port16channel mapping and recipient replay. Source imports HERAMCU45 model/schema/fixtures directly, no45 patches or physical encoding. Palette follows RtR black/white with minor yellow, existing IBM Plex Sans; synthetic controller silhouette is code-native SVG, not device-accurate geometry. Desktop/tablet work areas scroll separately; narrow layout puts workflow first, buttons52px and equal row baselines.

## Requirement coverage

R46-01..08 implemented8/8 and accepted in this scope, not a product readiness percentage.

| ID | Evidence and behavior |
|---|---|
| R46-01 | preservation baseline/final, frozen45+prior namespaces and ENDURE unchanged, floor20GiB, budget16MiB, no owned scratch |
| R46-02 | browser7 screenshots and40 actualChromium checks at1280/1024/360; manually inspected desktop/mapping/mobile layouts |
| R46-03 | direct45imports; explicit INFO/config/source actions, virtualclock, Origin/JSON/token/revision/body/session limits,17 HTTP checks |
| R46-04 | axes/16channel output, separateRFnamespace/ages, stale/jam/USB/reboot/newgeneration guards; max4history refusing rather than dropping |
| R46-05 | nine explicit result groups, ACK100 alone cannot advance or save; cancel/timeout preserve uncertain state |
| R46-06 | draftvalidate/applyACK/saveACK/readback; bounds/invert/axis/MMB metadata, mismatch/lostresponse handling, oldsavedflag clearing |
| R46-07 | actual browser export/sealed45recipient replay, expectedSHA mismatch rejection, read-only import; tabreload newworkspace with no readiness |
| R46-08 | model13/13, HTTP17/17, browser40/38, cold45 corpus76cases/795events and13bytechunk full calibration replay; JS syntax/fingerprints/finalpreservation |

The counts are distinct test suites, not firmware certification. The protected45 supplemental50 and older native regressions are not counted as rerun in46. No APK/native/firmware build or new linter/typechecker/dependency install.

## Failures retained and fixes

Browser1 stopped at reconciliation timing: busy flag changed without rendering disabled controls immediately, causing the test and UI to observe stale state. Busy render now occurs before the fetch. Browser2/3 stopped at second import of the same file: file-reading busy lifecycle and resetting the filepicker value were missing. Both fixed; rejected import also clears previous review success. Slider min/max clamp to calibration ranges after readback, so the synthetic preview never advertises raw4095 when calibration max4000. Current accepted browser7 is after these fixes, the pane layout refinement and RAM/restart scope text. Browser4/5 successful intermediate receipts and all failed artifacts remain intact.

No storage success is inferred from ACK. Peer applied/stored/readback are distinct; page/server memory is not a durable MCU journal. Workspace max2/server, archive4/workspace, bounded45 records. Lost response causes UI uncertainty and disables mutation; explicit state read reconciles local mock only, no retry. Imports cannot replace active session/config. Same-origin tokens and revision prevent accidental cross-workspace/repeated local actions, not a hostile-host security guarantee.

## Preservation, resources and handoff

No source/candidate/canonicalSOT/trust/ENDURE edits, SDK, signed package, APK, SITL or external publication. Cold76-case replay reads45evidence without overwriting prior receipts. Sixteen unknowns including USB dialect/IDs/CRC/firmware compatibility/RF-to-output association remain unresolved and visibly accessible. No physical MCU codec is offered.

QA Chromium contexts and ephemeral servers closed. No scratch, project copies/tmp installs, Docker, AVD, Next output or dependency folders created; nothing to delete. Retained screenshots/export/failure evidence deliberately. Optional review preview on127.0.0.1:8800 is separate and memory-only; its own startup/source identity is recorded if launched. Exact finalfree/allocated/protected counts in verification/preservation receipts.

Next: collect deployed firmware/dialect/USB descriptors/capture and confirm16unknowns, then a transport adapter tested against exact wirevectors. Android/HeraHub bench and Fly integration remain later gates; this UI is not eligible for physical drone operation.

Finaldraft guard refinement: validation of a replacement draft now clears the previous serverdraft first; UI tracks dirty edits across reconcile/tab changes. A rejected new draft cannot re-enable apply on the old validated config. Model2 includes a13th check; browser7 includes2 extra regression checks (40 total). Initial own preview44090 was closed before this refinement; the final preview has a separate receipt. All earlier receipt source/attempt context retained, not relabeled as current.

Final technical verification: 33/33 metadata/preservation checks, JSsyntax7/7,0errors. Preview final: preview2.json. Exact resource readings and fingerprints are scoped to host observation.
