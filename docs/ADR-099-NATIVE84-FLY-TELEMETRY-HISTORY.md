# ADR-099: Primary Fly telemetry and committed Android history

Accepted within NATIVE84 scope. Keep the frozen NATIVE83 bridge and mission gates unchanged. Create native/native84 and evidence/native84, separate package/origin/host port 8847 and owned SITL port 5884. Reuse the retained owned emulator AVD without copying or wiping its existing application data.

Add a pure presentation reducer with explicit source/session/boot/run, increasing envelope sequence, per-field host ages and local receipt expiry. A final paint hook provides sole ownership of Fly display after baseline mock paints; the mock journey remains available in its original scope. The new main Fly defaults to unknown before a selected owned session.

Extend copied DraftStore with read-only committed-chain pagination and exact-token lookup. A cursor binds the selected HEAD; concurrent append rejects the page/selection until explicit reload. Orphan revisions are never history. Pending HEAD is a visible error, never silently accepted. New review format includes full bounded observed trajectory and SHA, geometric context, and original raw references. Android journal hashing/SAF archive constraints continue to apply. Archive wire format AERISARCHIVE83 is retained.

No runtime authority is serialized/restored by history, archive or restart. Live display is simulation telemetry, not Hera qualification, actual camera media or real flight certification. No new production signature or Fly integration into the frozen candidate.
