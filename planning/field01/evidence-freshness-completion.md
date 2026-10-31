# FIELD01 delegated freshness repair and final checks

The root Contractor identified a gap in Payload01: failure/error flags alone did
not independently establish current heartbeat, transport and position freshness.
The explicitly authorized delegated repair is complete in the isolated gateway.
No frozen source or flight module was edited by this agent.

Payload operations now require an active run/boot, connected live transport,
finite heartbeat age from zero through 1500 ms, and a finite latest-position host
monotonic age from zero through 1500 ms. Missing/null/nonfinite/future timestamps
fail closed. Stale or failed flight state invalidates payload leases and discovery;
fresh telemetry returning later does not restore either. Status independently
rechecks freshness before reporting lease ownership.

Existing checks after command intent, adapter response and capture file sync now
use this gate. Noncapture commands also recheck after readback fsync. A stale
transition returns UNKNOWN with any earlier readback labeled as prior observation,
without claiming current authority. Timeout/unknown return paths sample freshness
so a timeout cannot leave a stale lease displayed until a later status request.
Capture guard failure retains pending evidence; final-result revocation retains
durable bytes while reporting ended authority.

Final targeted gateway checks: **15 pass, 0 fail**, retained at
`evidence/field01/evidence-gateway-tests-2026-10-21T12-35-21-202Z/results.json`.
The earlier 15-pass run at `12-34-22-091Z` remains retained. Checks cover stale
heartbeat, transport and latest position independently of error flags; missing,
null, nonfinite and future values; the inclusive 1500 ms boundary; no restoration;
and stale transitions during command intent fsync, adapter await, readback fsync,
capture file sync, and timeout. Other existing authority/context/capture tests
continue to pass. Flight/media/clock are fakes, Store01 is the actual async store.

Final app nonflight HTTP rerun after the Flight02 import: **11 pass, 0 fail** at
`evidence/field01/evidence-app-http-tests-2026-10-21T12-34-37-513Z/results.json`.
It used only owned ports 8890/8891 and a new owned workspace, with no flight
commands or SITL. Startup collision rollback, normal closure, Origin/Host/CSRF,
JSON object/body limits, compiler replay/CAS, rejection quotas and seeded storage
review/download/quarantine remained checked. Both owned listeners and writer
locks were released. Earlier failed attempts remain documented in
`planning/field01/evidence-app-http-qa.md`.

The repair and its new tests have the same delegated author. They are Builder
self-checks, not independent review of this repair. Existing root-authored app
HTTP behavior was checked by this delegated author, who also authored storage.
No independent human QA, physical camera/GNSS, Android or operational acceptance
claim follows. All image counts remain zero and no authority is restored.
