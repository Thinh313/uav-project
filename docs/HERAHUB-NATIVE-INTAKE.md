# HeraHub native integration intake / SURVEY02

Installation target is owner-confirmed HeraHub (old HeraLink). BOM/spec rows are document claims across variants; they do not identify a connected device or installed SDK. Brightness discrepancies do not block software work, per owner.

| Required observation | Current status | Next evidence |
|---|---|---|
| Hardware serial, model, revision, Android build/API/ABI | NOT_CHECKED | Read-only device inventory plus owner revision mapping |
| Display density, insets, orientation, touch constraints | NOT_CHECKED | Native window metrics, no inference from browser viewport |
| RtR telemetry/radio transport and accessible SDK/API | NOT_CHECKED | Approved SDK headers/docs and endpoint observations |
| Physical input devices, axis/button mapping/calibration | NOT_CHECKED | Native event inventory; no flight bindings by assumption |
| Payload/video stream and decoder latency | NOT_CHECKED | Observed URL/codec/auth path and measured decode/lifecycle |
| App lifecycle, network loss, thermal/memory/power | NOT_CHECKED | Installed diagnostic build on exact device revision |
| Firmware/vehicle/payload/radio as-built revisions | NOT_CHECKED | Serial-bound configuration tree, separate from BOM variant |

Development host has no `adb` executable on PATH in this session. No HeraHub device was connected or probed. No SDK downloaded, native project fabricated or APK claimed installed. Existing `app/core/device.mjs` already requires Android observation, explicit mappings/calibration and attachment; browser events cannot impersonate native evidence.

Read-only intake schema: evidence must include capture time, observer, device serial reference, hardware revision, OS/build/API/ABI, density/insets/orientation, package/SDK versions with hashes, transport endpoint scope, input inventory and video capabilities. Sensitive identifiers stay local. Unknown fields stay null. Reading SDK docs alone is not observed hardware capability. Diagnostics do not arm/change parameters or bind physical controls to flight commands.

This matrix makes native integration ready to scope once hardware/SDK evidence arrives; SURVEY02 browser/SITL evidence is not a native acceptance result.

HERA03 update: an existing host SDK/JDK was found in a later scan; APK compilation/dex/signature is complete. Owner confirms no SDK or device supplied; read-only adb inventory has zero devices. HERA03-NATIVE-CONTRACT.md and HERA03-DEVICE-RUNBOOK.md define the prepared artifact/trial. The table above remains NOT_CHECKED until actual device observations.
