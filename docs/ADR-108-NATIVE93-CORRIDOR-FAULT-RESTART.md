# ADR-108 — Corridor qualification and no-resume recovery

18/10/2026 · accepted for isolated engineering93 only.

Problem:92 exercised polygon AUTO; corridor had protocol-mock coverage only. Some retained oracle scripts assumed16items/6camera and cannot qualify corridor or partial recovery honestly.

Decision: use unchanged mission92 model+compiler and explicit corridor fixture selected in Android. Derive independent MAVLink expected counts/commands from immutable compiled plan; verify actual readback2cycles, camera exact values/frames and takeoff/NAV/terminal witnesses. Keep simulation source identity/session/boot/Home/HEAD protections.

One nominal run plus duplex-loss and Android app-restart while airborne. Passive observer remains independent of selected control transport. No auto reconnect/regrant/resume. Fault completion requires actual failsafe/RTL/ground/disarm observations and explicit ground recovery acknowledgement; saved review stays accepted=false. Closed-session Android reboot/cold-host restart verifies data preservation, never restores authority. Schema92 is retained; history of multiple runs under the same compiled model is append-only.

All work namespace93; preserve older source/candidate/ENDURE and private apps90/91/92. Development APK permitted by continuing Android test scope, no production signing or selection. Unknowns: physical HeraHub/HID/video/PhaseOne, actual Hera performance/corridor field acquisition and offline native parser remain unqualified.
