# ADR080 · Separate customer payload seam and local operator authority

Phase One client model/API is unknown. Keep an honest descriptor with nulls and an explicit unsupported hardware adapter. Synthetic capability fixtures exercise a vendor-neutral semantic seam using P22/T25 generic MAVLink; no invented Phase One wire commands or compatibility claim. LiDAR is an unimplemented slot, not a fourth functioning physical payload.

Two local mock subjects share one synthetic GCS transport. A new local authority layer checks role/scope/session/epoch/generation/freshness before T25 dispatch. It is not two physical radios, authentication of unsigned MAVLink, or autopilot enforcement. Existing gimbal-manager feedback remains a separate condition; an application grant alone never overrides it. Aircraft scope can be reviewed as abstract authority but has no flight-command mapper.

Exclusive ownership transfer freezes the scope, fences old tickets and requires fresh consent by current owner and recipient. Expiry/loss/reboot/reconnect never restores previous grants. In-flight commands become uncertain on revocation; they are not undone, retried or attributed to a new owner. Losing one operator revokes that operator's grants in the mock; no real aircraft action is prescribed. Actual approved loss/emergency policies remain unknown.

Reuse T25's conservative ACK-key quarantine and P22's bounded codec/discovery/observations. The same key cannot be reused until explicit new transport generation in this engineering corpus. That is a deliberate limitation, unsuitable as final continuous camera UX. View selection remains separate from explicit command target. Raw bytes and protocol observations do not become physical images or authenticated remote proof.

Corpus replay/review integrity is content-bound, not a software signature or authorization token. Importing a reviewed transcript yields historical inspection only. Source/candidate/SOT/ENDURE and historical CYBER64/RESTORE125 receipts stay immutable. No network, SDK, actual flight transport or candidate signing is added.
