# AERIS repository guide

Updated 26/10/2026. This private repository contains source, scoped fixtures,
research and milestone reports. It is not a self-contained production installer
or a backup of every raw flight capture on the engineering host.

| Location | Role |
|---|---|
| `app/`, `services/`, `tools/`, root `package.json` | Original web workbench; preserve frozen release/candidate bytes |
| `pilot/<milestone>/` | Isolated host adapters, cockpit and simulator increments |
| `native/<milestone>/` | Android shell, build definitions and scoped native code |
| `planning/<milestone>/` | TIP, QA harnesses, source pins and reproducibility notes |
| `snapshots/simstability03/` | Exact changed-source overlay from tested receiver03; not an automatically selected release |
| `delivery/COMPLETION-*.md` | Qualification of a specific revision and configuration; read failures and deferred gates |
| `research/`, `docs/` | Sources, decisions and product requirements; published claims are not observed hardware behavior |
| `.local/`, `runtime/`, most `evidence/` | Host-only caches, recipients and retained raw data; intentionally outside Git |
| `delivery/*` engineering archives/APKs | Host-only generated packages; manifest/checksum/qualification may be committed separately |

The current entry point is [product status](PROJECT-STATUS-2026-10-26.md).
Historical `LATEST.json`, package versions and READY labels apply only to the
named slice. A passing mock, archive verifier or old APK does not qualify a new
integrated APK, camera exposure or flight on Hera.

## Work safely

- Use the existing checkout. Do not copy the project into `/tmp` or download a
  runtime merely to inspect code. Read `AGENTS.md` and the parent instructions.
- `npm run check` performs syntax checks of the original workbench. Test scripts
  under `planning/` can start runtimes or write evidence; inspect their scope and
  use a fresh output path before running them. Do not blindly run all harnesses.
- `npm start` opens the historical host workbench. Android/SITL entry points need
  their own recorded prerequisites, pinned artifacts and admission. No launcher
  is authorized to select an arbitrary attached phone or physical vehicle.
- Current user disk policy is 20 GiB admission, 10 GiB runtime floor, plus the
  declared reserve and forecast. Do not lower executable guards to obtain PASS.
- Keep raw evidence, old failures, pending journals, frozen candidates and signing
  material intact. Ignoring a path in Git does not authorize deleting it.
- Private signing keys, credentials, APK/build outputs and large engineering
  archives are excluded. Never use `git add -A` to publish unexplained missing
  protected files as intentional deletions.

## Known checkout condition

At this maintenance checkpoint, 97 tracked paths were already missing, including
fonts, UI evidence, protocol definitions and a canonical BOM. They were retained
as existing working-tree deletions and excluded from the commit. No missing path
was restored or treated as an approved removal. Git HEAD still retains its
previous version; recovery requires a separately scoped exact-byte operation.
The previous evidence baseline records 165 preexisting missing paths overall;
that denominator differs from tracked Git paths.

Large raw files and host-specific artifacts are not backed up by this push.
Reports may link to host-local evidence which is absent in a fresh clone. Source
can be reviewed from Git; runtime reproduction still needs the declared cache,
artifact and configuration. Do not infer deployability from a successful push.
