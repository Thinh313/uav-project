# Review capacity must not prevent closure or hide evidence

Actual APK02 nominal route reached ground/disarm, but its explicit review action
failed `REVIEW_TRACK_BOUND_NO_TRUNCATION`: renderer trajectory exceeded1200
points. Raw recording continued and no accepted review was created. Preserve
this run, its screenshot, raw and UNKNOWN archive as a failed review attempt,
not a C07 PASS. The native source/candidate/ENDURE outside CREW02 stay frozen.

Contractor authorizes a narrow CREW02 asset repair. Keep all original mission
completion/ground/disarm/failure gates, workspace262144-byte quota and full raw
recording. Close and durably seal native raw before constructing review. For a
trajectory over1200 points, write a bounded, explicitly identified raw-reference
geography object: points[], fullWithinBound:false, trackOverflow:true,
full pointCount, reason and exact run/head/records/bytes of sealed native raw.
Do not silently truncate, downsample, count an empty track as full coverage,
raise quota, or assert mapping quality. Existing <=1200-point body/hash stays
unchanged. Invalid/unsealed/failed/mismatched raw cannot support acceptance.

The accepted flag continues to mean qualified safe completion of this simulated
mission, under existing observed/native guards. It does not certify geography
or survey quality. UI/history must distinguish compact review from the full
trajectory retained in raw. Independent receiver checks bind reference to actual
raw and verify the complete selected-source position count, not metadata alone.

Consolidate this repair with the host setup repair before development APK03.
There remain two authorized SITL windows: pilot-loss and a fresh nominal run,
with a long enough recorded trajectory to exercise the actual reference branch.
Keep the original failed window intact and do not recalculate it as accepted.
