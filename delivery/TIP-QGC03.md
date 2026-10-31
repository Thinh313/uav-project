# TIP-QGC03 · camera export and Home/height review

Owner 2026-10-12 authorizes this increment based on actual QGC corpus, desktop open/save and SITL, without SDK/HeraHub. Existing owner permission for QGC-only AppleScript/System Events/JXA/CGEvent persists. Contractor→Builder→Verify in one agent; no independent review or external release.

Decision: keep immutable source and existing raw export; add an explicit derived SimpleItems camera-section export. Pinned QGC stop action requires a zero-distance/no-immediate 206 followed by IMAGE_STOP_CAPTURE2001. A derived plan may suppress existing stop-time immediate shots only with explicit choice visible in the diff. Never reinterpret that shot as equivalent. Reserved nulls for2001 may map to zero only under the bounded Copter profile with recorded normalization.

AC01 retain source-byte provenance; freeze primary camera/mission sources and official desktop runtime. No comparator code copied into product.
AC02 explicit camera-section export inserts supported stop-pair commands, preserves navigation/speed/start flags, fails rather than changes unsupported camera intent; sequence/count/lineage reflects insertions.
AC03 Home/altitude derivation presents source versus fixed SITL Home AMSL and two explicit vertical choices: preserve relative height or preserve implied AMSL. No lateral relocation, mixed AMSL/terrain conversion, fence/rally omission or complex regeneration. Flatten cached Survey only with explicit snapshot acknowledgement.
AC04 UI previews hash-bound derived changes, requires explicit adoption, resets consent and leaves original separately downloadable; source changes/reload clear proposal/approvals. All actions remain command-free until existing upload/preflight gates.
AC05 expose observed fresh autopilot Home/AMSL and tighten loopback preflight to bounded horizontal/vertical differences; stale/unknown Home blocks upload/arm.
AC06 actual QGC opens/saves camera-pair exports and reopened file; inspect camera, Home and navigation differences. If terrain auto-update changes Home, capture it and use explicit Home review, not a loose equivalence comparator.
AC07 fly accepted derived mission in actual SITL with full readback, camera stop commands/progress/land/disarm; rejects mutated camera/reserved values and altitude/datum/fence cases. Hardware camera images NOT_CHECKED.
AC08 unit/API/browser/offline/corpus receipts, source manifest, SOT owner-intent addition and applicable gates, Completion and cleanup. Keep QGC01/02 evidence immutable.

No physical aircraft, SDK, native device changes, PARAM_SET, force-arm, autonomous AI authority or security configuration changes. Current mounted QGC preferences are preserved. Disk checked before download; downloaded runtime removed after testing.
