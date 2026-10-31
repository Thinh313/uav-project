# FIELD02 runtime repair decision, 22/10/2026

Contractor L2 decision within the user's authorized simulator-only milestone. No hardware, production, frozen-source or ENDURE action is added.

Actual Android13/WebView101 exposed unsupported AbortSignal.timeout, H264 encoder unsupported (VP8 explicitly selected), an inaccessible configuration sheet and reset starvation in the VP8 viewer. These observations are retained; desktop performance is not applied to Android. Repairs affect only FIELD02 browser modules, and each new diagnosis requires source+test evidence before a new live attempt.

First actual SITL run s9ec98cd74dde403a9d5a uploaded/readback and armed. AUTO was refused; the run was explicitly aborted from UI and remains accepted:false. Initial UI inspection suggested Home expiry, but independent raw review corrected that hypothesis: AUTO intent arrived9,367ms after the Home proof (still within10seconds), while AUTO_OPTIONS/CAM1_TYPE/WP_SPD were11,785–11,960ms old and failed their10second freshness guard. This is a real incomplete scenario, not an accepted nominal flight. No Home window or preflight freshness floor is extended. Preserve this correction instead of calling the initial hypothesis a proven cause.

The next harness will use actual ADB taps plus read-only state and screenshot/OCR observations, so it can inspect the bound post-arm Home and reach the visible AUTO button within10seconds. It will not invoke a flight API directly, inject DOM controls or retry uncertain commands. Home lat/lon/MSL and exact plan/run identities must match the declared simulator fixture before confirmation.

Budget disposition: allow at most5 total FIELD02 SITL attempts instead of4, including the retained aborted first run. Four slots remain for polygon, corridor, C2 cut and AP process reboot. This is one finite extra attempt for the newly observed Android UI/harness failure, not an automatic retry allowance. Every failed/aborted attempt consumes a slot; each remains≤600seconds, disk admission≥29GiB/31samples, runtime guard21GiB and floor20GiB. No further increase without re-evaluation. Native APK build budget remains2/2 consumed.

Flight budget code may change only while no FIELD02 run is active, with fresh source pins and previous manifests retained. No old manifest or review is rewritten. The first raw verifier also reports OWNED_STARTUP_PREFIX_BOUND; that failure requires independent byte diagnosis and cannot be waived merely to obtain PASS.
