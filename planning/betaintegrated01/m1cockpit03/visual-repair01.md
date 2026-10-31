# Actual Android visual repair, before any AP run

APK01 was installed on the owned API33 emulator. Root edited the survey name,
created four reference vertices and saved revision1 with SHA
10b966e26e36ee26a613358d9cd187b209ce48d9ac41eff59cf639f1f82dde66.
Eight screenshots cover four preview panes and day/night. WebView accessibility
exposed its container, so Root used actual reviewed screen geometry for nonflight
navigation; native flight targets use measured Android bounds/readiness.

Root and independent QA inspected these actual PNGs. Stable survey/preflight/review
layouts align with the logo/telemetry gutters and floating islands. No major
stable-screen overlap was found. However:

1. Fly-night0040 is a TRANSITION, not a clean Fly acceptance screenshot: native
pads appeared before the WebView left preflight. This is a product synchronization
fault. New presentation gate keeps overlays hidden until current-view DOM render
and two animation frames acknowledge through the nonflight STATE bridge. It never
hides active Fly controls on ordinary telemetry pushes. Old epochs/views reject.
2. Default WebView blue tap highlight conflicted with the RtR active state.
3. Native pad background drew a faint rectangle outside the CSS glass circle.
4. No-source Fly showed an empty Home glass box.

Builders repaired these under new APK02 input/archive/receipt, retaining APK01 and
all first captures. Touch/input algorithm remains byte-identical outside onDraw;
Owner03/Flight02/source guard unchanged. Explicit source SHA is retained in the
review link. PureJava/DOM gate tests are not compositor evidence. Root will
recapture settled Android views and then perform the actual closed-loop flight.
