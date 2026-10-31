# Roadmap supplement after FLIGHTSAFETY42

2026-10-14. No canonical frozen roadmap/SOT rewrite. Named actual simulator profile now proves negative battery/fence pre-arm, normal arm/takeoff, home-circle boundary-update breach→RTL/land/disarm, GCS heartbeat blackout→RTL and post-restoration NEW RTL heartbeat evidence, manual TCP reconnect/fresh named reads and landing. Finalrun03 only; priorfailed/insufficient runs retained. This is isolated harness, not native/Fly functionality or physical Hera acceptance.

Now: qualify firmware families using real parameter discovery before writes: 4.7 ARMING_SKIPCHK0 vs legacyARMING_CHECK1; RTL_ALT_M(floatm) vs oldRTL_ALT(intcm). Keep UNKNOWN/refusal for absent type/schema/version, typed readback and fresh session/boot ownership. Adapter/policy integration must be separately scoped, without replacing old receipts or ENDURE gates.

Next safety corpus: immutable profile readback; fixed-boundary crossing and polygon missionfence upload/download; altitude/Home/terrain references; GCS/no-position Landfallback, activebattery/RC/EKF failsafes and AUTO/FS_OPTIONS exemptions. Guard test interactions and stale/ambiguous/incomplete evidence; no ACK-only PASS. Run realSITL with headroom, close only ownedruntime, preserve failuretraces.

Native progression: survey→preflight→Fly→review via qualified adapter, deliberate operator confirmation and explicit SITLidentity; Androidpersistence/emulator gates still pending diskbudget. Physical HeraHub/input/video/SDK/calibration, authenticated radio and payload actuation/video need actualdevice/provider contracts/HIL/flight gates. ActualSIM32 performance/endurance acceptance remain separate; don't combine failedENDURE intervals. No Fly/signature/SDK/device or ENDURElaunch approved in42.
