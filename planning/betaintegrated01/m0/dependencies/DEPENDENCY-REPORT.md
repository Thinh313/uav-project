# M0 dependency/source-intake result

Status: **source inputs bound for adaptation, not a runnable beta release**.
Only this new dependency/planning/evidence scope was written. No product code was
imported, compiled or executed. No build, install, AP/Android launch, signing or
restoration of an original path occurred.

## Exact source result

- Conservative union:372 files/30,331,042bytes,440 static/reference edges.
  This is source/reference inventory, not a reachability or executable allowlist.
- Native98:47 Java source inputs,29 in the historical explicit APK Java list,
  plus generated BuildInfo90.java during a future controlled build. Other Java
  files are host-test/unselected inputs; they are not all production classes.
- Native98 virtual static assets:104 files,114 direct static ESM/HTML/CSS resource
  edges,0 unresolved after exact bindings. The104 assets consist of98 present
  resources plus6 missing-resource bindings.
- Missing Native98 resources: two definitions imports, three Barlow font targets
  and one camera-concept PNG. These extend beyond the97 tracked deletions because
  missing generated/broken-link assets are not all represented by Git deletion
  status. All six expected digests are pinned by `evidence/native98/build02.json`.
- Actual byte intake:3,496,744bytes total, under8MiB. One300,461-byte Git definitions
  body binds two Native98 projections; three font bodies and one PNG are copied
  separately. Origins include Git commit/blob and SHA256 in resource-intake01.
  These are new intake paths only; old originals and broken links remain untouched.
- Cold check of all47Java +104virtual assets matches historical build02 digests
  with0byte drift. This does not promote the historical APK's runtime acceptance.

## What remains to materialize

All37 conservative-union issues have a disposition:

- directory anchors/output roots are not missing executable modules;
- two Native98 definitions imports bind to exact intake;
- browser viewer imports resolve through explicit old HTTP asset routes:
  `clock-lifecycle`, `network-bootstrap`, `client` from `pilot/clockvideo05/media`,
  and `relay-core` from `media/big02`;
- the SIMSTABILITY03 snapshot is an overlay at logical `pilot/simhand01`, not a
  runnable physical module directory; authority comes from original logical path.

The source exists, but the following6recipes remain explicitly excluded as new
release executors until M1 materializes audited modules/build inputs:

1. Native98's historical directory scan, generated BuildInfo and build/sign paths.
2. Workbench hash-pinned text UI projection and inverse-count assertions.
3. MissionBeta/BetaVideo projection injecting host session controls into Workbench.
4. BetaVideo rewrite/import of historical server through `data:text/javascript`.
5. MissionBeta source rewrite/`exec` of beta06g17 flight runtime.
6. SIMSTABILITY03 overlay inheritance and its separate host TrainingLink authority.

There is no claim that the broad union is a no-unlisted-executable runtime closure.
The smallest M1 boundary is a new explicit Native98-derived native owner/provider
and lifecycle contract, with standalone modules for media/mission projections.
Historical launch/build helpers are reference inputs, not selected entrypoints.

## Provider incompatibilities to retain as blockers

- Native98 Activity requires Android hardware `ranchu` and an owned AP proof.
- Native socket is10.0.2.2:5937; logical JS target is127.0.0.1:5937.
- It binds internal-quad AP SHA011627d4…, while SIMSTABILITY03 uses external
  reference physics, a different port/context and AP SHA f2be1f34….
- Native98 rejects a second open in the same Activity. Reusable sessions require
  a versioned lifecycle fix and tests, not deletion of the old fence.
- There is no Native98 OperationGate.java. NativeSend98/WireGate95/UnifiedCore98
  are the transport gates; MissionBeta OperationGate belongs to a different shell.

## Small complete input set for initial mocks

`m1-mock-java-inputs.json` pins10 resolved pure-Java source inputs for the shared
send boundary, unified flight/payload policy and raw journal. No Android imports,
DirectTransport socket, AP binary, private keys or competing host GCS writer are
selected. This makes an initial bounded mock task possible without claiming a
fully assembled or installed APK.

Machine outputs:

- `source-reference-union.json`: broad inventory and static evidence.
- `native98-virtual-input-closure.json`: precise source/resource bindings.
- `projection-and-unresolved-disposition.json`: all37dispositions and6recipes.
- `m1-mock-java-inputs.json`: narrow source reference closure.
- Latest QA: `evidence/betaintegrated01-m0/dependencies/verification02.json` and
  `cold-recheck01.json`.

The first virtual-closure assertion correctly exposed the absent camera PNG.
Verification01 used the ambiguous field name `boundMissingNativeDefinitions` for
all6resource bindings; verification02 corrects it to2definitions/6assets without
overwriting the earlier receipt. Generation scripts use exclusive outputs; do
not blindly rerun them over their existing receipts or intake paths.
