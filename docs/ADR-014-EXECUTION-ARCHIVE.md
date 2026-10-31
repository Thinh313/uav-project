# ADR014 · durable attempt evidence / post-flight review

Memory journals lose mission context on disconnect and can contain several sessions. Archive one attempt at upload/recovery boundaries, with source/vehicle/session/build/world identity frozen, append-only records and a content digest. Capture lifecycle boundaries before adapter reset. The recorder observes existing adapter events, has no command/parameter-write authority, and exposes failures rather than implying data saved.

Recompute outcome from bounded within-attempt evidence. A recovered observation has no historical AUTO proof. Final/landed/disarm after an interruption does not prove the entire original task. Operator annotation can acknowledge/find issues but cannot edit flight outcome/source. Preserve gaps and diagnostics.

Use a local file store plus shared deterministic review core, same-origin guarded APIs and a separate operator Review screen. Export/import is self-contained for the pinned simulator source/profile; integrity is accidental-change detection, not signed authenticity or independent verification. Open attempts recovered after server crash seal as unknown; no false resumption or completed claim. Disk budget is explicit and no automatic evidence deletion is introduced.

Design pass: keep pinned IBM Plex Sans for RtR/operator consistency. Tokens: black #080808, field #191919, white #ffffff, neutral #aaaaaa, restrained yellow #dcc146, error #ad4536. Left-aligned historical attempt list and frozen route on a black field; white evidence/review column, responsive stacked on small screens. The route encodes reached NAV vs unobserved commands, rather than decoration. Remove unrelated numbered labels and generic cards. Existing Home/datum limits remain visible beside historical identity.
