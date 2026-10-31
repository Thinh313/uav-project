# SHOWCASE78 — Flight Studio

From project root, `node pilot/showcase78/server.mjs`, then http://127.0.0.1:8828/. No build/install/download. Preview admission20.25GiB, live admission28GiB plus inherited backend quota. Existing visual assets are read-only, no project copy.

Default: recorded reference SITL, zero flight commands. Click **Bắt đầu trình diễn** to unlock procedural RPM-dependent engine sound and playback. Three recorded flights, including the newly verified E2E flight with recorded-controller HUD, camera presets/orbit, seek, pause and fullscreen. Sound is synthesized, not calibrated Hera acoustics. Panorama is photographic projection, not measured collision terrain. Tab hidden, long animation suspension, resource failure or pause silences playback. Returning does not resume automatically.

**Điều khiển trực tiếp** opens the same-origin AERIS57 workspace. It needs the existing owned SIMTRAIN53 backend8807, its quota/firmware/pin/resource gates, explicit start/preflight/takeoff/keyboard/land/end actions. No startup or arm from page load. Do not start that backend/runtime below admission or automatically retry unknown writes. Physical HeraHub/HID, all-payload integration and full AUTO remain unaccepted. Read the SIMTRAIN53/AERIS57 runbooks before live operation. Stable external-physics1× remains unaccepted.

QA: `node pilot/showcase78/qa.mjs` (port8838 free, preview admission required). All new workspace records use evidence/showcase78/workspace. No cleanup/signing/SOT/ENDURE edits. This presentation is not product acceptance. Required live/projector/acoustic listening tests not performed must remain NOT_CHECKED.

Visibility test limit: Codex IAB hide/show kept document.visibilityState visible in this host test. The document-hidden guard is implemented, but actual OS/tab-hidden automatic pause is NOT_CHECKED. Explicit pause/seek/end audio silence and fullscreen were browser-checked.

Recorded input is local TX aligned approximately by logged Node/backend clock brackets (midpoint). It is not AP RC echo, proof of per-command execution, or a measured latency. Original134632-frame WAL is untouched; display selects every40th model frame. Old replays without input logs do not invent stick motion.
