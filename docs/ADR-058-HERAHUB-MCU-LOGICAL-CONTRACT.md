# ADR058 · HeraHub MCU contract derived from legacy documents

MCU document revision0.3 dated2024-07-02 covers HeraLink Hybrid USBVCP/115200/custom MAVLink. Applicability to currentHeraHub unconfirmed. Incoming Hera flightplan16.5kg/H and request3.5kg are separate contexts, never merged into a calibrated profile.

Normalize symbolic messages and proposed state machines in pilot/heramcu45. Preserve raw document names/types plus disputes. Wire IDs/enum absentvalues/CRC/USB interface/target/signing/version/timeout/ACK correlation remain unknown. No codec can be emitted; arbitrary supplied definitions cannot unlock physical encoding in thismodule. USB64bytes vs mapping160bytes is an unresolved transport-vs-message distinction. Realframing requires actualdialect and descriptors.

Local mock session/boot/transaction/step correlations support adversarial tests but are not fields of realCOMMAND_ACK. ACK alone not persist/calibration result. Nine calibration groups require group-specific result evidence. Configuration save remains uncertain until explicit exact readback; persistence over reboot only observed for the mockpeer with a fresh handshake and configuration read, never restored authority. Stale/duplicate/foreign data cannot refresh sources. Bounded preservation logs reject overflow, terminalsessions cannot reconnect in place; new session starts empty.

All prepared input outputs are preview-only synthetic values. No aircraft parameters/RC override/manual mode/payload transport/native route integrated. Existing frozen namespaces untouched. No SDK/APK/signature/SITL/resource installation.
