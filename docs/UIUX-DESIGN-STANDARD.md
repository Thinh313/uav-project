# RtR Field Interface · UX01 design contract

Date: 12/10/2026. Owner: user/AI Officer RtR. The user rejected M0 visual quality and requested deep source-backed UI/UX redesign. Branding instruction: **white/black primary, yellow secondary and scarce**. No supplied brand book/official yellow code; #F2CA30 is a reversible working token.

## Evidence and applicability

Primary captures/claims: `research/uiux-20261012`. NASA-STD-3001 crew interface guidance is a human-factors reference for spacecraft, not a UAV certification requirement. Apply its principles to this workbench via explicit project decisions. DJI's PFD article describes a product design, not an independent comparative UX study. W3C criteria supply measurable web accessibility requirements. Compliance with selected checks does not establish full WCAG conformity or commercial/pilot acceptance.

ISO 9241-210/110/11 public abstracts inform process and scope, not detailed clause compliance; full paid standards were not obtained. The research and operator evaluation protocol are in [UIUX-RESEARCH.md](UIUX-RESEARCH.md). Brand aesthetics are an explicit design decision; interaction standards do not certify premium appearance.

| Source | Evidence-backed principle | Project implementation / check |
|---|---|---|
| NASA crew interfaces 10.1 | Consistent layout, nomenclature, icons | One SVG icon set; stable workspace/control locations; sentence-case labels |
| NASA 10.2.1 | Indicate stale/missing/unavailable data | Text + symbol on link and telemetry; unavailable camera gets explicit empty state |
| NASA 10.2.4 | Confirm critical/destructive commands | Rehearsal mode commands retain explicit state; session reset requires confirmation to preserve/export log |
| NASA 10.4.2.1 | Present critical task data simultaneously | Plan canvas/summary/validation/action in one viewport at target desktop/tablet-landscape; Fly mode/link/telemetry/command visible together |
| NASA 10.4.2.2–3 | Color redundancy and consistent units | Every color state has words/icons; field unit suffix separate from label; GSD/spacing/interval use units |
| DJI PFD | Integrated scan of flight information | Compact telemetry strip and stable command dock; no fabricated heading/attitude/GNSS display |
| WCAG 1.4.3 | 4.5:1 normal text, 3:1 large text | Calculate selected token pairs; inspect rendered text |
| WCAG 1.4.11 | Meaningful control/state cues 3:1 | Contrast borders, selection/focus and route against adjacent surfaces |
| WCAG 2.5.5 (AAA) | Enhanced target 44×44 CSS px, with exceptions | Project minimum 44px; primary controls 48px; plotted features have equivalent previous/next buttons |
| WCAG 2.4.11 | Focus not entirely hidden by author content | Visible focus; drawers scroll focused controls into view; overlays do not cover command dock |

## Visual direction and rationale

An operating console, with instrument-like precision and a white editable inspector. Black is the surrounding workspace; the geometric plan is readable at the center, with a selected transect in yellow and the remaining route in white. Yellow is a hierarchy cue, not a panel background or a repeated decoration. No amber/brown/blue-green UI remnants. Error red is semantic and explicitly labelled; no green required for ordinary validity.

Palette: carbon #050505; stage #101012; raised #1C1C1F; paper #FFFFFF; ink #101010; secondary text #666666 on white and #B8B8BC on dark; RtR working yellow #F2CA30; error #B42318 on white / #FFB4AC on dark. Minor neutral grids are decorative, not relied on for interpretation.

Typeface: locally bundled IBM Plex Sans, using optical hierarchy and tabular numbers; offline/system fallback if loading fails. Main control/body 14–15px; supplementary 12–13px; metrics 26–32px. No sci-fi stencil text, uppercase captions everywhere, glowing borders or background animation. Small labels are evaluated on actual target screens; real daylight/gloves/device tests remain pending.

Compact supporting metadata may use 10–11px on the review prototype; critical metric labels use at least 12px. Production device legibility, physical viewing distance, daylight and glove operation are still unmeasured. The premium appearance is a design judgment, not a result guaranteed by an accessibility threshold.

Layout: 68px workspace rail; 72px global header; map-centric middle; 312px white inspector. Desktop is a viewport workspace with independent inspector scroll only for advanced camera settings. Sticky summary and primary action stay visible; no long scroll to change plan or inspect command result. At mobile widths the inspector becomes a keyboard-accessible sheet, while the plot remains in context. Touch targets do not shrink to fit.

## Functional UX improvements

- Camera details stay in a secondary disclosure; unit suffixes do not collide with labels.
- Save/open/import/export move into a deliberate mission file menu instead of four equally prominent boxes.
- Plan validation has a stable slot; dirty/invalid/valid state and next action are clear.
- Actual route selection, zoom/reset, previous/next transect and coverage footprint review; all geometry comes from the existing engine. View manipulation never changes mission settings.
- Keyboard zoom/fit and transect navigation; changing viewport state cannot issue a vehicle command.
- Fly centers actual rehearsal telemetry and state reconciliation; synthetic horizon drawing removed because attitude is unavailable.
- Rehearsal test controls go into a separate drawer; operational-looking commands remain stable, explicit and within the existing simulation boundary.
- New session dialog permits log export and cancel; no unexpected loss of event evidence.

## Acceptance criteria

UX-01: brand token compliance and selected initial-view yellow pixel budget ≤5% (project visual budget, not an external standard). UX-02: Plan/Fly critical information/action visible without page scrolling at 1440×900, 1024×768 and the actual 1280×720 browser viewport; basic inputs must not be clipped by the inspector footer. UX-03: control targets, declared token contrasts, focus and keyboard operations pass selected checks. UX-04: route/coverage/zoom interactions reflect actual planned geometry. UX-05: file operations, stale states and command lifecycle regressions pass. UX-06: mobile sheet/keyboard focus/reset workflow work at 390×844. UX-07: source hashes/claims and honest applicability preserved. UX-08: render critique/screenshots, test receipts and explicit user-review status in completion report.

Aesthetic acceptance is **pending user review**. Operator efficiency/safety/superiority require real tasks and operators; no headless test may declare those results.

Controller target update: the user specifies installation on Hera. [HERA-CONTROLLER-BASELINE.md](HERA-CONTROLLER-BASELINE.md) supplies the HeraHub model candidate, Android/density/input requirements and device gates. UX01's CSS-pixel checks remain browser evidence; the Android target uses a proposed 48dp touch floor and requires actual density/insets/hardware validation.

## CONTROL06 · Shared control geometry gate (12/10/2026)

The reported map-toolbar defect came from the generic form `label` margin-bottom of 13px. Flex centered the margin box, moving the DSM border up by 6.5px. Intrinsic zoom widths also fell to 36.40625px; the checkbox label inherited a different font and corner radius. Baseline geometry and screenshots are retained in `evidence/control06`.

Active Plan/Fly, QGC, Review and native-intake pages load `app/controls.css` after their page stylesheet. Toolbar controls use `control-toolbar` / `toolbar-control`; action rows use `control-group`. Keep form spacing in form selectors; toolbar controls explicitly own margin, font, border geometry and alignment. Do not compensate with translate, relative top, negative margins or per-label pixel offsets. Icon controls are 44×44 CSS px; text controls keep stable widths appropriate to their content. Narrow toolbars wrap with intact touch targets. Action groups use equal grid columns and stretch within each row; multiline labels can increase the entire row's height.

CONTROL-01: same toolbar row has matching top/bottom edges within 0.5 CSS px, 44px height, zero external margins and consistent corners. CONTROL-02: icons are square and all grouped controls have targets at least 44×44 CSS px. CONTROL-03: controls and text fit inside their group at 1440, 1280, 1024, 800, 640, 390 and 320 CSS-pixel viewports; geometry is checked at device pixel ratio 2. The 640 viewport also exercises the reflow width corresponding to a 1280-wide display at 200% zoom; it is not a native-browser zoom measurement. CONTROL-04: drawing label changes preserve the button box; DSM label click, checkbox centering and keyboard focus work. CONTROL-05: shared styles remain available offline. CONTROL-06: all current `.row`, `.actions`, `.map-tools` and `.commands` groups must declare the shared geometry class; new unclassified groups fail the gate.

`npm test` now runs unit/API tests followed by `npm run test:controls`. The browser gate starts its own static loopback server with SITL disabled, records measurements/screenshots and checks that no POST was sent. It must fail when geometry fails or the browser cannot run. Use `AERIS_PLAYWRIGHT_MODULE` to select an installed Playwright module on another host; do not silently skip this gate. `AERIS_EVIDENCE_DIR` selects a fresh receipt directory. Adversarial probes reintroduce the original margin and undersized icon to verify detection, then restore styles. Browser geometry is not physical HeraHub touch/legibility or operator acceptance.
