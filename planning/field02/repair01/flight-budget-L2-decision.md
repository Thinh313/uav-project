# FIELD02 repair01 scoped flight-budget decision

22/10/2026. Contractor root explicitly authorized Builder to prepare exactly two additional owned SITL requests under repair01, after independent UI/authority source/mock gates. This is an L2 implementation decision within the user's authorized repair milestone; it is not a new campaign, hardware flight or production release. Video live acceptance remains separately gated.

Seven existing SITL requests remain retained and count permanently. Frontend admission changes from refusing when existing count≥7 to refusing at≥9; runtime admission changes from total including current≤7 to≤9. Consequently the eighth and ninth cumulative requests may be attempted; any tenth request is refused. A failed or aborted new request still consumes one. No request or runtime was created by this preparation.

- Fixed owned runtime root remains `evidence/field02/flight/runs`, so new runs append to the same auditable history without resetting counters.
- `Flight01.pins()` now reads fixed `evidence/field02/repair01/flight-source-pins.json`. It does not read/rewrite the original manifest for new runs.
- `pin.mjs --repair01` writes the new57-file manifest using exclusive creation and refuses an existing output. The default/original output now also uses exclusive creation, so it cannot overwrite historical pins accidentally.
- New manifest retains original manifest SHA and declares cumulative cap9/prior7/new2. The original `evidence/field02/flight/source-pins.json` is byte-identical SHA256 `3b98baf5918f0595e1d370c4f6b2cce6bea78d6074b8fcb9c691182e1f4b07de`.
- New immutable manifest SHA256 `46e2266eef05c2ad85dacf7e425ca696b0a16a088c895d43075968005c51f43b`.

`flight-budget-tests01.json` evaluates the exact JavaScript guard in an isolated filesystem mock at7/8/9 prior requests, validates real57-file pins through the actual class, and proves both old/new pin destinations refuse overwrite. `flight-runtime-budget-tests01.json` evaluates the exact Python runtime assert AST at8/9/10 totals. Both leave every request file unchanged and start no runtime.

All other disk, resource, ownership, confirmation, timing, speedup1, no-PARAM-write and no-retry gates remain unchanged. The runtime's aggregate FIELD02 evidence guard remains512MiB; root must confirm aggregate current footprint plus repair headroom before launch. Repair01's additional evidence budget remains192MiB. No media files, native source, APK, SDK, old evidence or production key was changed by this decision.

A later flight-source change would invalidate this generation. It must use a separately authorized new immutable pin manifest or defer launch; it must never overwrite the current or original manifest. The broader host/media final freeze remains root's responsibility after the media Builder finishes.
