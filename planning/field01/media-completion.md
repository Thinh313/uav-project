# FIELD01 media Builder completion

Implemented independent publisher, relay HTTP server and embeddable WebCodecs viewer in `pilot/field01/media/`, plus Node actual HTTP/TCP fault tests in `planning/field01/media-http-test.mjs`. Reused the BIG02 Relay01 and packet codec unchanged. No existing PHONE07, ENDURE, frozen source, APK, container, SITL or dependency installation was touched by this work package.

The browser API, cross-origin compact publisher iframe, explicit origin-checked parent messages, clock domains, freshness requirements, bounded queues, persistence, limits and integration examples are in `pilot/field01/media/README.md`.

Verification: all module syntax checks passed. 17 actual Node HTTP/TCP fault groups passed in `evidence/field01/media-http-test-result.json`. This covers role/token/nonce/origin, source/target/config/boot/feed, frame identity/order/replay, source clock rejection, transactional failed configuration, queue overflow/keyframe recovery after controlled 500ms pause, size/header limits, actual incomplete-body TCP deadline, fresh immutable host capture binding, stale frame refusal, async report identity/quota persistence and restart invalidation. Test-only synthetic payloads/reports are explicitly labelled and do not represent decoded video performance. Test servers are closed by finally blocks; no persistent service was left by this work package. Initial sandbox binding denial produced a retained launch-only test directory; the authorized network test runs use owned ephemeral loopback ports.

Root browser integration owns foreground ≥30s codec/fps/calibrated latency evidence, decoded JPEG capture, screenshot geometry and UX verification. Those browser and physical-device gates remain NOT_CHECKED by this Builder. No physical latency, physical camera/radiometry, GNSS, Android or commercial readiness claim is made.

No scratch project copy, install, venv, build output or Docker image was created; nothing required removal. Evidence is retained under `evidence/field01/media-*` within the declared budget.

## Host panel extension

Added `pilot/field01/media-panel.mjs` and `media-panel.css` only for the follow-up UI integration package. `await mountMediaPanel({container,mediaOrigin,onCapture,onState})` yields `{element,viewer,snapshot,state,close}`. Explicit source and viewer actions, source/profile selection, visible independent publisher PiP, 30s measurement, 500ms pause, report save, capture callback and diagnostics are scoped to the passed container. Source commands require acknowledgement before repeated use. Source/decoded state, stale age and honest synthetic/clock/physical-latency scope remain visible. CSS uses existing cockpit glass variables with 48px minimum controls, small-height adjustments, and container-responsive rows. Module syntax passed; root owns screenshot and live browser verification. The host must serve the two new files and include CSS; no root app/ui file was edited by this package.

## App04 stale-source repair

Read-only live app04 bootstrap showed one source rejection with last accepted source timestamp39637.9ms, calibration sampled25118.6ms valid until85118.6ms. The calibration had not expired at the last accepted frame; the old generic error did not expose whether the rejected item was too old, too far future, or outside calibration bounds. A renderer/encoder/network stall remains an inference, not a proven diagnosis. The old publisher stopped on every rejected chunk and allocated the sequence before acceptance, making one transient stale item fatal.

Repaired browser-only publisher transport in `media/client.mjs` and `publisher.mjs`: discard encoded items older than750ms; suppress dependent deltas until a fresh keyframe; advance sequence only after a relay acknowledgement; on explicit source-clock rejection, discard the rejected item and refresh clock with at most2 repairs per source start. Uncertain HTTP errors still stop without retry. The root Node service need not restart; a browser reload loads the updated modules. The root service and ports8870/8871 were not stopped or modified.

## Renewed clock and visual coverage gate

The first 95s transport run reproduced `CLOCK_BOUND` at the second (≈60s) renewal, after581 accepted test chunks. The strict server lifetime equality is sensitive to floating-point addition/subtraction of fractional sampled time. The browser calibration now quantizes only its sample-validity marker to an exact1/1024ms binary grid, preserving full precision for offset lower/upper bounds.100,000 sample markers across the60s boundary pass the strict60000ms lifetime check. The failed transport result is retained in its unique media-clock-test directory; it is not a valid95s pass.

Panel layout now groups source setup/start controls/results inside one collapsed section. The decoded viewport and visible publisher PiP share a bounded grid with a four-button48px measurement bar. Starting a measurement closes setup, resets panel scroll and uses focus without scroll. Viewer measurement requires both canvas and publisher iframe to be within the actual browser viewport and all clipping ancestors. Computed checks run every200ms; IntersectionObserver additionally retains visual coverage loss. Reports include visualForeground, check count and failures; engineering coverage requires visual foreground. Earlier reports that only checked document.visibility do not prove both source/viewer were visually present.

Only browser modules/CSS changed for these repairs. Root process, media service and SITL remained running.

The repaired95s actual HTTP transport run passed with3renewals and≥900 accepted packets; all5 clock/recovery checks passed. Evidence: `evidence/field01/media-clock-recovery-test-result.json`. This remains non-codec transport evidence, not720p browser performance.

## Explicit fresh-source admission after reload

A root-observed reload then exposed Relay01's intentional run/boot fence: a new publisher document cannot configure a fresh boot in the existing relay. Reusing the previous boot would disguise the reboot. Added an explicit publisher-only compare-and-swap `/api/new-source` route for the next service launch: previous config must match, new run/boot/config must be unseen, target viewer and clock must validate. It closes the old relay, clears all source/decoded frame references, creates a fresh unchanged Relay01 and persists the retired/admitted identities with authorityRestored:false. Replacement budget8, total config budget32. Browser Start makes this explicit request only after the operator action. No flight/payload authority is restored.

18 actual HTTP/TCP groups pass, including fresh source admission, wrong-role/CAS refusal, immediate fresh-capture invalidation, oldboot packet rejection and identity replay refusal. The existing running root service was not stopped; its old request-handler closure cannot acquire the new route without a restart. Root must finish/close the active simulation before restarting the service. No claim was made that the current old closure could recover honestly after reload.

## App06 pause recovery race repair

Root observed app06 report03 containing an impossible110.6ms recovery for a500ms pause. The bug is confirmed in code: pause() published lastFault before awaiting HTTP while expected recovery ID was null; an already decoded in-flight frame satisfied recoveryId>=null. That report's recovery result is invalid and retained as failure evidence.

The targeted repair arms recovery only after a valid pause response. Server pause is now viewer/config fenced and returns the host start and conservative start+500ms resume bound. Recovery needs all of: response received; matching config; response recovery ID reached; client request-to-canvas elapsed≥500ms; recovered source-host lower bound at/after the server resume bound. API roundtrip is separately recorded, and recovered frame/recovery/source-bound evidence is retained. Unrecovered faults are preserved; config changes/stops cannot silently turn them into success.

Reports now retain measurement browser-clock start/end. faultWindows includes only windows overlapping that measurement; priorFaultWindows is separate. The recovery gate only evaluates current-window recoveries and requires500–2000ms.19 protocol test groups passed (actual localhost HTTP/TCP checks plus deterministic recovery-eligibility rejection cases for response race, early display, pre-resume source, wrong config and wrong recovery ID). No real-browser recovery result for this new version is claimed by Builder; root must run app07. Running services were not changed; server pause schema requires the next orderly launch.
