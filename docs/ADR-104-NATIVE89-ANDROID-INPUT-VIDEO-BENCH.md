# ADR104 — SDK-free Android input/video bench companion

Accepted within continuing simulation/bench-preparation scope. Native88 flight/candidate/ENDURE and signed development02 remain immutable. Hardware is unavailable, so BH03/BH04 cannot be closed physically. A separate minimal native companion exercises public Android input/lifecycle/media surfaces before vendor integration without copying the full GCS or touching live flight.

Input has two explicit paths: pure mock calibration/control-state rehearsal with no output transport, and actual Android callback observation with unverified device mapping. Android KeyEvent.eventTime and uptimeMillis share a declared measurement basis; elapsedRealtime is recorded independently, never subtracted from eventTime. ADB injected key events only prove that Android dispatch path.

Video uses the existing synthetic fixture, asset SHA, MediaExtractor inventory and public MediaPlayer/TextureView. Frame callbacks and producer texture timestamps are not attested camera timestamps or actual display scanout. Track source identity/generation, callback staleness and lifecycle revocation; do not represent imported/decoded bytes as real captured media or derive camera latency from rendering-start alone.

Each Activity creates a new bounded, exclusive SHA-chain trace with fsync, retains all earlier logs and restores no control/player state. Independent replay checks actual raw observations, not only a UI summary. The logger can affect measured callback timing; there is no hardware latency/FPS qualification. Next physical bench still needs Native88 intake and RtR-approved budgets/topology/policies.
