# CONTROL02 synthetic AP altitude datum contract

Root approved before new actual launch, 27 October 2026. This is an oracle
contract for the declared provisional external-physics AP03 profile only.
It does not state physical Hera altitude accuracy.

Every armed GLOBAL_POSITION_INT is checked against the same explicit native
post-ARM-confirmed CRC HOME_POSITION reference. Require:
`abs(altAMSLmm - confirmedHome.altMSLmm - relativeMm) <= 20`.

ArduPilot cached 4.7.1 GCS_Common.cpp lines6115–6124 builds global AMSL from
integer centimetres times10, and relative altitude from float metres times1000.
The20mm contract accounts for the distinct quantization paths. Domain/type,
freshness, Home mutation and datum labels are checked independently. It does
not change the horizontal10m or relative altitude5m flight limits or firmware
parameters. Existing native preflight1m tolerance remains a separate mechanism.
The cold oracle is stricter for this synthetic profile.

Boundary tests20mm PASS and21mm FAIL are required, including incorrect MSL,
relative altitude and latest Home changes. No tolerance adjustment after actual
observation is allowed in this tranche. All earlier source/receipts stay sealed.
