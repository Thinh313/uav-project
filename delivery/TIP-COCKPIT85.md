# TIP COCKPIT85 — UI alignment and visual QA

Scope: isolated UI overlay derived from NATIVE84. Do not alter accepted modules, source/candidate, canonical SOT or ENDURE. No flight commands, APK, production signature or dependency install in this task. Single agent switches specification/build/verification roles; no independent-review claim.

Design: RtR white/black/yellow accent, Barlow 500/600/700, transmitted glass, no solid button tiles. One 24px horizontal gutter (20px on compact screen) for logo and footer first metric. Shared 8px rhythm, 48px minimum touch actions, bounded panels, scroll only content, visible focus, reduced-motion and day/night inks.

REQ85-01: logo and first footer metric left edges differ by <=1 CSS px at 1280x800, 1366x768, 1920x1080 and compact 1024x600.
REQ85-02: left/right floating islands share Y centre, no header/footer intersection; no panel/action bar unwanted overlap, clipped titles or unreachable actions in four main views.
REQ85-03: every reachable contextual sheet, return confirmation, workspace and SITL tab reviewed in day/night; long text wraps, labels and controls align, content scrolls within visible bounds.
REQ85-04: theme glyph swaps, touch/focus states, enabled/disabled treatment and reduced motion checked. Retain all source/freshness/history disclaimers and existing safety gates.
REQ85-05: browser QA and repeatable geometry guards fail when gutter/overflow is intentionally broken, runtime safety regressions pass; frozen byte union matches before/after.

Browser coverage includes mock native journey and disconnected real-source presentation. Physical HeraHub, Android OS SAF/IME, real telemetry/flight and GPU performance not inferred from browser. Existing native84 remains latest accepted APK. Native85 APK is outside this UI request; browser verified assets may be proposed for next native build.

Decisions: user authorizes fixes; no extra design approval gate. No APK build because visual review is first and accepted APK stays immutable. Native shell assets are reused, not a disconnected redesign. Store test-only host journal in .local/cockpit85. No automatic cleanup of evidence.
