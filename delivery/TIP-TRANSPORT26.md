# TRANSPORT26 · Loopback SITL and payload transport fault verification

Owner authorization13/10/2026: test multi-payload transport/routing with SITL, connection loss and wrong-target responses; isolate from frozen source/candidate/ENDURE20. Sequential single-agent specification/build/verify using current MethodBox. Authorization supplies scoped architecture approval; no release approval/signing/Fly/hardware integration.

ENDURE20 was already FAILED at08:54:34Z before this implementation: fetch failure, no controller/canary listener, no24h acceptance. Preserve failed evidence/trust exactly, no recovery/restart/retry/lock deletion. Separate task remains authorized.

Architecture: new pilot/transport26 harness → unchanged TRANSPORT25 broker/MockTransport → explicit loopback bridge. Receive actual disarmed ArduCopter heartbeat from a dedicated container TCP5772; all payload commands go ONLY to a separate synthetic payload responder TCP5773. Camera/gimbal responses are synthetic network fixtures, not ArduPilot payload execution. Broker's existing mock provenance remains intact; an outer evidence envelope distinguishes SITL heartbeat, network fixture, admission and feedback. No new network authority in frozen code. No commands written to ArduCopter, no ARM/mode/mission/parameter command, no automatic reconnect/resend/failover. These are protocol/transport tests, not flight tests.

|REQ|Acceptance|
|---|---|
|T26-01|Fixed127.0.0.1 endpoints, separate disarmed SITL container/state, existing binary/image read-only; resource/disk/collision bounds; actual heartbeat observed, zero AP writes.|
|T26-02|Explicit reviewed immutable target+generation, one exact command dispatched to synthetic TCP responder, three direct camera components/shared-manager gimbal device routing and concurrent distinct camera commands; no queue/retry.|
|T26-03|Wrong responder/system/recipient/command, forbidden proxy-source impersonation and wrong gimbal feedback cannot complete target transaction; exact valid ACK remains accepted≠execution, consistent observation remains unattributed/no real image.|
|T26-04|Real socket close, half-open/heartbeat silence, explicit reconnect/fresh discovery, old local generation and uncertain admission refuse/retain ambiguity; no automatic resend/failover.|
|T26-05|Bounded framing/journal/bytes/write buffer/connection timeout; split/corrupt/duplicate inputs, configuration/allowlist/outbound rejection tests; raw network receipts and replayable scenario reviews retained.|
|T26-06|Core tests and unchanged T25/P22 regressions, before/after frozen2009/controller/candidate140/pilot/native/SOT/trust/failure evidence hashes; stop only owned simulator/responder, prune dangling images only; no source edit/new signer.|

Conservative T25 ACK-key tombstones remain; new generation requires manual reconnect. Remote unsigned wire freshness/authentication is NOT_CHECKED: local socket epoch prevents old callback attribution but cannot prove a remote frame is fresh. Claims do not exceed observed host transport/network synthetic scope. No browser/product changes required for this test task. Required tests not run are NOT_CHECKED; failure receipts retained.

Refinement decision: initialSYSID_THISMAV was not effective on existingbinary; observedheartbeat1 caused failure before commands, receipt preserved. Use MAV_SYSID42 verified from observed heartbeat. Network center camera102 replaces synthetic T25proxy1/device2: independent fixture must not impersonate actual autopilot component1 or mix sequence streams. Same-component AP proxy network integration NOT_CHECKED; unchanged42scenario T25proxy corpus remains regression evidence only.
