# Local ADR: isolate cockpit presentation from native flight authority

Outcome: an Android operator can edit/save a reference survey, inspect real
preflight observations, fly the accepted manual/assisted SITL exercise and reopen
a linked review after restart in the approved cockpit layout.

Choose one local trusted WebView for presentation and native Android controls for
flight input/actions. Retain exact ControlOwner03, ControlFlight02, native motion
clock, authority and journal source inputs. A narrow bridge may save/load drafts
and render read-only state/reviews, but cannot issue flight commands or grant
control. No old Native98 transport or mock flight loop is booted.

This is the smallest presentation adapter around the proven native core. Reusing
an old complete cockpit would also boot mock data and historic transport writers;
rewriting the accepted control loop would create an unnecessary new safety surface.
Native pads/buttons reserve fixed map zones and retain foreground/focus revocation.

Preflight approval binds the saved survey content and live session, not a JS flag.
Review completion requires a sealed native journal and independent fresh RX ground
observations. A cached UI counter cannot prove landing. Failed or incomplete
sessions remain visible with their uncertainty; no automatic rights restoration.

The exercise is manual/assisted training attached to a survey draft. AUTO mission
upload/readback, coverage completion, real imagery, physical Hera/HeraHub, long-run
Beta acceptance and production signing are outside this scoped change.

The direct baseline is the previously accepted native diagnostic control screen.
We are testing access to the same control exercise through a usable mission
journey, not claiming improved flight performance or DJI superiority. No AI model,
agent product inference or LLM baseline is added by this deterministic adapter.

Qualification uses fresh isolated development APK, owned Android emulator and
reference ArduCopter SITL. Visual observations, static checks, mock tests and cold
raw verification are recorded separately. Immutable prior sources, evidence and
ENDURE remain protected. Entry 20 GiB/live floor 10 GiB +256 MiB and existing
15-second runtime guards are retained.
