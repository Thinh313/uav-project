# AERIS source repository

Private GitHub repository: https://github.com/nclamvn/aeris

This is the existing independent AERIS source tree, not RAGAS source. The latest isolated UI overlay at this initial Git snapshot is COCKPIT85. The previously qualified Android package is NATIVE84 development10; no Android85 or production-flight qualification is asserted.

## Current UI

- `native/cockpit85/`: isolated native-derived UI assets and host preview.
- `delivery/COMPLETION-COCKPIT85.md` and `.html`: scoped acceptance, known limits and screenshots.
- `evidence/cockpit85/verification.json`: concise result; `verification-ui.json`: 306 selected browser scenarios and 1,127 aggregate assertions.
- `delivery/ROADMAP-COCKPIT85.md`: next Android integration gates.

From the project root: `node native/cockpit85/server.mjs`, then http://127.0.0.1:8848/mock.html. Requires Node22+ and the existing JDK/journal harness paths described in that module. It runs only a mock host journey; no flight transport. The separate `/` presentation reads an explicitly labelled NATIVE84 history archive included in the QA85 fixture. Tests create exclusive receipt paths and must use fresh evidence namespaces rather than overwrite old receipts.

## What this repository contains

Source, native/pilot modules, project documents, research/reference assets, selected regression fixtures and the complete COCKPIT85 evidence bundle are committed. Existing source/candidate/ENDURE bytes are not rewritten to prepare this repository. All original data remains on the host.

`.local`, virtual environments, runtime/AVDs/SITL downloads, private signing keys/tokens, development APK/build artifacts, old signed software packages and the bulk historical evidence archive are excluded from Git. Test fixtures are explicitly allowlisted. In particular, this source repository is not an independent copy of the complete ENDURE campaign archive; old fingerprint manifests can reference deliberately omitted host-only evidence. Do not infer 24-hour acceptance from this Git snapshot or change historical reports to make an incomplete clone appear complete.

No production signing key, hardware SDK or HeraHub access is provided by this repository. Before device deployment repeat the documented Android, transport, payload, HIL and physical-flight gates. Keep user-confirmed disk floor20GiB and never delete evidence automatically.
