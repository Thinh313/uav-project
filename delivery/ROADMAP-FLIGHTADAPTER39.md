# FLIGHTADAPTER39 roadmap supplement

14/10/2026. New supplement only; canonical roadmap/SOT/source/candidate/ENDURE unchanged.

| Area | Preparation now verified | Next gate |
|---|---|---|
| Composition |One readonly mock adapter; union framer, central session and separate telemetry/preflight/typed-policy results |Reviewed full AP stream framing/filtering, announcement/discovery and source association with actual named binary |
| Context/loss |Byte receipts, wrapping sequence/boot clock, stale/owner/writer revocation and conflict quarantine; no restore authority |Actual link/reboot/clock behavior and transport authentication/signing; no inferred AP receipt from GCS downlink |
| Typed config |28 readonly typed mock values, named index65535, bounded one-pass witnesses |Actual AP encoding/type/count/read duration and parameter-change notifications; explicit policy for longer live transactions |
| Flight safety |Rich failsafe/altitude mapping separate from old normalized config; incomplete remains UNKNOWN |AP-side state/cause/latch and confirmed Home/Origin/Terrain; typed fence upload/readback/enforcement adapter separately reviewed |
| Product/native |No frozen Fly/native integration or signature; old artifacts preserved |Android journey/runtime persistence, input/video, then Hera bench/HIL; runtime/build admission remains separate |
| Reliability |Old ENDURE failure preserved; no retry/resume/interval aggregation |A separately authorized valid endurance campaign/acceptance; host and device gates remain distinct |

Current verdict is MOCK_COMPOSITION_VERIFIED, not product flight readiness. No SDK/device needed for further bounded mock preparation. Existing no-SITL/emulator/no-signature constraints continue until changed by the user. Preserve20GiB floor and old evidence.
