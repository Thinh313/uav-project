# Pinned sources and interpretation

14/10/2026. Local XML/ArduPilot/Python generator files are read-only inputs. schema-generation.json and mapping-source-pins.json bind exact bytes. These references support implementation choices, not proof of actual vehicle configuration, certification or protocol conformance.

- MAVLink [serialization](https://mavlink.io/en/guide/serialization.html): field-size sorting, extension order, little endian, CRC_EXTRA, v2 trailing-zero truncation and unknown incompatibility-flag rejection. v1 has no mission_type extension. The subset has no message-signature verification.
- MAVLink [mission protocol](https://mavlink.io/en/services/mission.html): distinct mission/fence/rally types and upload/download exchange; protocol implementations may request missing items again. Our two duplicate-request buffers and 5s transaction limit are engineering mock policy, not complete retry conformance.
- ArduPilot [inclusion/exclusion fences](https://ardupilot.org/copter/docs/common-polygon_fence.html): polygon/circle fences and independent configuration. Actual enable/altitude/options/enforcement still require target-specific readback and testing.
- ArduPilot [GCS failsafe](https://ardupilot.org/copter/docs/gcs-failsafe.html): AP-side receipt history and context matter; host downlink does not supply those facts. Mode observations cannot establish the cause of a failsafe.

Local pinned MissionItemProtocol_Fence.cpp supplies command/param1/lat-lon/readback frame mapping. Copter mode.h supplies the restricted mode numeric table. EKF2/3 Outputs.cpp getVariances()/send_status_report() establishes square-root test-ratio quantities for this mock mapping. AC_Fence.cpp shows Copter FENCE_ACTION=1 is RTL-or-Land, so it is deliberately not universally normalized to successful RTL. No physical outcome follows from raw parameter equality.

Interpretation incidents kept separate:

1. First explicit XML traversal omitted standard.xml, where GLOBAL_POSITION_INT lives. Generation stopped before producing definitions; generation-attempt01.json retained.
2. The local upstream generator warns about CAMERA_TRACKING_STATUS_FLAGS_IDLE=0 in an unrelated camera bitmask enum. Selected message layouts/CRCs all agree with upstream mavparse. No camera schema is included here.
3. Upstream v2-generated Python with force_mavlink1 retained v2 extension payload bytes in the observed vectors. A separately generated v1 schema oracle is required; original oracle-vectors1.json and failing logic1.json retained. This observation is limited to the local pinned generator.
4. A test modified a shared fixture coordinate in RAM. The test now deep-clones fixture inputs; original source bytes never changed. No earlier failure receipt is replaced.
5. The pinned EKF source reports sqrt(testRatio), so a direct comparison of the XML's variance-named fields to an arbitrary ratio threshold was incorrect. Squaring is now covered by a threshold case that would pass incorrectly under the earlier direct comparison. Earlier pass receipts are historical, not substituted for current-source validation.
