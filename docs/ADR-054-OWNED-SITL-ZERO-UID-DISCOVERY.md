# ADR-054 — real full-stream inspection with simulator-scoped zero UID

Accepted within user-authorized isolated disarmed SITL scope,2026-10-14.

AP40's mock contract rejects UID0, but pinned GCS_Common::send_autopilot_version sets uid=0 and sends UID2. Do not modify that historical guard or label a real frame synthetic without an outer actual-evidence wrapper. New SITLDISCOVERY41 observer uses the unchanged full framer and codec with actual loopback TCP provenance; a strict locally owned simulator manifest binds binary SHA, image/CID/PID/boot and observed version/custom commit. UID0 is allowed only in that simulator scope; no radio authentication, hardware identity or source-build reproducibility is inferred.

Discovery/read-only parameters are actual network operations; no flight control output is provided. Connection loss/process reboot revokes process-local inspection witness; reconnection creates a new session and rereads configuration. Wrongtarget injections at the parser seam are fault evidence, not a real second aircraft. Journal/raw capture and cold replay remain separate from control or execution acceptance. Physical Hera/native/full preflight and ENDURE remain open.
