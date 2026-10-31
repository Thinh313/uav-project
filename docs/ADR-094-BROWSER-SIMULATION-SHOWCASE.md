# ADR094 — isolated browser demonstration over retained simulation contracts

16/10/2026. Accepted for engineering presentation only.

Reuse VISUAL56 assets/renderer and the unchanged AERIS57 → SIMTRAIN53 → ArduPilot external-physics control route. A new loopback presentation server serves separate UI/workspace files and a scoped capability catalog. It does not connect to arbitrary MAVLink endpoints or physical radios. Recorded mode never sends a flight command. Live mode requires explicit session, preflight, observed takeoff/LOITER and neutral-first input ownership; page load/restart never launches or arms an aircraft.

Virtual sticks translate pointer position into the existing discrete keyboard axes. A user-initiated12s scripted lesson uses the same key path; no direct pose animation or bypass of server session/boot/lease/challenge/freshness checks. Loss of focus/authority cancels the lesson and clears held keys; return of data does not restart it. This is not analog HID or HeraHub acceptance. Pointer behavior receives a separate no-network DOM fixture; actual SITL qualifies the scripted key path.

New live admission is28GiB plus inherited24GiB/quota checks, preserving the20GiB floor. No dependency download/build/signing, speedup change, cap change, fsync relaxation or raw-frame removal. The actual run retains134632 frames and full oracle/readback. Whole-run RTF0.99732764 and minimum5s0.86314327 do not meet stable1×. Renderer interpolation/selection is presentation only.

Synthetic motor sound is linked to estimated RPM; it is not measured Hera acoustic behavior. Photographic panorama is not surveyed terrain or collision geometry. Weather/load reference profiles are provisional. Internal-quad obstacle results76/77 are separate from this external-physics run; sensor-loss safety remains failed. Do not imply successful avoidance protection in the showcase.

Presentation/catalog/loop changes after live closure receive browser/host regression, not another actual AP run. Preserve this scope distinction in completion evidence. All frozen paths/source/candidate/SOT/trust/ENDURE remain unchanged; newly appended simulator run evidence is retained.
