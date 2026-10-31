# CONTROL06 · Consistent toolbar and action controls

User request: fix unbalanced/misaligned map controls at the root and prevent recurrence. Release: 1.1.1, 12/10/2026. Single-agent specification, implementation and verification; no independent review claimed.

The DSM label inherited 13px bottom margin from form styling, moving its visible border 6.5px above the other controls. The zoom buttons were only 36.40625px wide, and DSM inherited an 11px font and square corners. `evidence/control06/before.json` and `before-toolbar.png` preserve the measured baseline; `user-report.jpg` preserves the supplied screenshot.

`app/controls.css` defines shared zero-margin control boxes, consistent typography/corners, centered content and checkbox, 44×44 square icons, stable content-button widths and wrapping without shrinking touch targets. The generic form label retains its own spacing. Plan/Fly, QGC, Review and native intake adopt equal-column action groups; the Plan QGC navigation link moves below the action grid. No positional compensation was added. Server allowlist and offline package include the stylesheet; static cache version/hash changed.

Acceptance and prevention: CONTROL-01–06 in the design contract are exercised by `tools/control_layout_qa.mjs`, mandatory after unit/API tests in `npm test`. Seven viewports, DPR2, Plan/Fly and three companion pages, drawing state, label click, checkbox centering, focus and offline controls pass. The two injected regressions are detected, restored geometry passes, and no POST or JavaScript errors occur. Existing map drag/command visibility and QGC import/export/offline regressions pass. Exact counts and source-byte hashes are in the receipt directory.

SOT/product/flight contracts and previous milestone receipts are preserved. No new SDK/device integration, flight test or hardware claim is needed for this CSS/layout change. HeraHub physical interaction and owner aesthetic acceptance remain pending. No dependency install, project copy, extra build folder or external scratch files were created.
