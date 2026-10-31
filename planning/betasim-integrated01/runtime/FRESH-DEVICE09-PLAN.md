# One fresh owned simulation device, preparation plan (not executed)

This is a new engineering test target, not product migration, journal rotation, or a remedy for retained UNKNOWN generations. The original `aeris-beta-m1.avd`, every original private-file TAR, all eight-generation source limits and all prior campaign counters remain unchanged.

## Fixed target and transitive inputs

The only proposed new target is `.local/betaintegrated01/android/avd/aeris-betasim-fresh09.avd`, with its exact adjacent `aeris-betasim-fresh09.ini`. Its fixed AVD name is `aeris-betasim-fresh09`; its only allowed serial is `emulator-5582`. A creation command must refuse either path already existing. There is at most one created target; later campaigns reuse its actual retained state.

Use only the cached `native86-android/sdk` emulator and Android33/default/arm64-v8a image, with the same pinned executable/system.img/source.properties hashes as the original spec. Pin the original cached userdata.img (1,048,576 bytes), encryptionkey.img (18,874,368 bytes), kernel/ramdisk and generated exact config before creation. No SDK download, old-AVD copy, old writable hardlink, old snapshot, wipe-data, clear-data or hidden journal move. The selected APK remains `77c65876eecb6d4fbc68a113bf682fa416c4272b3ed1de71f803c63df58d1b21`.

Create only the bounded text config/ini and required pristine seed files; emulator-generated files must remain inside this one new root. The new spec must contain a versioned `deviceState` object: fixed paths/name/serial, unpredictable creation nonce, exact creation-receipt path/SHA, cached input pins, old-retained-root path, and the aggregate-growth baseline reference. The new Root entry must pass exactly the selected admitted spec to its guardian. Current source incorrectly hardcodes the old guardian spec and rejects any AVD name except `aeris-beta-m1`; these must be explicit versioned branches, never a permissive arbitrary `--spec` bypass.

## Growth accounting and feasibility

Before creating any new file, record the original retained AVD's per-path device/inode/allocated-byte baseline. The new root has an empty baseline, so every newly allocated byte, including first-boot cost, is positive growth. Aggregate positive growth is SUM(old-root positive growth, new-root positive growth), with no contraction offsets, no credit refund, no rebaseline after first boot, and the original hard cap 536,870,912 bytes. The same creation baseline and used credits carry into both r07/r08; each campaign's local counters retain their original domain and limit. Count retained old native private-file bytes as an additional observed historical domain, not as new-device zero. Root task/STATUS/DATA/SAF limits do not reset because a device changed.

Current original AVD total allocated bytes are 912,932,864; its R01 baseline was already 888,377,344. This is historical baseline allocation, not permission to waive the new target's startup growth. New first-boot allocation is UNKNOWN. The pristine seed is small, but no evidence proves a genuine new boot fits 512MiB. A strict bounded preparation may stop with its partial target retained if it approaches that cap; it cannot erase/retry the target or declare admission from a post-boot baseline. If first boot requires the original target's ~0.85GiB overlay scale, this plan cannot fit the unchanged cap and must report a real blocker.

Disk forecast must reserve this full remaining 512MiB growth envelope, source/artifact allocations, raw capture hard bounds, native TAR bytes and original 10GiB+256MiB floor before any creation or actor. No creation is currently admitted by this document.

## Genuine target and native producer identity

After the owned QEMU launch/readiness barrier and before root/install/enrollment, record original bounded ADB outputs for the selected serial: `getprop ro.boot.qemu.avd_name`, `settings get secure android_id`, and the actual package private directory after installation (`run-as vn.rtr.aeris.mission pwd`). Bind these original command receipts to the source-held QEMU PID/start/argv, new userdata/backing file identity, creation receipt/spec SHA and creation nonce. Reject unknown/empty/mismatched identifiers. These are Root-observed guest/device facts, not native-reported attestation.

Fresh-package absence must be proven by exact package-manager output plus a strict new-target creation proof. Only that branch permits one new development install; it must not reuse the current predecessor-install path, which correctly requires an existing package and cold backup. No old device application is uninstalled or cleared. Existing package targets continue the old backup-required branch.

Root then joins genuine native DUMP ACK and original DTO PID/processEpoch/source/key/generation to this device proof, and includes the proof in Root registration, native closed-TAR manifest and raw-management handoff. Do not inject Root's deviceStateID into native fields or imply native independently reported it. Every later observation must remain on the same guest/device/Root enrollment; planned process restart changes the original native key/epoch only through existing explicit rollover, with no authority restoration.

## Required causal checks before Root may create it

Actor-free tests must cover wrong/foreign spec/name/serial/creation receipt, missing cached input SHA, existing new root, symlinks/writable old hardlinks, old+new positive growth with no contraction offset, persistent baseline across campaigns, unknown growth, wrong AndroidID/AVDName/filesDir, package-absence on an old target, and native ACK/producer joined to a foreign device proof. Original candidate loaders and old AVD/input fingerprints must remain byte-exact. Creation and actual guest identity remain NOT_CHECKED until Root explicitly performs them.
