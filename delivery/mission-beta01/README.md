# AERIS Integrated Mission Beta01

Engineering simulation package for this macOS workspace. Development APK only. No HeraHub, real camera, production signature or physical flight acceptance.

## Start

Double-click `Launch.command` (default owned ArduPilot SITL; no automatic flight), or from the repository:

```sh
python3 -B delivery/mission-beta01/launch.py doctor --mode sitl
python3 -B delivery/mission-beta01/launch.py start --mode sitl
```

The launcher verifies pinned source/APK and cached ARM ArduPilot, applies the existing 20 GiB admission / 10 GiB floor plus reserve and decline forecast, starts the owned host and emulator-5582, waits for Android boot, then installs the pinned development APK. No downloads, automated flight commands, automatic retry or evidence deletion.

Open `http://127.0.0.1:8895/publisher`, choose VP8 and explicitly start the synthetic source. Keep the source tab foreground during video qualification. Android receives/decodes; the source is not a physical camera. Cockpit is `http://127.0.0.1:8896/` inside the owned Android shell. A browser view alone does not provide Android persistence or SAF evidence.

Protocol-only mock is explicit: `python3 -B delivery/mission-beta01/launch.py start --mode mock`. It does not prove ArduPilot physics or hardware.

Navigation completion in Review does not mean video or beta acceptance. The current handoff is **NOT READY**: the first source07 integrated run failed the maximum-gap gate (489 ms versus 250 ms). Do not count it as a qualified beta nominal. See the completion report.

## Exercise

1. Survey: choose polygon/corridor fixture or supported KML, acknowledge the explicit datum, compile and review plan. Verified SITL profile is a small synthetic flat area with relative-Home height, not arbitrary terrain or Hera configuration.
2. Preflight: acknowledge simulation and Home, activate the Android session, connect the owned SITL; wait for EKF/pre-arm ready. Read-only preflight, grant simulation authority, upload and compare readback.
3. Start synthetic video, collect the six 30 s windows. Arm on the simulated ground, review the fresh post-arm Home and explicitly confirm AUTO. Home approval expires after 10 s; a rejected request is not permission to retry automatically.
4. For hold/resume qualification, wait until initial takeoff has been proven and the next navigation leg is current. Hold and resume require current authority, session/boot/model and fresh observations. Resume additionally observes typed MIS_RESTART=0. The receiver checks transmitted command, ACK and armed heartbeat, not ACK alone. Early RTL can land safely but leaves the survey INCOMPLETE.
5. Discover/select the synthetic RGB or IR-look payload, grant a distinct payload lease, set gimbal and capture a synthetic JPEG. IR-look is not thermal measurement. Geotag is host telemetry reference, not measured camera exposure position.
6. After verified navigation/RTL/ground disarm and complete video windows, save video evidence and close to Review. Review exports the **selected run**; select the intended ID. Interrupted runs are kept and cannot be relabelled complete.
7. Export through Android SAF with a unique filename. Native writes, reads back and checks the bytes. A separate receiver recomputes raw hashes, KML/plan bindings, mode proof and video qualification:

```sh
node pilot/missionbeta01/receiver.mjs /absolute/path/to/exported-package.json
```

Save the workspace explicitly before testing Android restart. Reopening restores mission input and closed history, never flight or payload authority. A restored mission is not a resumed flight.

## Stop and limits

`Ctrl+C` in the launch terminal, or `python3 -B delivery/mission-beta01/launch.py stop`. Stop validates the owned controller identity and closes only that runtime. Existing locks are never removed blindly. No evidence/container/volume auto-cleanup. A guard failure or unknown closure blocks a new flight allocation; diagnose and preserve receipts first.

This is a workspace-bound engineering handoff with cached dependencies. It is not a clean-machine installer, hardware qualification, real-world survey certification, or a measured claim of superiority over DJI. Read the completion report for the exact build, actual runs, failures and remaining gates.
