# CONTROL05 startup envelope and independent channel ordering

Declared before the next actual attempt. All earlier source, raw, receipts and
selected CONTROL04 oracle remain immutable.

Cached ArduPilot4.7.1 GCS_Common.cpp200–220 explicitly sends three0x30/0x20 SiK
radio bootloader-reset pairs before configuring the MAVLink communication port.
UARTDriver::txspace returns0 while disconnected, so connecting during initialization
can receive a suffix of that startup sequence. Unknown bytes remain errors.

The new observer classifies zero to three exact3020pairs, maximum6 bytes, only
before the firstFD/FE MAVLink magic byte. A fragmented incomplete pair has200ms
maximum inter-byte age. Complete pairs do not require the next MAVLink packet to
arrive within200ms: AP calibration can take seconds. The existing20s bound now
explicitly waits for first MAVLink magic even if startup prefix bytes were seen.
Any byte latches EOF as terminal, including a partial/complete startup pair.
No unknown byte, fourth pair, malformed half-pair or post-MAVLink reset prefix
is skipped or resynchronized. The existing strict CRC Framer is unchanged.

Every received raw chunk is durably recorded before classification. Completed
prefix pairs are explicitly journaled and the cold receiver reconstructs and
compares them against raw. Prefix classification does not count as a MAVLink
frame. Native relay remains byte-transparent, without stripping. Root waits for
an actually CRC-validated passive42/1 heartbeat and AP executable validation
before native CONNECT; the passive observer transmits zero MAVLink bytes.

Nominal release proof must not compare absolute host timestamps to guest times.
The closed native journal must show CRC AP42/1 mode17 after the BRAKE packet and
before neutral/release TX, by native record order, within its own freshness bound.
Each command/neutral/release byte sequence must match the host relay's packet SHA.
The independent passive channel must observe mode17 before the LAND packet on the
host's clock. It may legitimately observe mode17 after native cleanup packets.
Native UP/revocation and fresh different-lease/consent remain independent checks.
No ACK, local send or process termination is proof of flight execution or ground.
