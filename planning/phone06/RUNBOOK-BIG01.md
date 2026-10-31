# PHONE06 code and actual acceptance

All commands run from `/Users/os/Downloads/AI technique/aeris`. This is a simulation-only isolated development package, not a flight release. Phone absence blocks installation/actual acceptance, not code review. The broad historical baseline has missing paths; active dependency closure is checked separately and does not repair that baseline.

## Offline source and compile

`python3 -B planning/phone06/entrypoint.py source`

`python3 -B planning/phone06/rig06.py --dry-run`

Builder receipts are in `evidence/phone06/builder/checks02.json` (29 original declared input cases) and `targeted02.json`/`targeted03.json` (trust durability repair and six actual feed input variants). The grouped feed-count mistake is retained in `feed-accounting-correction01.json`; aggregate cap was prospectively reassessed to57, not retroactively described as54-compliant. Full cached Android javac, fixture javac, actual native post-WAL boundaries and JS syntax are offline evidence, not Android ART, USB or aircraft evidence. Do not rerun all green cases without a new reason.

## Build, install, public provisioning

Root may build after source/QA gate and resource admission: `python3 -B native/phone06/build.py 01`. Existing cached development key only, no key creation. Script pins all sources, signs and verifies v2/v3/signature/certificate, compares unsigned ZIP payload and retains signed APK/build receipt; removes unsigned/staging in finally. Do not reuse an attempt number or overwrite receipts.

Connect one authorized Xiaomi by USB, enable USB debugging and accept its prompt. Use cached `/opt/homebrew/share/android-commandlinetools/platform-tools/adb` (the entrypoint resolves it explicitly). Enumerate `/opt/homebrew/share/android-commandlinetools/platform-tools/adb devices -l`, then exact selected `/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s SERIAL get-devpath` must prove `usb:`. Never switch adbd modes, auto-connect TCP, root the phone or read unrelated data.

`/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s "SERIAL" install --no-streaming "PATH_FROM_BUILD_RECEIPT"`

`/opt/homebrew/share/android-commandlinetools/platform-tools/adb -s "SERIAL" shell am start -n vn.rtr.aeris.phone06/.ShellActivity`

Use the app's explicit crew identity initialization. Export **public identity** through Android SAF; no private key leaves AndroidKeyStore. Root creates a PUBLIC trust policy from this exact native public identity and the independent host B public EC certificate using the existing crew02 trust schema (`format`, `version`, `realm`, `aircraft`, `nativeSpkiSha256`, increasing `trustEpoch`, `peerCertDerBase64`, `peerCertSha256`, `peerSpkiSha256`, `peerPrincipal`, comma-separated explicit `peerScopes`; validate exact inherited schema, no invented member array). Import it through the PHONE06 Public trust picker while disconnected. Full inherited certificate/context validator runs before atomic commit. Identical explicit repeat revalidates and forces file+directory before success; conflict or uncertain durability refuses. The original Android KeyStore/mTLS actual gate remains required on the Xiaomi.

## Controlled campaign

Root fills a new admission file from `planning/phone06/phase-template.json`, using actual APK/source SHA, selected serial, unique run IDs and fresh resource forecast. The template itself is never admission. Admission is engineering evidence, not cryptographic aircraft attestation. Default nonneutral manual qualification remains false and qualification issuance UNSUPPORTED until a separate actual proof policy exists.

`python3 -B planning/phone06/entrypoint.py preflight --admission ADMISSION.json`

`python3 -B planning/phone06/entrypoint.py usb --admission ADMISSION.json --apply`

The USB script requires exact authorized `devices -l` row and USB devpath. It creates only reverse5960/5961 and forward5942/5967 after conflict checks, records ownership and never kills old listeners.

`python3 -B planning/phone06/entrypoint.py run --admission ADMISSION.json --run RUN --case nominal`

The derived lifecycle controller preserves one connect, no bootstrap TX/retry, passive guest-listener readiness, speedup1/cap500ms, full frame/raw retention and honest cleanup/exit/seal. It uses a newly named aeris-phone06 container and explicit phone ports. Root waits for actual owned guest native listener5766 plus bootstrap proof, not launch.json alone.

`python3 -B planning/phone06/entrypoint.py ticket --admission ADMISSION.json --run RUN`

The public owned descriptor is passed as an explicitly quoted Intent extra, not a nonexistent SAF launch picker. On a stopped own package, run `python3 -B planning/phone06/entrypoint.py launch --admission ADMISSION.json --launch-json "evidence/phone06/runtime/runs/RUN/launch.json" --apply`. It proves USB, validates descriptor, refuses a running own process, safely quotes the remote am command and starts fixed ShellActivity with `source87=direct` plus bounded `owned95` JSON. It neither connects nor grants. Then explicitly validate USB simulation in the phone controller panel. A repeated or unknown launch attempt is not retried automatically. Stop an old own app only after known ground/closed state using an explicit Root action; the launcher never kills it. Host ticket checks current owned CID/PID/start/binary/run/source, native guest listener and challenge before issuing <=900s phone-local admission. Request deadline3s; no automatic renewal. The app remains sole GCS and WAL/fsync precedes wire.

## Actual workflow and independent operator

On phone: import KML or supported QGC SimpleItems, inspect/datum/compile, fresh typed preflight, exact upload/readback, arm approval and post-arm Home, then explicit AUTO. Unsupported complex QGC/fence/rally remain review-only/refused. No automatic arm or reconnect.

Start host B explicitly with its existing private test identity stored outside evidence:

`node native/phone06/host/companion.mjs --identity-dir IDENTITY_DIR --native-public PUBLIC_IDENTITY.json --evidence-root evidence/phone06/runtime/runs/RUN/operator-b`

Open `http://127.0.0.1:8861` and use explicit Connect→Join→claim/propose/accept. Independent mTLS identity, scopes, sequence/CAS, presence and after-WAL authority gates are retained. Phone/operator A does not synthesize B heartbeat. Actual phone TLS/camera/gimbal/routing/partition/reboot evidence is pending, not inferred from mocks.

Manual touch is LOITER5 only, correct Mode2 axes, neutral ready, separate pointer IDs, strict fresh sample/new sequence and native250ms lease with actual wire>=50ms. HOLD/RTL/LAND are explicit. Nonneutral actual controls remain disabled until qualification; do not flip a flag based on typed parameters. AP fallback and RC timeout still need actual proof. Takeover permanently disqualifies autonomous survey completion and cannot resume AUTO in that run.

## Read-only 3D and diagnostics

Phone explicit **Mở nguồn quan sát** starts loopback5967 with run/generation/source shown. Host receives its per-run secret only through its own0600 `.local/phone06/secrets/RUN.cap`, generated by admission; no secret in URL/UI/WAL/evidence. Do not copy this file into evidence.

`python3 -B pilot/phone06/mirror.py --run RUN --generation PHONE_GENERATION --source-id NATIVE_SOURCE_ID`

`node pilot/phone06/server.mjs --mirror evidence/phone06/runtime/runs/RUN/native-mirror.jsonl --clock-bracket evidence/phone06/runtime/runs/RUN/clock-bracket.json --run RUN --source-id NATIVE_SOURCE_ID --plan-sha256 PLAN_SHA256 --evidence-root evidence/phone06/runtime/runs/RUN/viewer`

Open `http://127.0.0.1:8862`. Full licensed visual56 PBR/GLB/HDR assets are dependency-pinned; missing historical font paths use byte-exact read-only crew02 font aliases. Viewer is never a second GCS. Audio opt-in is synthetic, no microphone or sensor sound claim. Source age is WAL append proxy plus clock uncertainty, not end-to-end sensor latency. Stale/closed feed pauses motion and becomes UNKNOWN. Mirror closure is always conservatively PARTIAL; terminal raw and final completeness come from public SAF export, not last fetched size.

## Review/export and cleanup

Use phone ground/disarm completion guards, honest review and explicit SAF raw export. Independent receiver:

`python3 -B planning/phone06/entrypoint.py receiver --package EXPORTED.zip --run RUN --expect PREDECLARED.json --expect-sha256 PREDECLARED_SHA256`

Before export, Root declares a bounded expectation with exact format `aeris-phone06-public-export-expectation`, version1, run, receiver, nonce, snapshot UUID, exporterSourceId and rawSourceId; SHA-pin it independently. The receiver requires that receipt and rejects changed or self-described context. It verifies bounded stored ZIP membership, SHA chain, META/run and closed/prefix/torn-tail extent. It asserts neither actual mission acceptance nor TLS identity, images or authority restoration. Crew audit/B chain/manual/failsafe/phone screenshots remain separate evidence.

Stop only owned Node/mirror/viewer/controller processes. Mapping cleanup works even after admission expiry or low-resource stop:

`python3 -B planning/phone06/entrypoint.py usb-close --usb-receipt evidence/phone06/runtime/usb-SERIAL.json --apply`

It refuses changed mappings and removes only exact recorded same-source/destination ports. Never prune containers/volumes or delete evidence. No actual runtime, phone installation or acceptance is claimed by this runbook.

## Touch preview

Root only: `python3 -B planning/phone06/preview06.py`, then `http://127.0.0.1:8860/index.html`. Preview stages pinned assets in owned `.local/phone06/preview`, removes them on shutdown and is mock-only. Validate844×390,915×412 and1280×800, popovers, theme sun/moon, safe area, 48dp actions, both sticks/release and reachable HOLD/RTL. It does not replace physical Xiaomi UI/ART/input tests.
