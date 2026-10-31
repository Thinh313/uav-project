# ADR047 — isolated, atomic native mock journey

Native30 separates draft and manually saved review. That cannot establish preservation of accepted mock progress after process death. NATIVE33 derives an isolated offline shell and keeps draft + current session + bounded prior-session history in one hash-bound Java workspace journal. No writes to frozen application, candidate, trust or ENDURE.

Mock transitions are serialized and committed before saved-result publication. Storage refusal or an uncertain reply leaves the UI blocked and requires explicit reload of the actual committed head. Hash checks alone are insufficient for completion: review validates a legal event sequence, current mission/form identity, exact waypoint progress and ordered landing. ACK is an observation only.

After reload, active or prepared sessions are interrupted by an appended event with a new runtime epoch. Original events remain intact. Completed/interrupted history is read-only; no input ownership, preflight or flight authority can be restored. The next flight requires a newly compiled session and explicit current confirmations. History/revision bounds refuse rather than silently delete evidence.

Android uses an offline WebView/Java persistence bridge with zero permissions and an existing development certificate. The host preview shares these assets and the actual Java journal but cannot substitute for installed Android/ART/private-storage/reboot evidence. Emulator installation remains gated at28 GiB free after prior extraction incidents; no SDK/image download is admitted below that gate. Product release and physical control remain out of scope.
