# Actual QGC desktop corpus · v5.1.5

Seven .plan files are unmodified actual QGC5.1.5 UI Save As outputs. provenance.json binds output hash, initial source hash (where applicable), observed edit sequence and runtime receipt. The AERIS-seeded Survey polygon and generated-by-QGC route are explicitly distinguished. qgc-created-simple is a fresh editor route after Clear/No Template. Physical endpoint was never connected.

Original AERIS exports are in the parent fixture directory. Simple roundtrip changes Home10→7 and camera stop immediate flags0→1. Cached Survey roundtrip regenerates coordinates and trigger spacing, preserving polygon. Neither pair is semantically equivalent; the test suite expects the differences to be detected. The second QGC save of its own SimpleItems output is stable. All raw corpus plans are blocked by the fixed SITL Home contract; geofence and AMSL are additionally blocked in isolated negative tests. No source file is silently relocated or altered for flight.
