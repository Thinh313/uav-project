# H7: SAFE_GNU_LONGNAME_L_V1

This is a new explicitly selected read-only transport schema. It preserves only
the original device TAR. It creates no normalized TAR/view and never retries an
old strict decoder after failure. Historical H6/m501 results remain unchanged.

Python `tar_profile_h7/reader.py` and Node `tar_profile_h7/native-tar.mjs` validate
all physical headers, checksum, octal fields, zero padding and complete framing.
Only one GNU `L` pathname metadata carrier immediately followed by its matching
regular header is permitted. It is not a file. Links, K/PAX/sparse/device/FIFO,
chains, orphans, traversal, duplicates and nonzero extra fields remain refused.
Existing logical AJ02, workspace, original-file, registry and crypto checks run
only after this transport validation. No files are extracted.

The selected source asset `assets/native-tar-profile-h7.json` binds the profile,
Python/Node source SHA and layer-specific limits: original receiver192MiB;
current native/SDK producer64MiB; legacy producer168MiB; logical512MiB;
8192 logical members; UTF-8 path240 bytes. The six original export filenames,
192MiB aggregate reservation, all eleven artifact pools,13/68MiB host caps,
14 owners/future60686336 bytes,100/200/250ms guards and APK remain unchanged.
`android.py`, metadata_budget.py, inventory.py, emulator.py and guest_sync_h4.py
are byte-identical to H6. Original V1 capture rows still identify the raw bytes.

The SDK report binds a separately recomputed profile observation to the exact
original captureRef. The closed-native observation, fullraw manifest and product
descriptor bind selected profile/source hashes; independent Node receivers check
the selected source identity. Historical candidate loaders remain unchanged.

Root first qualifies fresh SDK-only slots m601/m602 on one future immutable
release, actual selected APK/private originals and distinct genuine boot UUIDs,
with normal SDK exit0. The existing unconsumed g104 entry accepts only that
same-release Root proof; it resumes the already reconciled registry and sends no
PREVIEW/APPLY/install. No SDK-only closure claims flight or current authority.

Example Root entry (after independent QA, candidate and admission):
`root-reconcile-h7.py --candidate <Root-selected> --candidate-sha <SHA>
--spec evidence/nativejournal17/emulator-spec.json --intent <Root-intent>
--intent-sha <SHA> --install-stage-proof <Root-prerequisite>
--install-stage-proof-sha <SHA> --slot m601` (then m602 with its prerequisite).
`root-native-h7.py` retains the existing g104 CLI and requires the H7
`aeris-h7-root-reconciled-sdk-cold-acceptance` proof with eight exact original
m601/m602 observation/guardian/SDK/private references. No actors were launched
by Builder. Current mock/offline replay is not Beta acceptance.

The discarded unheld paired spike is retained in
`planning/betarc01/H7-PAIRED-SPIKE01.tar.gz`. The two generated H6 assets were
briefly written through a restored hardlink during prepare, then restored to
exact baseline SHA at the original inode from the untouched frozen candidate.
The incident retains the written bytes and makes no continuous-SHA claim.
Prepare now publishes only the two exact assets using atomic copy-on-write,
with an exclusive pending file, fsync, replace and directory fsync.
