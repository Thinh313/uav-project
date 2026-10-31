# Receiver runtime preparation capsule

This is a preparation tool and mock suite, not a working flight release. It
requires the separately supplied authorized private engineering receiver. Public
Git alone does not contain the candidate pools, APK, SDK, AVD or Linux image.
The held source/candidate and all runtime guards remain unchanged.

## Run mocks first

From the repository root, with Python3.12+ on macOS/Linux or WSL:

```sh
python3 -B -m unittest discover -s handoff/receiver-runtime03/tests -v
```

These tiny fixtures exercise layout, hashes/modes/hardlinks, disk admission,
profile routing, relocation and failure handling. They do not start Android or
SITL and do not certify real hardware, actual SDK/image availability or a beta.
Native Windows filesystem behavior is not certified.

## Prepare an authorized private receiver

Keep every machine-specific contract, profile, plan, receipt and log OUTSIDE Git.
Choose an existing private control directory outside all repositories and a new,
nonexistent managed destination outside Git. Do not copy or modify old campaigns.

1. Copy `CONTRACT-RECEIVER-TEMPLATE.json` to `CONTRACT.json` in that external
   control directory. Fill absolute source/destination/history paths. The source
   must be the complete private receiver, including all six artifact pools. The
   historical R08 reference is supplied here at `reference/R08-avd-baseline.json`.
   It is old provenance, not a fresh baseline or permission to reset counters.
2. Use existing supported Darwin ARM64 CPython3.14, Node24, authorized Android33
   ARM64 SDK/AVD and cached pinned Linux image. No install, new AVD, wiping,
   signing, actor launch or automatic cleanup is performed by this capsule.
3. Run the commands below with your explicit absolute paths. Outputs must have
   unused filenames. All `plan`, `prepare` and `check` calls MUST pass
   `--contract`: the unchanged helper's default local `CONTRACT.json` is
   deliberately absent from this public capsule.

```sh
capsule="$PWD/handoff/receiver-runtime03"
control='/ABSOLUTE/PRIVATE/CONTROL-DIRECTORY-OUTSIDE-GIT'
source='/ABSOLUTE/PRIVATE-RECEIVER'
managed='/ABSOLUTE/NEW-MANAGED-RUNTIME'
image='sha256:e27f0236daf88218a8a76a2c58c4c185e36fbc0c67e05d12ca5af9292f442f84'
python3 -B "$capsule/tools/runtime_layout.py" profile --root "$source" \
  --sdk '/ABSOLUTE/SDK' --avd '/ABSOLUTE/ANDROID-USER-HOME/avd/aeris-beta-m1.avd' \
  --adb '/ABSOLUTE/ADB' --android-user-home '/ABSOLUTE/ANDROID-USER-HOME' \
  --image-id "$image" --out "$control/PROFILE01.json"
python3 -B "$capsule/tools/runtime_layout.py" plan \
  --contract "$control/CONTRACT.json" --profile "$control/PROFILE01.json" \
  --out "$control/PLAN01.json"
python3 -B "$capsule/tools/runtime_layout.py" prepare \
  --contract "$control/CONTRACT.json" --plan "$control/PLAN01.json" \
  --out "$control/PREPARED01.json"
python3 -B "$capsule/tools/runtime_layout.py" check \
  --contract "$control/CONTRACT.json" --plan "$control/PLAN01.json" \
  --spec "$managed/evidence/runtime-observe04/emulator-spec.json"
```

The trusted reference config and R08 retain historical author paths and allocation
identifiers solely to prove their original SHA. They contain no live credentials
or current machine profile. The generated effective profile uses explicit receiver
paths. Config relocation permits exactly the image directory path replacement;
all other configuration and binary hashes remain fixed. AVD index routing is
validated and pinned. No SDK/AVD files are written or copied.

Preparation retains every original artifact inode group within the new layout,
using independent origin inodes. Old history stays sealed in the original
receiver. New active metadata, including the guardian spec's same-new-inode
planning alias, remains charged. Limits remain 8MiB artifacts, 64MiB metadata and
10GiB disk floor; preparation additionally requires 256MiB reserve plus a positive
forecast <=64MiB. Full runtime admission remains separate. Partial preparation is
retained without a final receipt; do not automatically delete, overwrite or retry.

A successful preparation/fixture run is NOT Android-SITL admission. The original
owner must still verify the cached image live, exact candidate/source, metadata,
artifact union, native state/quotas, power/lid, ports/PIDs and current disk budget.
Only the original owner may start the authorized bounded campaign after every
gate passes. ACK is not proof of execution. No drone hardware gate is waived.
