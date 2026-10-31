# Glass01 — requested material and alignment revision

16/10/2026. The user rejected detached opaque camera tiles and requested a premium blur-glass interface across bars and controls. This changes the design mock only.

- One camera dock owns the clean-view action, payload, shutter, zoom, settings and gimbal readout. One width, padding, vertical rhythm and center axis. Standard targets56×56; shutter64×64 at1280,56×56 in compact600px-height layout. No per-button black backgrounds.
- A shared glass material uses28px backdrop blur, subtle saturation, translucent tint, thin highlights and a single edge/shadow system. Header alpha.54, nav.28, telemetry.50, camera dock.42. Buttons remain transparent inside the dock. Main actions use a translucent yellow tint and border.
- Camera/map now extend behind the chrome so blur samples the actual scene, rather than an opaque black body. Heading and reticle share one scene axis. Dock and bottom action bar share the same right edge.
- Contextual task/review panes, menus and confirmation dialog use the same glass vocabulary. In compact layouts the dock remains above telemetry; clean view retains its own restore button plus critical flight status/actions. Three preflight confirmations and their note remain above the fixed pane footer at1280×800.

`glass.css` owns the material and geometry tokens. `index.html` groups the controls; `cockpit.mjs` is byte-identical to the prior mock. The preview server was restarted only to expose the new stylesheet route; it still serves read-only assets on8840 and has no flight API.

Validation: actual CUA in-app browser, readonly DOM geometry plus real clicks at1280×800 and1024×600; default viewport restored afterward. Center alignment,56px targets, heading/reticle axis, dock/footer clearance, glass RGBA/blur and pane content were measured. Screenshots and JSON are in `evidence/cockpit80/glass01/`. The previous73 functional checks remain prior-revision evidence; they are not relabeled as a fresh full glass regression. Native/HID/GPU-performance/glove/outdoor acceptance remains NOT_CHECKED. No APK, signing, SITL, SDK, frozen app or ENDURE change.
