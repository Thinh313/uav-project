# BETA06 Builder handover

Production source is frozen; source/mock clearance does not establish actual beta readiness. Parent Contractor alone operates Android, browser, host listeners, SAF and AP/SITL.

## Launch and data

From the AERIS root:

```sh
node pilot/beta06/app.mjs evidence/beta06/host-app01 --allow-sitl '--workspace=/Users/os/Downloads/AI technique/aeris/evidence/beta06/workspace01'
```

The second and final host uses `evidence/beta06/host-app02` and the same workspace. Control8872/media8873/AP5972 remain fixed. Explicit source start, viewer start and authority grants remain required. The stage contains132 files/4,716,316 bytes; it reuses declared immutable aliases and does not restore the95 preexisting missing paths. The shared workspace is an exact17-file/785,280-byte data fork; lineage and hashes are in `evidence/beta06/workspace-copy01.json`. Its inherited captures/reviews do not count as BETA06 execution.

## Frozen boundaries

`evidence/beta06/flight-pins.json`: SHA256 `f084141186b41856dbbbbb9b9faeb88b4454e1f7307277933fe927e0852db119`,265 files,34,945 bytes. It binds the prior immutable manifest,11 legacy request hashes, new production files and final11-file helper manifest02.

`evidence/beta06/builder-source-freeze01.json`: SHA256 `08be3d0ffe6225744f820727af53bc64d8274843ce20e4c64818ddf994ceb6b5`. It inventories21 new source/test files plus the derived stage and proves effective adapter dispatch, empty new run root and source syntax.

`evidence/beta06/builder-source-ready02.json`: SHA256 `9ae5c1701fedf748236dee8ad7c5e864192df706d83991d72010f446423b4e80`, final helper manifest. Earlier helper manifest01 is retained and superseded.

New paths only: own app/resource/media wrappers, flight base/takeoff/adapter/runtime, namespace-only strict handoff/delivery adapters and narrowly diagnostic SAF UI. Unchanged CLOCKVIDEO05 control, clock, authority, mission, media profile, queue/dependency and raw-verifier semantics are reused. The new adapter overrides the dormant inherited connect/pins methods; the effective new counter refuses request5 before writes. Old source/caps/pins/native/evidence/ENDURE remain read-only.

## Executed source/mock commands

All commands ran without a listening socket, AP, browser or emulator:

- `python3 -B pilot/beta06/stage.py`:132 curated files, no dependency download/build.
- `node pilot/beta06/saf-tests.mjs`:2 mock groups PASS; exact reference/ground/one-hex/one-attempt policy, not native proof.
- `node pilot/beta06/namespace-tests.mjs`:5 groups PASS; normalized changes, effective inheritance and new4/5 boundary.
- `node pilot/beta06/receiver-tests.mjs`:2 groups PASS on a read-only historical protocol-mock archive; not a new beta execution.
- `node pilot/beta06/http-handler-tests.mjs`:8 groups PASS using real handlers in-process; no listen/AP.
- `node pilot/beta06/reuse-tests.mjs`:4 groups PASS; frozen algorithm normalization and diagnostic UI contract.
- `node --check pilot/beta06/pins.mjs` and `node --check pilot/beta06/freeze.mjs`:PASS.
- `node pilot/beta06/pins.mjs`:exclusive canonical pin manifest emitted, exact frozen-save serialization PASS.
- `node pilot/beta06/freeze.mjs`:all265 pins matched, source syntax/AST checked, no new AP request, effective override proof PASS.

Independent QA source/helper reports are separate evidence; their final gate is required before actual launch.

## Mandatory runtime limits and unknowns

Maximum2 hosts/2 coldboots/4 distinct AP requests,30 minutes per host and540 seconds/AP; no retry or quota reset. Admission/runtime resource guards and all freshness thresholds stay unchanged. The fixed development APK remains unchanged. Native lifetime10/16 leaves exactly6 picker operations; the explicit wrong-SHA diagnostic must consume0 and requires actual callback/journal proof. URI-dispatch acknowledgment is not native completion or provider readback.

N1/N2, airborne synthetic capture/gimbal, video windows, real C2cut/AP reboot, persistence and SAF outcomes remain NOT_CHECKED by Builder. No physical Hera, real camera/gimbal, standalone-controller, radiometry or production-readiness claim follows from these tests. All selected actual results must be reported against the fixed supported internal configuration.

No build/cache/download/full-project scratch was created. Derived owned stage may be removed only by Contractor's final owned-cleanup plan; evidence and shared workspace are retained.
