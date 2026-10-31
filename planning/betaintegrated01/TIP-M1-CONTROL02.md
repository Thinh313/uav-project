# M1-CONTROL02: geography oracle qualification and nominal pilot release/LAND

User27/10/2026 authorizes geography oracle repair, mock first then native Android–SITL
UP → observedBRAKE17 → fresh consent → explicitLAND9; exact frames, immutable
previous source/candidate/ENDURE, entry20GiB/livefloor10GiB+256MiB, no production sign.
Apply personal Vibecode6.3. Explicitly delegate Builder oracle, Builder native
review/repair if needed, and independent QA. Root Contractor only owns actual
Android/AP/service launch, test fixtures, baseline verification and report.

## Isolation and budgets
All CONTROL01 source/profile/APK/raw/receipts/seal4251files now immutable, in
addition to previousM0/M1/ENDURE/canonicalSOT. Never change old receipts to PASS.
New product code only pilot/betaintegrated01/control04/ (oracle), and only if
an evidenced native bug demands it native/betaintegrated01/control03/ versioned
substitutions. Reuse APK02, hostcontrol03, AP03+model/pacer+nominal39 profile exact
bytes initially. No SDK/dependency/AP install/rebuild, project/tmp copies, firmware
parameter changes, guard weakening, raw sampling, hidden speedup or frame drops.
New plan/tests planning/betaintegrated01/m1control02/, evidence/betaintegrated01-m1control02/.

Window<=3h, <=3 repair/check cycles per failurefamily. New unit<=128MiB/2000files,
newruntime<=4GiB/9000files, <=3host/APstarts +1emulatorstart (max4total). Initial
nominal90s, may use a separate bounded60/90s repair only within budget. No blind
flight retry/reconnect, automated grant or restart. No30min or physicalaircraft.
Root refuses ARM if <30s left in declaredcapture, maintains finite simulator abort,
observes ground/disarm if possible, then managedclosure. Everyattempt retained.
Build only if necessary, cachedtools, free>=20GiB, <=128MiB own build scratch,
existing developmentkey only; preserve previousAPKs. No production signature.

## Geography contract declared BEFORE new actual
Purpose is a qualified window/reference repair, not relaxation of the10m/5m
limits. Versioned oracle must use CRC-checked AP Home and bind native explicit
postARM confirmation where claiming confirmedHome. Keep startup0,0 observations
in raw and classify PRE_AUTHORITY, never use them as flight origin. A coordinate
0,0 is not globally invalid: a legitimate Home at0,0 plus qualified/fresh GPS/EKF
must remain supportable. Missing/unknown/nonfinite/out-of-domain/geographic jump
in the armed window fails; no outlier deletion or stale good facts overriding
newer contradictions. Geography reference is stable explicitpostARMconfirmedHome;
window from first actualARMED observation through observedterminaldisarm, fresh
APposition/GPS/EKF/Home/context, not a chosen safe subwindow. After-window new
arming requires a new case/confirmation, not ignored. Unknown boot/frame/context,
changed confirmedHome/missingconfirmation or datum mismatch failclosed.

Geodeticdistance must handle longitude wrap/dateline correctly and validpoles;
use an independently derived geodesic reference in tests. Unit/datum E7/mm exact.
Retain rawpositions even when unqualified before flight. Ground-only recovery
has no consent and must not be forced to have a postARMconfirmation; no flight
PASS inferred from its telemetry. Replay old loss05 under NEW oracle for regression,
without rewriting its original CONTROL_NOT_READY or historicalaggregate.

Mock matrix at least: startup0,0→validHome; legitimate0,0; missingGPS/Home/confirm;
Home changes afterconfirm; armed0,0 jump fromotherHome; dateline/highlatitude;
E7/mm/type/domain/nonfinite/missingvalues; stale/reordered/foreign/bootreset;
nooutlierdrop; takeoff/ground/latestcontradiction; oldloss andground regressions.
Nativeinput/authority integrity remains independent of geo oracle.

## Nominal actual sequence and requirements
Fresh39typedpreflight (observe up to60s within90scapture), explicit neutralconsent,
GUIDED4 observed, nonforcedARM observed, shownpostARMHome confirmation, takeoff3m,
hover3m±.75 withhorizontal<=.5m/s across>=1s actualfreshpositions, LOITER5 observed.
ActualAndroid rightstickforward held>=1s, forwarddisplacement>=.3m, effectiveaxes
<=.25, horizontal<=10m fromconfirmedHome, relativealt<=5m. Use~1.5–2s gesture.
OnUP: pilotconsent revoked BEFORE safety packet; one BRAKE17 request, actualmode17
observed BEFORE neutral1500 +release(first8channels0,last10=65534); no automatic
pilotlease restoration or normalRC afterrevocation. Fresh neutral input and second
explicitconsent create a differentlease. Explicit LAND9 command sent only after
release; noGCSfailsafe/error confounder. ObserveLAND9, freshlanded1+disarmedHB+
position|relativealt|<=.4m in>=2 independentfreshgroups afterLAND, then close.
ACK/localwrite/APforcedkill never establish execution or ground.

One nativewriter only. Root uses observed fixedgeometry from freshUIXML and a
Root-reviewed initialscreen, freshfocus/state/screenshot peraction; do not claim
individualvisualreview on everyimage. Keep allinput/motion/lease/rawTX/RX/frames.
Cold independentQA must bind input→wire→APmovement/modes, newconsent timing,
no staleinputrevival, nativecommits, externalparentanchors, exactFRAME/STAGE/AP
coverage+originalmodelbyte replay. Local orchestration trust is not remoteauth;
Androidinjectedtouch is not physicalHID. Current UI is isolated diagnosticcontroller,
not premiumcockpit integration; 30min/media/hardware and fullBeta remain separate.
