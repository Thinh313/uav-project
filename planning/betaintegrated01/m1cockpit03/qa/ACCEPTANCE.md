# Independent acceptance: M1-COCKPIT03

This is a narrow cockpit-integration qualification. Full beta, AUTO survey, media,
physical controller and real aircraft acceptance remain separate. Root alone runs
Android/SITL. QA does not infer observed execution from compiled code, local write,
ACK, test counts or app-authored review labels.

| Boundary | Required evidence | Rejection examples |
|---|---|---|
| Source/package | Current compiled source/assets/archive SHA, accepted Owner03/Flight02 unchanged, development signature | Drift, extra legacy sender/activity, production claim |
| Trusted bridge | Exact local asset origin/CSP, five allowed message types, current epoch/increasing id, bounded queue | Raw command, flight grant, foreign/duplicate/late callback |
| Presentation | New view renders before native overlays; same Fly PUSH leaves safety controls available | Old preflight with Fly sticks, unacknowledged view actions |
| Workspace | Immutable saved revision/content hash, contiguous generations, bounded quota, pending/error visible | Silent reset, overwrite conflict, stale revision, pending treated committed |
| Approval | Saved draft SHA and context/provider/source bind immutable preflight link | Changed draft, wrong boot/operator/AP/config/source, forged saved marker |
| Native control | Actual source inputs and immutable pointer clocks, durable input/binding before intent, current lease | Regenerated/stale input, unknown target, restored consent |
| Flight proof | Full frame/model/AP raw replay plus exact native UP/revoke/BRAKE/cleanup/new lease/LAND sequence | ACK-only flight, partial raw promoted, failsafe confused with user LAND |
| Closed review | External native commit anchor, record/seal/CRC chain, exact linked draft/context, latest fresh post-LAND independent ground groups | Pre-LAND group reuse, latest armed/airborne contradiction, stale final facts, wrong target LAND |
| Review UI | Bounded selected detail with matching journal anchor, trajectory explicitly presentation-only | Empty trajectory caused by thin summary, startup points presented as flight, coverage/photo claims |
| Restart | Draft/history exact bytes survive; no connect/grants/rights automatically restored | Consent/session restored from persisted history |

Mock evidence includes actual Java algorithms with a cached Gson test-only
JSONObject adapter. This is not Android's parser or WebView. DOM/RAF doubles do
not prove compositor timing, measured FPS, touch usability or rendered graphics.
Actual Android screenshots and full raw cold audits are required separately.

Retain every failed receipt and announced source revision. A failed actual run
cannot become green through a new reader without explicitly preserving its old
classification and documenting the scope of the newer interpretation.
