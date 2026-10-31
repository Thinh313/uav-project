# ADR: successor integrated cockpit and explicit runtime scope

Use selective successor files from Beta05 rather than edit any prior handoff. Reuse KML/compiler/preflight, wire transport, payload gateway, video encoder/decoder and deterministic receiver. A new MissionLink adds explicit expected Loiter/AUTO/RTL transitions while retaining mode/identity/freshness guards. MIS_RESTART must be observed C_CAST typed zero before resume; no parameter writes.

ArduPilot official AUTO docs state re-entry resumes by default and MIS_RESTART=1 restarts: https://ardupilot.org/copter/docs/auto-mode.html . Documentation is an external claim, actual 4.7.1 runtime observation still required. No assumption about physical flight performance from this test.

Beta05 pins1547 currently have3missing legacy evidence artifacts (two screenshots and one old WAL), no changed present bytes. Preserve those gaps and original pin file. New source-pins is a code/assets/runtime-input closure, not a replacement verification of old artifacts. Legacy historical screenshots/WAL are not eligibility inputs for the new runtime and no code path may consume them. Pin the retained launcher source and all execution dependencies, manifests used for projections and exact ARM artifact/image separately. Never launch old controller pretending its all1547 check passed.

Keep ports8895/8896 and emulator5582 for allowlisted shell origins; reject foreign listeners, exact owned containers/PID identity closure; new evidence and Docker task namespace missionbeta01, speedup1/internalquad,8request maximum including failures.6nominal+2fault budget is distinct from old3request scope; old containers retained and not counted toward a new falsely continuous campaign.

Six30s bounded windows accommodate pauses/corridor while keeping raw-window budgets. New package format and versioned receiver avoid promoting old three-window acceptance to new data. Archive receiver-verified package before publication; current authority never imported from metadata. SHA proves internal consistency, not camera/source authentication.
