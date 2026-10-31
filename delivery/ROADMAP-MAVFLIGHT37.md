# MAVFLIGHT37 roadmap supplement

14/10/2026. New supplement only; frozen canonical roadmap/SOT/source/candidate/ENDURE remains unchanged.

| Feature | Current gate | Next preparation | Subsequent runtime gate |
|---|---|---|---|
| F08 geofence | Offline binary subset and full mock item/raw-param readback PASS | Pin actual firmware/capabilities, quantized geometry admission, altitude frame/options/active-enable mapping; prove parameter cast semantics | Actual pinned AP SITL upload/readback/breach/context/failsafe interaction |
| F10 preflight/failsafe | Partial wire observations + explicit synthetic supplements, uncertainty retained | Complete readonly parameter/unit/sentinel/mode/clock mapping for named AP build; AP-side GCS/independent RC data contract and cause evidence | Fault injection on AP SITL, then Hera bench/HIL/operator cases |
| F11 return reserve | APFLIGHT36 synthetic energy model only; remaining Wh not inferred from percentage | Calibrated battery/payload/power and datum/environment/landing inputs; reviewed units/uncertainty | Hardware calibration and field validation; no autonomous recommendation before acceptance |

Priority remains core control, reliable evidence and operator safety. Simulation rendering/AI autonomy/fleet and product comparison cannot substitute for firmware and hardware acceptance. Full mock readiness is explicitly synthetic, not permission to arm or fly.

No APK/emulator/SITL/signing/integration is authorized by this supplement. The 20GiB disk floor applies to later work too. Resource availability does not change scope. ENDURE acceptance remains separate; no restart or verdict update follows from module37.
