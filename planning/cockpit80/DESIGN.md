# COCKPIT80 — design concept, before native implementation

User brief16/10/2026: high-end, spacious, modern RtR touch + physical-stick/button controller UX. Current native79 engineering shell is not the product visual baseline. Reference images inform calm hierarchy and image-first composition, not their branding/layout or operational validity. No native/app/candidate/ENDURE change; no build, signing, SITL or external publication. Single-agent design/build/critique; no independent review.

## Visual direction

Color tokens: black #080909, panel #151718, white #f7f8f7, secondary #b9bfbc, RtR yellow #edc83c, conditional warning #e36f52. Yellow is reserved for active selection, mission geometry and one primary action; natural scene colors are image content, not UI branding. Green only conveys conditional mock status, never brand decoration.

Type: existing local Barlow Medium/Semibold/Bold, Vietnamese support checked in browser. Stable tabular numerals; 30–34px telemetry, 16–18px controls, secondary text13–14px. No thin-weight body, no technical console labels in normal workflows.

Layout: 64px top +84px telemetry, 72px left navigation, camera/map fills the remaining stage. At1280×800, scene stage occupies about77% of the screen before temporary overlays. Left aligned task panes are opened on demand; no permanent dashboard/card column. Safety-critical link/battery/flight mode stay visible even in clean view.

```
┌ RtR / AERIS   Aircraft + flight mode          link / GNSS / battery ┐
│nav│                                                            │
│   │    Camera / illustrative map                      payload   │
│   │                                                   shutter   │
│   │    small map ↔ camera                         zoom / angle   │
│   │                                                            │
├───┴ height / Home │ speed │ Home distance │ time   Pause / RTH ──┤
```

## Input model: proposed, not confirmed Hera firmware mapping

- Touch: ≥56px primary targets, no hover-only action, sheets scroll internally with persistent actions. Camera/map swap by one tap. Shared pointerdown/up handling for hold-to-confirm, with keyboard equivalent.
- Physical sticks: remain flight inputs when menus are open; never silently repurposed to navigation. Mock only displays stick channels in the input preview. No hardware capture or flight output.
- Proposed dedicated navigation input/D-pad: arrows move UI focus, Enter selects, Escape returns. This is a keyboard preview; actual Hera controls/MCU mapping remain unknown until confirmed.
- Proposed C1 toggles map/camera, C2 opens mission information. Dedicated pause remains a direct action; return-to-home requires explicit intent/confirmation. F1/F2/Space/R are desktop equivalents only.
- Pilot/payload roles are a local visual scenario. Payload role does not expose flight actions. No real authority/session grant is minted.

## Mock coverage

Fly: photo-first camera, switchable illustrative map, payload picker, mock shutter, zoom, telemetry and explicit return confirmation. Mission: corridor/survey preview and editing knobs. Preflight: meaningful checklist and Home/datum confirmations. Review: sample-image contact sheet and timeline, never physical-media evidence. Input/scenario sheet: touch/keyboard proposal, link loss, video loss and low battery. Link loss removes live-looking values and blocks mock commands; no command queue or retry.

Generated background is an illustrative image, not live video, real map, calibrated terrain, actual inspection or flight evidence. The scene is not georeferenced. Product content stays concise; concept provenance is persistently marked. No production claims or automatic promotion of design to accepted native UI.

## Acceptance before presentation

Verify four views at1280×800 and1024×600, high/low chrome contrast, target sizing/alignment, camera/map/payload switching, modal keyboard/focus behavior, mock-role restrictions, lost-link/video states and no external requests/flight routes. Capture screenshots, critique and iterate. Hardware ergonomics, gloves/sunlight, native renderer, joystick latency and operational safety remain NOT_CHECKED. Show the mock for user design review before native implementation.
