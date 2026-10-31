# ADR109 — portable planning, explicit simulator attestation

18/10/2026, accepted engineering scope. Local APK KML parser + geometry + QGC mission compiler replace network planning. Model92 unchanged. Preserve legacy format/scope/provenance strings exactly for hash interoperability; new compiler receipt records Android execution location separately.

The original Python parser and AUTO63 compiler remain frozen independent differential oracles. A bounded XML reader rejects unsupported constructs instead of resolving entities/URLs or guessing altitude semantics. Copies of geometry/QGC algorithms keep original bytes and source fingerprints; portable common hashing uses already qualified SHA primitive.

Offline mode is selected by the existing explicit launch source (mock/no host credential). It has local planning/persistence, no aircraft transport or flight authority. SITL mode does not silently fall back to offline when the host is unavailable: keep host-idle guards and journal mutation gate. Local compiled plans must be independently recompiled and compared in full before connecting to SITL; mismatch never replaces the committed plan. Import validation uses local compilation, not host availability.

Risks: corpus equivalence is bounded to tested KML subset; shared geometry is not an independent mathematical proof. Raw mission execution and hardware performance require separate gates. XML malformed cases need rejection tests and documented stricter subset. No new campaign/signature/ENDURE qualification follows from this change.
