# FIELD01 position context repair

The independent flight Builder identified a P1 lookup risk: position history can
contain multiple runs, so a temporally near position is not necessarily from the
current capture's run/session. Root explicitly authorized a targeted gateway edit
after its previous freeze. This agent made no frozen flight/source module changes.

Gateway finish now requires the returned position's run, boot, model SHA and plan
SHA to equal the current capture and committed workspace. When current flight
request.session is present, the returned position session must also match. A
mismatch retains the original JPEG with position null and explicit timing reason
`POSITION_CONTEXT_MISMATCH`. It never writes old coordinates under current context.

Updated synthetic lookup fixtures carry full exact identities. Five individual
run/boot/model/plan/session adversarial cases and a rapid reconnect case verify
that fresh current telemetry plus fresh prior-run position history cannot bypass
the gate. Existing nominal capture, authority, stale-source and async tests remain
checked. Final gateway checks: **17 pass, 0 fail**, retained at
`evidence/field01/evidence-gateway-tests-2026-10-21T12-47-06-816Z/results.json`.

No new SITL or physical capture was performed. The accepted retained SITL dataset
already matches its exact raw run/boot/model/plan and remains unchanged. This
repair and its new tests share an author; they are Builder self-checks following
an independently identified issue, not independent review of the repair.
