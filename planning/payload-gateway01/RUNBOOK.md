# Run the integrated mock cockpit

From `/Users/os/Downloads/AI technique/aeris`, with at least20GiB+128MiB free:

```sh
python3 planning/payload-gateway01/serve.py --evidence-root evidence/payload-gateway01/demo-next
```

Use a new evidence directory on each launch. Open `http://127.0.0.1:8866/`. Discovery → choose RGB or IR → explicit60-second mock grant → open synthetic preview → change gimbal/ISO and observe mock readback → close panel → shutter → Hồ sơ → Xuất gói ảnh(.tar). IR is thermal-look, not temperature measurement. No connection to a drone or physical camera is possible in this runtime. Plan/preflight/native-only actions are disabled in this host slice, not certified here.

The UI does not silently retry commands or restore rights. A fault can be injected from the controlled-fault disclosure. Reboot requires discovery/selection/grant again. Missing exposure event/file, bad GNSS and truncated JPEG remain unknown/quarantined. Selecting another camera revokes the old device scope and clears displayed readback.

Ctrl-C closes the owned child process, seals the writer, releases only its own writer lock and removes the curated stage. Server self-stops at15minutes or20GiB+128MiB resource guard. Evidence and incomplete/PENDING folders are retained. Do not delete a stale lock or write into a workspace while another server owns it. A failed/incomplete journal opens read-only; this milestone intentionally has no repair/delete endpoint.

Explicit restart with existing evidence, after clean closure:

```sh
python3 planning/payload-gateway01/serve.py --evidence-root evidence/payload-gateway01/demo-after-restart --resume-workspace evidence/payload-gateway01/demo-next/workspace
```

This appends a new host session to the owned mock workspace. It does not grant previous rights or overwrite old run receipts. An explicit preview start admits a new browser media epoch and prevents old-config replay. Payload device boot and media browser boot remain separate.

Independent implementation receiver for a browser-downloaded TAR:

```sh
python3 planning/payload-gateway01/receive.py /absolute/path/aeris-capture-ID.tar --capture capture-ID --package PACKAGE_SHA_FROM_UI --out evidence/payload-gateway01/new-receiver-receipt.json
```

Receiver verifies exact three TAR members, original SHA, manifest/sidecar context, geotag math and local replay controls. No TAR extraction onto the filesystem. Package integrity does not attest source authenticity or mission success. `gateway.json` is separate diagnostic lineage, not part of the three-member core package.

Useful checks (new output paths required):

```sh
node planning/payload-gateway01/test.mjs evidence/payload-gateway01/mock-next
node planning/payload-gateway01/http-test.mjs evidence/payload-gateway01/http-next.json
```

The HTTP test intentionally changes mock state/preview epochs and reboots the mock adapter. Run it on the test instance before interacting with the browser, not during someone else's demo. No APK/build/SITL/emulator/install is needed. Full hardware, multi-device performance, Android and field acceptance remain separate.
