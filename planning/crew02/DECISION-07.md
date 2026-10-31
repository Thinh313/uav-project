# Nominal mission with deliberate delayed camera feedback

Before any SITL launch, choose the existing synthetic peer `loss` fixture mode
for the nominal KML mission as well. In this fixture the word `loss` means only
camera100 capture feedback is held five seconds. It does not inject a flight
failure or change the mission. Camera102/101 and both preconfigured-primary
gimbals keep normal feedback. No fixture source/physics/autopilot parameter is
changed for this selection.

This allows a real pending B capture to be present when its owned process is
SIGSTOP-partitioned. The native three-second presence expiry must revoke B,
preserve pending UNKNOWN against late feedback, and allow A's AUTO mission to
continue. Late ACK/image-index protocol observations remain synthetic and never
prove exposure, media or physical execution. The nominal mission still must
reach every waypoint and end near Home, ground and disarmed with accepted native
review. Run metadata will explicitly retain fixture mode `loss` and mission
scenario `nominal`; they must not be conflated by the verifier.
