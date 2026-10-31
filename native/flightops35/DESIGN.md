# Native35 design decisions

Apply frontend-design skill and reviewed GCS34 cockpit direction. Operator task is editable survey + auditable mock preflight/Fly, not a brochure or AI chat dashboard. Four workflow stages share one mission. Map is the visual anchor; editable panel and video occupy distinct areas; no disconnected copies of state.

Tokens: canvas #000000, map #15181c, panel #20252b, primary ink #ffffff, secondary #c7ced6, selection/route #efcd36. Risk red/amber used with text only for conflicts/unknowns. IBM Plex Sans bundled exact from existing app;14px base,26px mission title, tabular instrument values. White/black dominate; yellow is secondary.

Layout desktop: fixed header / stable instruments / four stage tabs / map+video alongside scrollable context panel / stable Hold–RTL–Takeover bar / storage/status. All horizontal controls use shared52px minimum height and flex alignment, never checkbox label baseline alignment. Nav is workflow sequence, not decorative numbering. Desktop1280×800 keeps critical bar visible; small screens stack secondary panels with no horizontal overflow.52CSSpx is a host layout check, not native48dp acceptance.

Critique against brief: reuse industrial black/white requested branding instead of a generic bright accent dashboard. Remove marketing counters/cards/AI chat; observed mode and owner remain prominent. Source scope and absence of real media remain explicit. Alert stack is bounded; details scroll inside panel, not over critical bar. Native touch/glove/readability/input and actual video remain operator/device gates.
