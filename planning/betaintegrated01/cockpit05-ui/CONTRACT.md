# COCKPIT05 visual mock: flat selection rows

Scope: isolated HTML/CSS/JS preview only. All cockpit04 APK/source/input pins, candidate, ENDURE and historical receipts remain immutable. No APK, native, SITL, emulator, network or signing.

Design plan: keep the existing glass cockpit, reference-map geometry and Barlow Vietnamese fonts. Retain warm white #f6f7f5, day ink #172620, neutral muted #c4ceca, glass #101715 with alpha, and restrained gold #e2be54. Review titles and metadata share one left edge; a small trailing check identifies selection, plus aria-current. Flat rows use2px corners, dividers and>=48px touch height. Notices use a neutral information icon beside text. Navigation uses a short straight centered underline and icon background instead of a leading curved stripe.

Critique against the brief: a new rounded card or replacement leading accent would repeat the rejected treatment. Therefore no extra wrappers around each record and no decorative gold left border/inset shadow. Functional map arcs, radio/battery symbols, panel glass and keyboard focus remain.

Allowed changes: presentation CSS, review-row trailing icon/accessible name, notice wrapper markup. Request/review-cache/authority/telemetry model logic stays unchanged. Preview model data is explicitly synthetic, memory-only and never a real bridge or transport. mock.html offers survey/preflight/Fly/review/theme inspection, without flight controls or real camera/telemetry.

Verification: reuse scoped deterministic DOM/native-bridge doubles after changing only the asset path; add structural/style checks for all three rejected leading-stripe patterns and the trailing selection cue. These checks do not certify rendered pixels or flight behavior. Root owns independent/browser review if available.
