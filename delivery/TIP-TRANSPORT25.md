# TRANSPORT25 · Mock transport and multi-payload routing

Owner authorization13/10/2026: implement transport contract and multi-camera/gimbal routing corpus by mock/replay, isolated from frozen source/candidate; keep ENDURE20 and no SDK/HeraHub. Single-agent specification → build → verification. New `pilot/transport25`; read-only imports of pinned PROTOCOL22 codec/session. No network aircraft adapter, live/SITL writes, compiler/trust/SOT edits, signing or Fly/native integration.

| REQ | Acceptance |
|---|---|
| T25-01 | Runtime-validated immutable synthetic configuration and typed transport contract; mock adapter only, source/context/clock/byte/capacity bounds and explicit disconnect/reconnect. |
| T25-02 | Three heterogeneous camera/gimbal bindings, component/proxy/manager identities and capabilities from heartbeat/information; no route inference from labels. Selection separate from immutable request target. |
| T25-03 | Raw per-link deframing, exact-frame duplicate handling, active outbound link only, no automatic failover/resend; late/foreign generation and spoofed/unknown routes refuse. |
| T25-04 | Responder/command ACK key serialization, proxy recipient guards, accepted ACK vs observation/causality/physical media, terminal tombstone and timeout/authority/fault/uncertain-send invalidation. |
| T25-05 | Camera mission addressing projection separate from direct command addressing, reviewed draft only; broadcast0/unsupported/missing binding refused, no compiler or mission upload. |
| T25-06 | Immutable raw synthetic corpus with declared expectations: concurrent distinct routes, same-manager/same-proxy ambiguity, loss/reboot/authority/fault/fragment/dedup/reconnect and negative config/admission. Unit/corpus and prior PROTOCOL22 regressions. |
| T25-07 | Offline inspector/pinned export with explicit mock labels, tamper/offline refusal, responsive aligned controls and browser checks; no device/API/network command route. |
| T25-08 | Before/after source/slot/controller/PAYLOAD21/PROTOCOL22/NATIVE24/SOT/candidate fingerprint match; live unchanged soak/0errors. Sources/receipts/cleanup retained; no claim of device/SITL transport acceptance. |

Conservative fixture policy: one outbound command per responder/command per local generation, even after terminal success/rejection, because ACK has no transaction UUID. Reconnect is explicit and discards pending work, not a guarantee of wire freshness; authenticated transport/key/replay custody stays NOT_CHECKED. Capacity bounds and refusal are server-owned constants, not user-relaxable. A mock transport admission receipt is not vehicle acceptance. Task identity is local provenance and not encoded/authenticated on wire.
