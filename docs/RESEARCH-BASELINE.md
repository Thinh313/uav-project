# Research baseline · 12/10/2026

This is a first technical baseline, not a complete competitive study or runtime audit. Source receipts and full primary captures are in `research/ragas-baseline`. The inherited paste remains a research input; statements are accepted only at the evidence scope actually checked.

## RAGAS and source discovery

GitHub's primary API response contains 13 release entries; the newest returned is **v4.0.14-b111**, published 09/10/2026, with Android ARM64 APK and Ubuntu 20.04 x64 DEB assets. v4.0.10 also uses build 111. This substantiates a versioning audit question, not an OTA defect. Binaries have not been downloaded, executed or disassembled.

The release notes report survey calculation fixes, QGC plan handling, camera mission upload fixes, waypoint altitude modes and terrain display. They document claims about changes; they do not replace regression traces or flight-test evidence. M0's tests independently exercise its own analytical model, not RAGAS behavior.

The organization API returned two public repositories: `ragas-release` and `supersplat`. The authenticated GitHub connector returned an empty accessible-repository list for this owner. No RAGAS/Ghidorah application source was obtained; private source might exist outside this access scope. Supersplat is identified as a 3D Gaussian Splat editor, not assumed to be a GCS dependency.

The GitHub website view misleadingly showed no releases while API returned releases. API capture is used for release metadata; website rendering is not interpreted as release deletion.

## Protocol references

[MAVLink command documentation](https://mavlink.io/en/services/command.html) distinguishes command acceptance from completion. M0 models explicit acceptance and fresh observed mode; actual MAVLink message encoding, retries, long-running command semantics and target routing remain for integration work.

[Mission protocol](https://mavlink.io/en/services/mission.html) is the basis for a future transaction harness; M0 does not implement it. [QGC plan specification](https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html) is the future interchange reference; M0's rehearsal package is deliberately its own format. [ArduPilot SITL](https://ardupilot.org/dev/docs/sitl-simulator-software-in-the-loop.html) supplies the next integration environment; no SITL executable has been run for M0.

## Claims and unknowns

Official source quality (tier A) means authority for what the maintainer publishes, not independent measurement. Source capture timestamp/hash and exact claim spans are stored. No unrelated Python `ragas` evaluation library is included. Flutter/Dart, Ghidorah/ROS, security/SBOM and hardware details from the inherited paste remain unverified against source/binary/device in this project.

DJI/Auterion/UgCS workflow benchmarking remains pending. Two initial DJI URLs failed in the web extractor; no comparison verdict is derived from that failure. The next comparison must use the same survey tasks, devices/configurations and measured operator outcomes.
