# Survey & Inspection Workbench 01

Host/mock-only application. No aircraft transport, SDK, SITL or operational authority. Node built-ins + Python standard library; no install/build required. Frozen modules are imported read-only.

Run from the AERIS repository, after checking `df -h /` (minimum 20 GiB free):

```
node pilot/workbench01/server.mjs
```

Open http://127.0.0.1:8890/ (loopback only; not a HeraHub or phone deployment). The current task leaves this preview running for review. Change only WORKBENCH_PORT if an explicit alternate local port is needed; no listener takeover or automatic retry.

Choose polygon/corridor or paste/upload KML → explicitly select a feature → set optics/AGL/overlap/speed/heading → set Home, power/payload/wind/reserve → acknowledge synthetic flat datum → compile → review mock preflight → explicit consent → Fly replay scenario → coverage and per-photo diagnostics → proposal/export. Changes revoke approval. Workspace reload/import never restores authority.

For KML outside the sample location, open Pin, tải & gió and explicitly set Home coordinates, or choose Home từ đầu vùng (mock), then apply/recompile. Absolute heights/holes/unsupported KML are refused, not silently flattened. Camera/power values are synthetic assumptions, not installed Hera truth.

Quality is computed from synthetic 16×16 pixel arrays, with hashes/exposure/navigation clock/pose binding. Real files are always zero. Grid coverage is footprint-center sampling, not photogrammetric accuracy, multi-view reconstruction, terrain clearance, airspace legality or field acceptance. Refly is a proposal requiring new safe mission planning; it sends no commands.

Save/export workspace ≤2 MiB. Local browser storage retains the explicitly saved/last completed workspace; this slice is not a crash-durable flight journal or full review-history catalog. Storage failure is visible and existing in-memory data remain available. Keep exported files for archival use; no automatic deletion. SHA checks consistency/integrity, not sender identity/authenticity.

Independent receiving process:

```
node pilot/workbench01/receiver.mjs /absolute/path/to/aeris-survey-workbench.json
```

It reparses KML, regenerates the plan/coverage/proposal and validates synthetic pixel hashes. Same semantic module, separate process; not an independent algorithm or external certification.

Verification scripts are in planning/workbench01. Historical receipts are retained; never reuse output names to overwrite earlier evidence. Mock tests currently take an optional output file, HTTP tests require running preview and loopback access. Protection checks are read-only against G17 references and write only a new receipt in evidence/workbench01.
