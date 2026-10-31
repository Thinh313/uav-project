# PACK15 · local deployment runbook

This is an internal engineering software package. Node >=22 must be supplied separately; measured host runtime is recorded in evidence. No OS/runtime/Docker/SDK/APK is shipped. Linux and HeraHub runtime/storage/input are not claimed tested by a macOS run. Only host-preview/host-sitl may start; herahub-proposal remains NOT_CHECKED.

Use reviewed tools/release.mjs from a trusted checkout as the bootstrap verifier. Do not bootstrap trust by running an unknown package's verifier. Obtain public policy and expected manifest digest independently of the received package. The included development public policy is an example trust anchor generated on this host, not a RtR production identity. Never transfer .local private signing keys with a package. Verify policy/key fingerprint/revocation/minSequence with the owner; choose a reliable clock. PACK15 is not TUF or a remote updater.

Commands (replace placeholders with explicit paths/digests; no implicit latest):

```
node tools/release.mjs verify --package PACKAGE --trust PUBLIC_POLICY --expect MANIFEST_SHA
node tools/release.mjs install --package PACKAGE --trust PUBLIC_POLICY --expect MANIFEST_SHA --slots SOFTWARE_SLOTS
node tools/release.mjs verify-installed --slot SOFTWARE_SLOT --trust PUBLIC_POLICY --expect MANIFEST_SHA
node tools/release.mjs budget --profile host-sitl --workload WORKLOAD_JSON
node tools/release.mjs start --slot SOFTWARE_SLOT --trust PUBLIC_POLICY --expect MANIFEST_SHA --profile host-preview --data PERSISTENT_DATA_ROOT --workload WORKLOAD_JSON --port 8789
```

`start` verifies the entire installed inventory/signature/time/sequence again, checks target/runtime and observed free space for the declared scenario, then starts loopback server. Data root must be separate from software slots; software updates never overwrite it. Host-preview has no flight adapter. Host-sitl permits dedicated simulation only and never auto-connects or ARM/AUTO. New profiles initialize declared quota/floor; a pre-existing mismatching lifecycle policy fails startup rather than being silently rewritten. Default checkout start still uses existing runtime roots.

Sizing input fields are integer bytes/counts: missions, filesPerMission, maxFileBytes (assumed per-file upper bound), journalBytesPerMission (declared retained journal estimate, not measured rate), partialCheckpoints, concurrentExports, softwareBytes, freeBytes (null means unobserved). Archive estimate includes 32 MiB possible legacy results per mission. Source and receiver copies are separate; recipient totals include full partial checkpoint copies, export uses a separate workspace bound, software counts two slots plus one staging copy. Metadata reserve and 20 GiB host floor are retained. Device usable space, real capture rates, journal expansion, other processes and physical allocation remain unknown. File/count/mission/store limits can make a plan unfit despite enough disk. No automatic deletion/retention weakening. Startup budgets are forecasts, not reservations; runtime intake/export guards still apply.

Failed software stages never become published slots; publication is a directory rename under exclusive install lock. Existing slots are never overwritten. An interrupted install lock/stage must be inspected manually; no automatic ambiguous-state recovery. Software stores are separate from evidence. Files are ordinary host files; re-verification catches mutations before start, not hostile privileged mutation after verification. Official release key custody, secure bootstrap, rotation/threshold, signed remote metadata, rollback continuity across operator policy replacement, device power-loss/native rollout and external release need their own gates.
