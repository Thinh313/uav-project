# M1 native runtime runner contract

New diagnostic shell, **not final cockpit**. Package `vn.rtr.aeris.beta01runtime`,
Activity `.RuntimeActivity`, singleTop. The development APK is debuggable solely
to support owned emulator fixture injection and extraction with `run-as`.
No physical provider or non-emulator endpoint is accepted.

Before launch, root independently checks build/source/AP/config/model pins,
actual emulator profile and storage admission. Expected provider is a pinned APK
asset. RuntimeContext is not restored from saved history.

Root writes exact UTF-8 bytes to application-private `files/launch-binding.json`
using ADB `run-as vn.rtr.aeris.beta01runtime`; root supplies its SHA256 in an
explicit Activity intent. App checks file SHA, bound expected descriptor and
actual `ranchu` hardware before opening a socket. Root's launch observation is
trusted local orchestration input, **not remote authentication**.

Binding JSON fields: version1, rootOwnedContainer=true, targetSystem42,
mode=CANDIDATE_EXTERNAL, profileId/binarySHA256/modelSHA256/configSHA256/endpoint/
firmware (must equal APK asset), run/epoch/boot/operator/generation (new exact
identifiers ≤128chars). `boot` is root's AP launch-generation identity; actual AP
time_boot_ms is recorded separately and regression revokes the session.

```text
adb -s emulator-5582 shell am start -n vn.rtr.aeris.beta01runtime/.RuntimeActivity
  --es m1Action CONNECT --es launchBindingSHA256 <exact-root-file-SHA256>
```

`CLOSE` and `STATUS` use the same component and `m1Action` extra. A successful
CONNECT opens only `10.0.2.2:5961`. One native socket thread is sole writer, no
HTTP flight broker, reconnect, retry or persisted lease. It retains each raw RX
chunk before parsing and every TX intent/fsync before write/flush, then records
WRITTEN or UNKNOWN. A WRITTEN record is local transmission only.

Private output paths (extract after owner closure):

- `files/probe-<UTCms>.json`: actual API/ABI/fingerprint/app/WebView/viewport/
  insets/font scale, actual EGL/GLES pbuffer renderer, available codec names.
  Profile `NO_MEDIA_M1_RUNTIME` explicitly has no media capability;
  decoderBackend=NOT_STARTED_NOT_OBSERVED. It does not satisfy full Beta media.
- `files/latest-state.json`: atomic replaceable current checkpoint, explicitly
  not append-only raw evidence. Closed elapsed/authority are from lifecycle.
- `files/runs/<run>/`: append-only segmented raw/lifecycle records, seals and
  session manifest. Never reopen an old run. On restart prior records persist;
  no automatic connection or restoration of authority occurs.

First smoke remains read-only: native GCS heartbeat, typed parameter requests,
AUTOPILOT_VERSION, Home and position/land telemetry stream requests. Expected AP
is target42/component1, firmware4.7.1/dbe79216. Literal duplicate/old MAVLink wire
sequence cannot refresh readiness; ambiguous half-range and boot regression fail.

Optional **separately enabled** manual diagnostic capability is false in the
initial profile. `CONSENT` requires actual minimal probes plus exact typed
Profile95/Home/land/position/firmware observations. `GUIDED`, `ARM`, `TAKEOFF`,
`LAND` each represent an explicit UI/root test action with a newly observed zero
input and a200ms one-shot lease. They do not run automatically. `TAKEOFF` is
fixed3m; it requires observed armed/GUIDED/on-ground state. RC `PULSE` is guarded
and zero-axis by current UI; it is not a continuous manual training controller.
These diagnostic hooks are not completed M1 manual/assisted qualification.

`RuntimeActivity.onPause/onDestroy` closes the owned socket and revokes inputs.
`CLOSE` is a managed local close, not LAND or a ground observation. Root must use
a declared simulator abort/landing protocol if an armed manual case is admitted.
Reader/journal/UI failure never permits another flight send.

Cold receiver:

```text
python3 -B native/betaintegrated01/runtime/receiver.py <extracted-run> <run> <epoch>
```

It returns COMPLETE_BYTES_UNATTESTED for complete unanchored bytes. An externally
retained successful-close session SHA may be supplied with `--expected-commit`;
even a match never enables publication or claims aircraft execution. Never infer
the trusted external anchor from the same untrusted extracted package.

Native guest quota is128MiB,1MiB segments/256segments, bounded record8KiB and
256MiB guest free reserve. These are distinct from host20/10GiB+256MiB/15s
forecast guards owned by root. Native raw format does not assert host/AP model
frame completeness; root independently verifies host and AP streams.
