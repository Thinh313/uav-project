# Safety revocation must work after foreground is lost

Actual window1 background closure safely closed the transport and authorities,
but recorded `CREW_INVALIDATION_FAILED`. Source inspection found invalidation
calling `payloadCore()`, whose foreground requirement correctly protects normal
commands but also rejected safety teardown after onPause. The original
NATIVE_BACKGROUND cause never reached the expected per-session revoke receipt.
Do not treat this generic closure as proof of the specific missing audit event.

Authorize only a package-private, safety-only native station revocation path
which can remove authority after foreground loss. It cannot claim, grant,
connect, retry or write actuator commands. Existing foreground checks for normal
payload access, all last-writer checks and flight gates stay intact. Record
the actual successful revoke and original cause before pilot common-close. If
revocation itself fails, retain an explicit failure cause and close safely;
never record a failed revoke as success or append to already sealed raw.

Preserve old Java bytes, independently test foregroundfalse cleanup/zero wire and
unchanged normal foreground denial, then recheck actual airborne A loss while
B continues its own heartbeat. Consolidate before final development APK03.
