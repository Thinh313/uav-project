# H10: durable generic command results and read-only forensic capture

G105 reached the owned companion READY and both public native closed-unused
journeys, but its source seal's full COMMAND_COMPLETE exceeded progress4KiB.
The exact original oversized result length was not retained and is not invented.
The source seal had effects before the ACK failure. Old G105 remains failed,
its final native TAR was not captured and the G10375-file/8-archive decoder
cannot be reused as a proof of the changed state.

All management actions now use command_h10/command-result-h10.mjs. A lossless JSON
envelope binds run/full runtimeContext/candidate/ownerPID/companionPID/sequence/
action/full result. Existing reports file1MiB and owner/global caps remain; writes
use at most16 original payload64KiB chunks, exclusive first then append. Every
chunk must return the real original writer commit ref. The fullfile SHA/bytes
and final original chunk ref are emitted in a small COMMAND_COMPLETE only after
all commits. JSON values that would silently disappear/change are refused.
A fault keeps the prefix and says action may already have executed. No retry,
overwrite, quota increase, truncation or special SEAL-only summary is introduced.

Root command_results_h10 reads exact original control/ACK/result bytes, rejects
symlink/path/crosscase/candidate/command/PID/SHA/size/partial/duplicate claims,
checks the current owner's original committed-file highwater/final writer ref,
and returns the reconstructed full result. Both isolated Root consumers
root-native-h10.py and root-owner-h10.py call this one reader only after matching
kind+sequence. The latter covers G2/G3/G4. The selected companion itself is an
explicit alias/new argv selected through the H9 central pre-spawn boundary; old
Root/Node sources are immutable. Future G1 drivers are prepared but not admitted
for the changed G105 state. No G105 command may be resubmitted.

Real mock Unix-socket tests use the actual Node helper, actual ProductWriterClient,
actual Python ProductWriter wire/dispatch/fsync and actual Root reader. Larger
than64KiB results roundtrip as two result commits plus one progress commit under
the original200ms/64KiB guards. Separate tests run the actual source sealForRoot
body with synthetic size-stress inputs and retained G105 media; these do not
claim the missing original G105 full result or whole app runtime acceptance.

The required wire test also exposed a distinct normal-close race: a client could
close before Root declared writer closure and trigger genuine unexpected EOF.
Both normal owner close paths now use shared begin_managed_close after their
required proofs. It checks writer/observer health, atomically revokes new data
admission and drains the one admitted data frame through reply+trace completion,
using its ORIGINAL first-byte+200ms deadline and a begin+200ms ceiling. It tracks
an operation, not idle clients; no sleep, retry or extended deadline. Failure
poisons the writer and cannot become a normal close. Health is checked again in
the postclose receipt, including observer failure and actual thread drain.
Emergency begin_close/disposal remains separate. Tests force ACKfile-visible/
reply-pending completion below the original deadline, overdeadline refusal,
preexisting unexpected EOF, pending/failed closes and no normal-claim bypass.

Only m801 is added as a fresh forensic slot. root-capture-h10.py requires exact
Root intent/prerequisite, selected APK/UID/root, two cold observations0/30s and
one complete original64MiB-bounded raw TAR. It writes the capture report before
normal SDK closure and does not call the initial registry semantic decoder.
Forensic closure validates original command/capture refs and no-actor monitor
closure only. It makes NO registry pending0/private-conservation/SDK qualification/
G1/flight assertion. Root and QA must independently inspect the fresh current raw
and genuine SDK closure before authorizing any evolved-state continuation.
Capture bytes/report remain if a later check/closure fails; failures are not
converted into a successful diagnostic exception.

Root entry m801:
- root-capture-h10.py --candidate C --candidate-sha D --spec S --intent I
  --intent-sha ID --prerequisite P --prerequisite-sha PD --slot m801
- Intent format aeris-h10-root-forensic-intent, status
  ROOT_SOURCE_QUALIFIED_READONLY_FORENSIC_CAPTURE_NOT_QUALIFICATION; binds C/S/
  entry SHA, slot m801, run beta-rc01-forensic-capture01 and prerequisite SHA.
- Prerequisite format aeris-h10-root-forensic-prerequisite version1, status
  ROOT_COLD_VERIFIED_G105_FAILED_PHYSICALLY_CLOSED_NOT_QUALIFICATION; binds current
  candidate, selectedAPKSHA256, priorSlot g105, actual priorKernelBootUUID,
  baseAPK as parsed codePath directory, authorityRestorable:false and4–8 exact
  original evidence refs. This is metadata admission, never actual acceptance.

Caps20/100MiB, 11 artifact pools,14 owner/future60686336B, progress4KiB/16 commands,
writer64KiB/200ms, HostHealth100ms, freshness250ms, native/export/disk/power guards
remain. H7/H8/H9 runtime source SHA/size/mode/inode/device are preserved; old H6
restoration incident remains disclosed. No APK build/signature or SDK/AP/Android
runtime actor was launched by Builder. Mock Node children/owned Unix writer
threads were created and closed with task-local fixtures automatically removed.
