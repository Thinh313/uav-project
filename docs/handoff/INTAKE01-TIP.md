# INTAKE01: fresh-receiver acceptance

31/10/2026. Contractor scope. Receiver must clone the immutable original tag,
run its README verbatim, independently check the private package, and leave a
small reproducible path for another researcher. Product beta qualification is unchanged.

## Scope

Only new handoff helpers, tests, handoff docs, manifest/validation and regenerated
handoff PDF may change in uav-project. Do not alter app/services/native/pilot,
VIDLIFE12 selected source, source/candidate or ENDURE in the original aeris checkout.
Preserve original tag research-handoff-2026-10-31. Publish a new intake revision.
No SDK install, APK signing, emulator/SITL launch or flight command in this task.

## Expected receiver path

Clean network clone -> original README checks -> owned historical HTTP smoke ->
read-only private bundle validation -> deliberate preparation of a NEW private
workspace without a Git remote -> original source/mock checks in that workspace.
A checksum is integrity against a supplied digest, not owner authentication,
runtime/SDK admission or flight acceptance.

## Repairs

Provide a compact portable private-bundle CLI with verify and prepare commands.
Require external expected SHA (or sha-file), exact safe member paths, bounded
counts/sizes, checksum and manifest equality. Check source/context/engineering
inner bytes and hardlink targets. Preserve hardlinks/modes during preparation,
allow only expected anonymized-context overlays or identical duplicate bytes.
Private destination must not exist; refuse symlink/path escape, unsafe member
kinds, wrong digest, truncation and insufficient disk. No extraction into a
public Git workspace, no overwrite, deletion, remote mutation, image load or
actor launch. Preparation is NOT operational admission.

Provide one portable source/mock intake command if it improves exact README
usability. Keep existing mock commands and guards intact. Do not run broad legacy
npm test again without reason; prior floor/timing failures remain disclosed.

## Resource and evidence

No project copy under /tmp. Clean checkout and private receiver workspace are
permanent, task-named directories under the shared project parent. Floor10GiB
plus256MiB reserve and declared positive workspace allocation; stop if insufficient.
Use in-memory bounded archive reads or owned fixtures in ignored task paths,
clean fixtures after test. Preserve old package and old receipts; version new ones.

Root owns actual clone/README/bundle checks, final source graph154 comparison,
original-tree preservation, PDF review, new Git tag/push and final offline package.
Builder owns helper implementation and adversarial fixtures. Do not claim beta,
real-Hera compatibility, image runtime or a full legacy-suite pass from this task.
