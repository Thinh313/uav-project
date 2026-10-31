# FIELD01 — host mission, payload media and verified handoff

This is an isolated engineering integration for the parts that do not require a Xiaomi phone. It is not an Android build, a Hera driver, a physical camera integration, or operational flight clearance. Existing PHONE07, candidate and ENDURE sources stay unchanged.

Use the current checkout with cached dependencies. No dependency download or project copy is needed:

```sh
python3 -B pilot/field01/stage.py
node pilot/field01/app.mjs evidence/field01/NEW_APP_RUN --workspace=evidence/field01/app01/workspace
```

Open `http://127.0.0.1:8870/`. Omit `--workspace` to create a new workspace. Every app launch needs a new evidence directory. Reusing a workspace restores the verified semantic document, exact model/plan hashes, original KML text, image bytes/references and review history; JSON object key order follows canonical WAL serialization, so the whole JSON text is not promised byte-identical; flight and payload authority are never restored. A stale crashed writer lock opens read-only and requires investigation; do not delete it automatically.

The same cockpit provides KML polygon/corridor and scoped QGC SimpleItem planning, preflight, upload/readback, post-arm Home approval, AUTO simulator flight, payload discovery/selection/explicit lease, mock gimbal/camera control, decoded RGB/thermal-look capture, review and export. Browser file import is local; it does not use Android SAF. Unsupported QGC ComplexItems/frames/datum remain review-only. Simulation coordinates and compiler limits are deliberately restricted to the pinned synthetic flat world, height10–30m, speed0.5–2m/s and100m radius.

The compiler runs canonically on Node. WebKit and Node differed in non-wire geodesy float least-significant bits. The server verifies the exact saved model/CAS and replays every committed/restored compiled document. Browser load still verifies schema and hashes. Flight02 independently replays the same canonical document, without a numeric tolerance or a hidden waypoint change. Original rejected browser output and the comparison are retained in evidence.

`--allow-sitl` is explicit and starts no simulator until the user selects SITL and presses Connect. It uses only the pinned cached ArduPilot internal quad, the fixed owned `aeris-field01` container and loopback5970. Admission requires31 samples≥29GiB; runtime stops at21GiB to protect the20GiB floor. This task has already used its three-attempt budget; do not launch another attempt without a new, bounded task plan. No real vehicle endpoint is supported.

Read preflight before granting authority. Review the exact Home after arm and explicitly approve within10seconds before AUTO. A command ACK never proves mission completion. Flight02 additionally supports a narrowly defined raw-evidenced takeoff climb/current transition when ArduPilot reports REACHED for the following speed item; it never fabricates a REACHED event. All other navigation, RTL, near-Home, ground and disarm evidence remain required. See `flight/flight02-README.md`.

Video uses an independent visible publisher iframe, WebCodecs, real localhost HTTP/TCP relay and viewer. Start the source and viewer explicitly. H264720p30 is preferred; VP8 is an explicitly selected fallback. Both actual canvases must remain visible for a valid foreground measurement. Buffers are bounded and discarded media frames are counted. This policy does not discard physics/journal frames or change simulator speedup. A500ms pause is measured from its requested start, armed after the response, and needs a new source frame after the server resume bound. Fresh-source replacement after reload is explicit, fenced, bounded and invalidates old frame references.

Payloads are synthetic mock adapters. A capture stores a JPEG encoded from the latest decoded1280×720 synthetic video frame, not an original camera sensor image. Original JPEG bytes received by the capture store are immutable. Coordinates are nearest SITL telemetry host-receipt references in MSL and relative Home; physical exposure timing and sensor-clock uncertainty remain UNKNOWN. No ellipsoid altitude, radiometric temperature, survey accuracy or actual images are invented.

Raw mission and media TAR exports require a closed flight and are independently receiver-checked. SHA integrity does not establish sender authenticity. No receiver restores command authority. See `evidence/README.md`, `flight/handoff-README.md` and the completion report for retained evidence, failures and current scope.

Send SIGTERM to the exact app PID recorded in its app-launch.json to close cleanly. Closure invalidates authority, waits for an in-flight simulator action, closes the owned simulator/writers/listeners, then writes an app-closure.json. A pending closure must not be reported as complete. Do not delete campaign locks or old evidence.

The review action “Tạo bộ bàn giao” collects an accepted SITL raw archive and captures from that exact flight. Download index.json, flight.tar and the capture TARs into one folder. Keep the index SHA shown by the cockpit outside that folder. The standalone receiver cross-checks run/boot/model/plan and each reference coordinate against the exact raw position row before issuing a durable receipt. See evidence/delivery-set-README.md. Mock-only or image-free flights expose raw export without offering this SITL delivery action.

Browser QA covers 1280×720 and an actual900×500 nested viewport. On the smaller viewport, opening the control console hides the video panel; closing it restores the full video area. A valid video measurement requires the video and publisher to remain visible, so opening the console during a small-screen measurement invalidates visual coverage. This is deliberate layout behavior, not proof of Android/Hera performance.
