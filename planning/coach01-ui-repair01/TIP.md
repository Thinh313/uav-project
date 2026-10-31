# COACH01 UI repair01: code review and mocked UI logic

25/10/2026. Authorized scope: code inspection and mock tests while browser access remains blocked. Same assistant switches Contractor/Builder/Verify; not independent human QA. No real browser, screenshots, APK, SITL, emulator, signatures, SDK, aircraft link or production deployment.

Outcome: fix UI defects reproducible from actual app source in a Node VM with a minimal DOM/canvas/fetch/RAF/storage test double. This harness is not a rendering engine or user/computer automation. Preserve actual observed differences as red→green, without claiming browser E2E or pixel acceptance.

Mutable existing files: pilot/coach01/app.mjs,index.html,style.css,server.mjs (asset map only). Before bytes of these four archived exactly. New replay helpers and mock harness allowed. core.mjs/store.mjs, rule policyV2, old source/candidate/ENDURE/canonical SOT and prior reports remain unchanged. No rewriting old completion/receipt/handoff.

AC1 Bootstrap and server restart: no POST with undefined/stale CSRF. Read-only bootstrap before each explicit mutation; bounded errors; no automatic retry of POST. Ready/error/busy recoverable states and visible errors.
AC2 Replay state: switching report resets at, slider and marker together; pause/replay/seek/end/background deterministic; no stale RAF, input or hidden-tab progression. Exact gap/unknown-heading state, no false fresh data from tolerance or filtered interpolation.
AC3 Async handling: disabled conflicting controls while load/export; file input cleared even after rejection so same file retry works; stale image callbacks don't alter newer report; successful report remains usable if history refresh alone fails.
AC4 Export: explicit validated fetch→Blob download, never navigating app to a JSON error page; digest/context verified before publication; cleanup Blob URL. Failure preserves current report/position/history and permits explicit retry.
AC5 Render algorithm: canvas resized only on size/DPR change, transforms reset without cumulative scaling; timeline supports negative relative-Home height; fit math handles bounded small viewport without hard minimum scale causing clipping. Tests cover math, not real element geometry.
AC6 Theme/preferences/accessibility: sun/moon/action labels match; safe storage fallback; restore theme and a known saved report only through verified server GET, no authority restoration; selected controls/focus visible in light palette by token math, no visual certification. Keep glass/Barlow/RtR branding.
AC7 Verify scoped mock scenarios, source/datum/authority labels, import/export API asset routes and unchanged report recomputation; preserve baseline existing gaps. Gates20/10GiB+256MiB, own repair evidence <=64MiB, no installs/whole-project copies or user/evidence deletion.

Stop at hard resource floor or actual need for visual observation. Full browser/touch/file chooser/download persistence, contrast compositing, FPS and pixel geometry remain NOT_CHECKED. Do not use other automation to bypass disabled browser. Record backend baseline vs simulated UI vs actual UI separately.
