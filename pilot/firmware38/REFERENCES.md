# FIRMWARE38 references

Local exact bytes are pinned in evidence/firmware38/source-pins.json. Reference source identifies 4.7.1; actual binary/device association remains NOT_CHECKED. Manual interpretation is same-agent work, not independent firmware validation or promotion into canonical SOT.

- [MAVLink parameter protocol](https://mavlink.io/en/services/parameter.html): distinguishes bytewise from C-cast parameter encoding; modern capability bits identify each. Missing flags require prior component knowledge. The exact-source legacy exception here is local/pinned, not a general rule. Classic containers preserve raw bytes; supported types and precision still require checks.
- [ArduPilot GCS failsafe](https://ardupilot.org/copter/docs/gcs-failsafe.html): receipt history, selected GCS and mode/options affect behavior. This module separates configuration and AP-state mock inputs from observed execution.
- [ArduPilot fences](https://ardupilot.org/copter/docs/common-geofencing-landing-page.html): fence types/actions/margins are separate settings. Current mapping records configured and active masks separately, without claiming actual enforcement.

Selected source anchors: ArduCopter/version.h; Parameters.cpp/.h, defines.h, Copter.h, events.cpp and ekf_check.cpp; GCS_Common.cpp capabilities(), GCS_Param.cpp cast_to_float/named-read index and GCS_MAVLink.cpp type conversion; AC_Fence.cpp/.h and Location.h altitude frame/configuration; AP_BattMonitor_Params.cpp/.h and Backend.cpp threshold/timer semantics; AP_Param.h AP_Enum inheritance; RC_Channels_VarInfo.h timeout declaration. Each source file's SHA is retained. The actual source branches, rather than page wording alone, drive the mock boundary cases.

The protocol pages do not prove aircraft firmware, Home datum, battery calibration, RC/GCS reachability, mode changes or physical return success. ACK/UID/CRC do not supply those missing facts.
