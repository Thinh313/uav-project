# Read-only scene integration

Root switches explicitly to Builder for this bounded lane. The existing QA agent
reviews source/contracts independently. Root's visual inspection is self-review.

Reuse immutable visual56 FlightScene, licensed CesiumDrone/PBR/HDR assets and
simhand01 RotorAudio. No downloads, dependency install, physics equations or
flight commands. Serve through the same companion origin. The wrapper consumes
qualified, committed FDM frames and never writes pose back to flight control.
Fixture, replay and live provenance must remain distinct.

Input age is based on original compute/sample time, conservatively adding the
HTTP round-trip bound; receiving an old pose does not make it fresh. Freeze stale
pose and mute audio. Payload pictures use a separate camera/render pass and a
specific committed frame, with camera intrinsics/extrinsics and original raw ref;
never crop the observer HUD and call it a camera image.

Verify ENU/NED/quaternion/camera basis with analytic cases, context/order/clock
negatives and mutation isolation. Render the reused model in a clearly marked
fixture for screenshot QA. Actual live ground-truth, camera-file, audio and
performance acceptance still require the integrated Android–SITL release.
