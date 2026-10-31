# ADR-051 — explicit firmware and typed safety contracts

Accepted for user-authorized offline mock scope, 14/10/2026. MAVFLIGHT37 deliberately admits only REAL32 and does not normalize full firmware/configuration semantics. Build FIRMWARE38 separately, with read-only imports of its codec/session helpers and APFLIGHT36 journal.

Bind source interpretation to a digest of selected local ArduCopter source, version and schemas. A synthetic AUTOPILOT_VERSION announcement must match reviewed contract identity/capabilities. Modern C-cast/bytewise negotiation is explicit; the pinned AP source advertises legacy PARAM_FLOAT and casts values to float. Permit this exception only in its named source-bound contract. Unknown/conflicting claims fail closed. Neither version/UID nor CRC authenticates the aircraft.

Decode classic parameter raw bytes with declared types. C-cast integers outside unambiguous float32 range are unknown; bytewise 32-bit values preserve all bits, including NaN-shaped float containers. Keep classic 64-bit types unsupported. Read requests return mock buffers only and support named-read index65535. A current process-local readback witness cannot be recreated by serialized snapshots.

Use a richer policy schema for failsafe action/fallback graphs and options instead of collapsing SmartRTL, RTL-or-Land, Brake-or-Land or terminate into the old normalized enum. Preserve mAh thresholds rather than fabricate Wh. Configured policy, modeled trigger/branch and observed result remain separate; control commands and execution claims are absent.

Altitude mapping uses AP Location::AltFrame (0 AMSL,1 Home,2 Origin,3 Terrain), not MAV_FRAME. Reference snapshots include datum, boot/context, uncertainty and receipt age. Bounds and lower/upper frame differences are explicit; active fence/type flags and minimum-floor activation require separate state. No field-model geometry/native/Fly integration or real firmware admission is authorized here.
