# GEO14 · geographical/Home/datum and survey quality review

Version 1.9.0. User-authorized host engineering increment, no SDK/HeraHub. Single-agent Contractor → Builder → Verify, no independent audit. Legacy source/record/wire versions remain readable. New reviewed survey-run v2 explicitly binds a versioned policy; only simulator mapping is supported.

| REQ | Required acceptance evidence |
|---|---|
| G14-01 | Primary protocol/datum/DSM claims captured, scoped, hashed and processed with Refinery; user intent only enters SOT |
| G14-02 | Explicit WGS84/EGM2008/ellipsoid/MSL/relative-Home distinctions; conversions require matching declared geoid context; unknown operational launch/datum blocked |
| G14-03 | Pinned asset coverage and no-data checks; conservative continuous grid-cell route clearance bound, not only sparse point sampling |
| G14-04 | Versioned operator engineering policy for predicted GSD/overlap/clearance and separate measured quality criteria; no camera commands/synthetic metrics promoted to physical quality |
| G14-05 | New v2 survey requires explicit source/policy/Home review before upload/ARM/AUTO; fresh Home guard also protects legacy AUTO; HOLD/RTL remain available |
| G14-06 | Geo snapshot binds source/compiler/policy/session/vehicle/Home and is validated in immutable execution record and portable handoff |
| G14-07 | UI supports draft/record comparison and separate evidence-linked declared quality report; stale/offline changes invalidate approval, shared control geometry |
| G14-08 | Corpus includes broader ACCEPT13, v2 flat/DSM-offset and negative datum/Home/no-data/policy/quality/evidence cases; actual SITL flights, wire refusal and restart |
| G14-09 | Legacy preservation, recipient handoff/re-import and existing safety/storage guards pass; protected evidence and scratch hygiene |

Thresholds are an AERIS engineering test policy, not RtR aircraft defaults, client requirements or an industry certification. Planned DSM envelope is conservative for linear horizontal/altitude segments on the retained bilinear grid; excludes takeoff/landing descent, true trajectory dynamics, current obstacles, DSM uncertainty and operational flight clearance. DSM EGM2008 differences map into flat simulator Home only. No actual geoid grid, calibrated camera, capture provenance, achieved coverage or surveyed checkpoints exist; field quality remains NOT_CHECKED even if declared metrics meet thresholds. Local unsigned quality assessments may bind declarations to actual verified file hashes, but cannot authenticate a sender or physical observation.
