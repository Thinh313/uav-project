# TIP-PROTOCOL22 · Offline camera/gimbal protocol corpus

Owner authorization2026-10-13: implement discovery and feedback correlation using protocol corpus; preserve active soak. Integrate into Fly through a new signed build **after** accepted ENDURE20. No SDK/device. Contractor → Builder → Verify in one agent, no independent review.

Implementation stays in `pilot/protocol22`, new evidence/reference/research directories and new docs only. Keep PAYLOAD21 bytes and the ENDURE20 app/services/package/controllers/corpus/trust/slots unchanged. No socket transport to aircraft, no SITL flight or hardware commands. Official MAVLink XML and reference C serializer supply a pinned bounded dialect and independent encoding oracle; all generated traffic is synthetic corpus, not aircraft capture. No dependency installation or whole-project copy.

| REQ | Acceptance |
|---|---|
| P22-01 | Selected official XML/header snapshots have URLs/commit/hash/license; reference C packets and independently decoded fields match bounded JS codec. |
| P22-02 | Incremental MAVLink framing handles truncation/extensions/fragmentation, rejects corrupt/unknown/signed/unsupported frames with bounded input and trace;64-bit timestamps retain exact integers. |
| P22-03 | Camera component/proxy and gimbal manager/device discovery require heartbeat/information; expiration/reboot/reconnect invalidates generations/authority; limits/capabilities/stream status are distinct. |
| P22-04 | Local requests serialize ambiguous wire ACK keys; exact responder/command/proxy/result target checked; no local IDs invented on wire; timeout/rejected/late/reordered feedback cannot claim execution or implicit retry. |
| P22-05 | Camera ACK separated from fresh settings/capture observations; snapshot baseline and camera ID/index/time checked; missing focus/zoom/media/camera-definition evidence stays unknown. |
| P22-06 | Gimbal manager authority status separated from configure ACK; radian/quaternion/setpoint/flags/device/limits/fault handling tested; agreement is not causal execution proof. |
| P22-07 | Replayable ordered raw-frame corpus covers positive/negative/loss/boot/late/proxy/authority scenarios, report UI and conservative export with original hashes/context. |
| P22-08 | Current frozen inventory/controllers/source facts/corpus preserved; post-soak integration TIP/guard prepared; no signing/selection before independently validated ENDURE20 acceptance. |

Wire protocol can establish responder message identity and consistency with a request, not universal command causality or physical file existence. Use ACK_ACCEPTED and OBSERVATION_CONSISTENT_UNATTRIBUTED, never confirmed physical execution/media. Request-message ACK does not identify requested message in its wire payload; serialize requests per responder/command. After uncertainty require an explicit new transport/discovery generation; reconnect does not resume. Automatic non-idempotent retries disabled. Official target/controller/native/HIL/flight and actual camera/gimbal implementations remain NOT_CHECKED.
