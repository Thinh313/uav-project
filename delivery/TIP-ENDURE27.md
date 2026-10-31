# ENDURE27 · Diagnose host sleep/fetch failure and fresh24h campaign

Owner13/10/2026 authorizes diagnosis/fix, preservation of all old attempts, then a new24h campaign only after checks pass. NoFly/SDK/HeraHub. Owner confirms intent to connect AC and keep host awake. Current MethodBox sequential specification/build/verify; no independent audit. Scoped architecture authorization already supplied by task.

Observed macOS power log: Clamshell Sleep15:53:20/74s, DarkWake15:54:34, matching failed GET72.618s and supervised shutdown. Forced host suspension is verified as occurring; link-specific Undici error cause was not retained, cannot reconstruct it as certainty. Old90s cadence alone cannot exclude shorter real sleep. Idle-only caffeinate did not stop forced clamshell sleep. Do not disable lid/OS power safety or hide fetch failures by retry.

New pilot/endure27 external controller/soak/power observer imports unchanged app/services/old evidence helpers. Reuse exact signed9/bootstrap, new generation05 and evidence/endure27, never overwrite evidence/endure20 or prior attempts; no new signature. Observe IOKit actual sleep/wake with bounded fsynced native sidecar, AC/lid/runtime guard, structured bounded fetch error/cause and peer diagnostics. Any observed sleep invalidates continuity regardless of<90s; unknown fetch also remains fatal. No automatic campaign restart or request retry. Only intentional local body abort after65536bytes is expected.

|REQ|Acceptance|
|---|---|
|E27-01|Old raw chains and all oldfile/controller/candidate/source hashes preserved; original sleep/wake source capture/timeline and limits documented.|
|E27-02|Native sleep/wake observer ready/live; callback log append+fsync before acknowledgingOS, no sleep prevention; gateAC/lid/observer, bound logs/fail closed.|
|E27-03|Fetch errors retain bounded name/code/cause/abort/source/timing; supervisor/global cancellation not mistaken for intentional abort; no retry.|
|E27-04|Loopback realHTTPreset/header/bodytimeout/intentionalabort and synthetic sleep/power/guard-death tests; prior core regressions. Short tests are not24h evidence.|
|E27-05|Exact packet/bootstrap/signature/140payload/664original+copy verified, fresh VALIDATED generation05, managed short canary+27exports/raw/corpus integrity before new24h; resource/disk/port/currentAC gate.|
|E27-06|Detached24h starts onlyafter gatesPASS; nativeobserver and caffeinate alive/currentpins/manifest/PIDs/progress checked; monitor quiet while healthy. NoFly. Completion only after actual timing/raw/trust/supervision/27/664 checks, no stitched hours.|

If currentAC fails, complete preparation/tests and retain pending start until physical source passes; no speculative start or automatic retry. A new campaign FAILED remains failed, not resumed. Selected7 remains until full protected24h acceptance. Required checks not run are NOT_CHECKED. Capture failure causality conservatively; do not claim a new software application bug fixed when host interruption caused campaign failure.
