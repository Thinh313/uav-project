# Project instructions

Follow the parent disk-hygiene instructions. Never copy the whole project to /tmp. Use current checkout; no per-task build folders. No dependency install is needed for the app. Project Python dependencies, if required by the evidence toolkit, live in `.venv`.

Use the transfer methods at `../00_AI_Work_MethodBox` through `../03_Vibecode_MethodBox`; current transfer entrypoints take precedence over older references. Separate Contractor specification, Builder implementation and Verify phases. A single agent can switch phases; do not claim independent review. Spawn agents only with explicit user authorization or applicable explicit delegation instructions.

The working name is AERIS. The confirmed first workflow is survey/mission planning. UI prototype and synthetic data must be labeled. No operational MAVLink link or production flight commands in M0. Preserve schema version, unit, altitude datum, timestamp and aircraft/session identity. ACK alone must not be portrayed as vehicle execution. Do not invent evidence, certifications or performance results.

Edit internal source facts only in `sot/source_canonical`, regenerate the registry through the adapter, review the diff and refresh the baseline/gate. External sources remain claims in Refinery even when official. Browser captures/primary files and hashes must accompany claims. No automatic promotion to verified_primary.

A required test not run is NOT_CHECKED. Record REQ/AC coverage and evidence. Major source/stack/flight changes require an ADR and scoped TIP. Hardware integrations need recorded target configurations and the relevant simulation/HIL/flight gates.
