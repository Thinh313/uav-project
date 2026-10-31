# Delegated FIELD01 nonflight HTTP QA

Final result: 11 pass, 0 fail. Actual app, shared compiler, Store01 and localhost
HTTP ran on owned ports 8890/8891 with a new owned workspace. No root app on
8870, prior workspace, frozen source, flight command, SITL, browser, CUA, Android,
camera or dependency installation was used.

Final retained output:
`evidence/field01/evidence-app-http-tests-2026-10-21T12-24-12-630Z/results.json`.
Executable checks: `planning/field01/app-http-tests.mjs`.

Checked outcomes:

* A deliberately occupied owned app port causes startup to reject, close its
  already-started media listener and release its own writer lock automatically.
  Observation records both `mediaStillListening: false` and
  `writerLockRetained: false`. Normal closure also releases both owned listeners
  and its writer lock.
* Wrong Origin/Host, absent/wrong CSRF, wrong content type, malformed JSON, null
  body, oversized body and unknown route reject without mutation. Oversized
  input returns HTTP 409 and the service remains responsive.
* Saving a newly authored synthetic polygon uses the committed workspace CAS.
  Compile rejects stale heads and documents different from the saved model.
  Valid compile/save binds the exact mission SHA and plan SHA. A modified plan
  with recomputed valid integrity hashes still fails compiler replay; rejected
  writes preserve the committed head.
* Repeated invalid workspace writes retain eight rejection files totaling
  108090 bytes. Item size and aggregate limits hold; oversized rejection content
  is not persisted. This is a small bounded check, not a disk stress fill.
* No connected flight means discovery/grant/capture requests reject and invoke
  the mock adapter zero times. Startup and state restore no authority.
* A clearly labeled test-only direct Store01 seed is visible through HTTP review,
  JPEG download and durable TAR handoff with exact bytes. This does not prove an
  app media capture. Directly injected corruption causes review/download/export
  quarantine; a guard failure retains pending files without a successful receipt.

The QA agent proposed robustness repairs to the root author before any app edit.
Root implemented startup cleanup, bounded rejection retention and the generic
object-only body gate. The QA agent made no app.mjs changes. Its earlier gateway
fix remains the announced reserved journal kind rename.

Retained earlier attempts, without hiding failures:

| Attempt | Outcome | Interpretation |
|---|---|---|
| `evidence-app-http-tests-2026-10-21T12-23-18-995Z` | 1 pass, 2 fail | Sandbox blocked localhost bind with EPERM; not app behavior. Own cleanup completed. |
| `evidence-app-http-tests-2026-10-21T12-23-27-946Z` | 7 pass, 3 fail | Two QA assumptions repaired: fetch rewrote the Host header, and compiled items use param1 rather than params. Real null-body join acceptance was fixed by root. |
| `evidence-app-http-tests-2026-10-21T12-24-12-630Z` | 11 pass, 0 fail | Final bounded check after targeted repairs. |

Localhost bind required the existing tool escalation path because the ordinary
sandbox returned EPERM. The actual run used only owned test ports and explicitly
closed every app/store it created. No existing live app or stale crash lock was
deleted. Test-created evidence is retained; no outside scratch directory or
dependency install required cleanup.

The root app and this QA have different authors, but this agent implemented
Store01, so storage review is not independent. There is no independent human
review or physical field claim. `actualImages` remains zero. This result covers
the nonflight HTTP surface and fixture storage flow; it does not establish
browser journey, live media capture, SITL or Android acceptance.
