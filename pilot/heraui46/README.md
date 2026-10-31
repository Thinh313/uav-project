# HERAUI46 · HeraHub MCU engineering console

Isolated diagnostics/calibration/mapping/replay UI, using frozen HERAMCU45 directly. **Mock only. No USB/MAVLink codec, SDK, Android build, signing, real input ownership or flight control.** The original16 unknown protocol items remain visible. Existing app/native44/candidate/SOT/ENDURE are unchanged.

Run from project root with free space≥20GiB: `node pilot/heraui46/server.mjs`; open `http://127.0.0.1:8800/`. Existing Node only; font served read-only from native44. Exact allowlisted assets and JSON mock endpoints; no external assets or device transport.

Connect mock → INFO → read configuration → request source samples → input preview. No background telemetry; virtual clock advances100ms per internal action or explicit timeout/fault step. A live-looking value is still synthetic. Chosen RF-to-output topology is a proposed mock association, not firmware truth.

Calibration has nine groups. ACK100% and group result are separate; min/trim/max or buttonmask are explicit synthetic fixtures. After nine groups, request SAVE, receive ACK then exact readback. Mapping edits a staged draft for two ports/16channels, per-channel bounds/invert, axis deadzone/invert and MMB metadata. Opaque MCU coefficients are never interpreted. Save/readback and old flag invalidation use45 model guards unchanged.

Controls are52px; desktop uses two separately scrollable work areas, tablet retains alignment, narrow screens place workflow before instrument. Header/current state and fixed critical actions remain visible. The three early browser failures and later accepted layouts are retained; final screenshots/current actualbrowser checks are in browser7.

Host sessions are memory-only, maximum2/workspace server and4 archived records/workspace; a full archive refuses new session rather than dropping evidence. Export before restarting preview. Reloading a tab creates a new workspace with no restored readiness; serverrestart discards RAM. This UI makes **no local journal durability claim**. Import replays evidence read-only, never hydrates active configuration/session/authority. Optional expected bodySHA helps identify original history but is not a signature/authentication guarantee.

Lost response blocks further mutations; explicit state read may reconcile the host mock, never auto-resends the prior action. Revision/Origin/token guard only local UI requests, not authentication of a real controller. Need actual dialect/firmware/USB capture before building a physical adapter.

QA scripts use exclusive numbered outputs. Do not blindly rerun a script naming an existing receipt directory. Model12, HTTP17 and browser40 checks plus protected45 cold76-case replay are scoped host evidence. Android/emulator/HeraHub execution NOT_CHECKED. Floor20GiB and newnamespace16MiB tracked separately from full project capacity; no dependencies or scratch builds needed.
