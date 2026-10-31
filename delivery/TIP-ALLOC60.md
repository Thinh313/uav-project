# ALLOC60 — extent allocation A/B

User authorized15/10. Single agent specification/build/verification with retained TIP/ADR/report (Vibecode transfer); no independent reviewer claim. Only new pilot/alloc60,evidence/alloc60,delivery/ADR files. Freeze prior source/candidate/ENDURE/SOT.

REQ1: Darwin F_PREALLOCATE/F_ALLOCATEALL, F_PEOFPOSMODE at empty WAL fd; reserve WAL quota384MiB once before MAGIC/header. No ftruncate/zero padding/PERSIST flag/contiguous fallback. Logical EOF, offset, WAL format, CRC/SHA, per-frame fsync barrier unchanged. Verify returned allocation>=requested and EOF/offset unchanged. Unsupported/partial/ENOSPC => fail closed with receipt/descriptor close, no silent fallback.
REQ2: mock exact deterministic WAL bytes versus none, short/error/flush/overflow/snapshot fault cases, crash before first sensor, process reopen/every-byte parser and original model oracle. No host power-loss claim.
REQ3: maximum4 starts predefined ABBA none/preallocate/preallocate/none, same optimized mode, UI1920x1080 and AP/rate1200/speedup1/cap500ms, neutral hold20sec then observed LAND/disarm/end. Fresh24GiB admission, stop20GiB+768MiB;2.5GiB new cumulative budget including all failures. No heavy analysis during active runs, no external host intervention. Preserve aborts/no mutation retry.
REQ4: compare per-syscall p50/p95/p99/max, full5s/whole RTF/cap clipping, host wake and actual UI timing; all admitted frames exact original oracle+AP correlation and fsync before send. Scoped benchmark cannot prove stable1× under all loads; no threshold invented or speedup changed.
REQ5: hash all prior protected files before/after including sealed IO59, pin current source before runs, retain receipts/report/fingerprints; no signatures/build/SDK/device/soak.
