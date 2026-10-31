# RESOURCE18 · Host resources and service isolation

Owner authorization: current roadmap continuation; no SDK/device required. Contractor/Builder/Verify are separate phases performed by one agent, not independent review. Final1.13.1 / sequence6 (initial1.13.0 / sequence5 retained); no external publication.

| REQ | Acceptance |
|---|---|
|R18-01|Fixed engineering budgets:256MiB V8 old space,512MiB parent-sampled RSS,256MiB available RAM admission,20GiB free-disk floor plus64MiB reserve. Unknown observation blocks, no bypass environment/automatic deletion.|
|R18-02|Managed macOS launcher applies Seatbelt before Node; candidate/data separation, code/trust read-only, common user/temp/volume data denied except explicit read roots. Keys and original corpus inaccessible; socket ports restricted. Unsupported host fails without fallback.|
|R18-03|Read-only fresh resource API/UI; development preview never claims managed isolation. Mutations blocked on low resources. No stale success after malformed/offline responses.|
|R18-04|Parent watchdog bounds startup, heartbeat stall and shutdown; handles crash/OOM/SIGKILL, no automatic restart. Incomplete supervision never claims success. Parent killed => existing IPC loss termination.|
|R18-05|Actual bounded V8 OOM; actual Docker memory-cgroup OOM and tmpfs ENOSPC on reused image with no true evidence writable mount. OS denial of forbidden read/write/socket observed.|
|R18-06|Store ENOSPC/EDQUOT/EIO injection retains raw partial, no commit/receipt promotion, marks unhealthy; quota/reserve denial before write and restart revalidation. Corrupt original is never repaired silently.|
|R18-07|Original664-file corpus checked before/after and copied generation verified; managed candidate starts/restarts, read-only canary replays156 records before increasing selection (initial5, repaired6); no MAVLink writes/SDK.|
|R18-08|Immutable begin/end supervision receipts bind policy/isolation/manifest/layout and begin digest; interrupted journal remains raw. Sources and receipts fingerprinted, coverage reports exact scope.|

Limits: macOS sandbox-exec is a host engineering facility, not Android support or certification. System reads/metadata and mach lookup allowed; no host-admin containment, CPU cgroup/pid namespace or sealed OS/runtime custody claimed. RSS sampling may overshoot and V8 heap excludes external Buffer memory. Docker probes use sh/dd only, not AERIS or native runtime, and do not establish AERIS Linux isolation. No physical power-loss, full host disk fill, independent security review, HeraHub/SDK/native/HIL/field acceptance. Existing sealed/checksummed records retain their bytes; software Ed25519 signatures do not sign flight records.

macOS RAM admission uses vm_stat free+inactive+speculative pages (explicit reclaimability estimate, not guaranteed allocation). Native OS free bytes alone incorrectly rejects idle cached hosts. RSS watchdog measures the registered Node PID, not a cgroup/process-tree ceiling; fixed vm_stat subprocess is allowed for measurement. Other platforms remain unsupported for managed RESOURCE18 isolation.
