# RECOVERY07 · BENCH06 connection / restart matrix

Authorized: user requests loss, reboot and mission recovery on BENCH06 without HeraHub/SDK. Single agent separates Contractor, Builder and Verify; no independent audit claim.

REQ-R07-1 / AC1: exact sealed BENCH06 corpus, source/runtime frozen before actual loopback tests. Three accepted patterns × inbound telemetry blackout, TCP close and duplex blackout; four rejected patterns remain non-executable.
REQ-R07-2 / AC2: inbound/TCP loss after observed AUTO→HOLD; unknown live fields and invalid profile/readback during loss. Fresh heartbeat alone restores no mission verification. Read-only download verifies exact mission. Wrong source and wrong resume review rejected. Explicit source review emits no command; pilot explicitly RTLs, observes ground/disarmed. No automatic AUTO/reupload.
REQ-R07-3 / AC3: duplex loss during AUTO; passive upstream observer proves GCS failsafe text and RTL. Restore/download cannot imply complete execution. FS_OPTIONS16 continues pilot-controlled modes on GCS loss, hence HOLD tests do not promise autonomous RTL. Never alter parameters to obtain a preferred result.
REQ-R07-4 / AC4: three observed-disarmed Docker restarts, exact pinned argv includes -w. Reset destroys stored mission; fresh session and profile, read-only download fails, AUTO blocked without writes, deliberate reupload/readback works, remains disarmed. This is reset/reload evidence, not retained-storage reboot or in-air power cycling.
REQ-R07-5 / AC5: durable hash-chained execution records, separate upload/recovery attempts and QGC derivation, no COMPLETED promotion across gaps. Receipt includes passive raw packets, outbound write capture, stage snapshots, independent reset/session identities and conservative summaries. Import validation derives protocol acceptance beyond PASS flags. Local historical viewer and validated import/export; zero flight-authority writes.
REQ-R07-6 / AC6: boot-time regression invalidates execution/profile, blocks authority until explicit reconnect; tests include reordered telemetry, pending transfer and fresh heartbeat.

Baseline: ArduCopter4.7.1 / quad / world Home10.854,106.807 AMSL10 / speedup5, profile1.0.0 four read-only names. Blackouts are packet transport faults, not physical RF measurements. Container, host, browser, binary/hash and probe logs retained. Hash integrity is not signed authentication. Device/HIL, reboot retaining flash, Android process death, long-duration/power-loss durability and human/RAGAS comparison remain NOT_CHECKED.

Primary reference consulted 2026-10-12: https://ardupilot.org/copter/docs/gcs-failsafe.html and https://ardupilot.org/copter/docs/radio-failsafe.html (FS_OPTIONS bit4 / +16 pilot control). Actual runtime observations are the acceptance evidence.
