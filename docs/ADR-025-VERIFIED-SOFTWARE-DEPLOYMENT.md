# ADR-025 · verified software slots and separate persistent data

Accepted for PACK15 host engineering. Use a bounded uncompressed stream with a canonical Ed25519-signed inventory instead of platform installer dependencies. Explicitly inventory portable JS/static assets and two host profiles; keep data, private keys, research, SDKs and runtime binaries outside payload. Trust policy and required expected manifest digest are caller-provided outside the package. Package has no embedded self-trusting public key.

Verify every byte before immutable slot publication and again before an explicit start. Slots do not contain mutable data; startup requires an external data root and a matching versioned profile/capacity scenario. Default checkout behavior is retained. No active-slot pointer, remote update or in-flight restart is introduced. An engineering key generated on this host is not claimed to be RtR production identity. Declare HeraHub-only fields unmeasured and refuse startup for that proposal.

Sizing compares estimates to real format/store limits and explicitly includes concurrent export/checkpoint/software reserve. Capacity is an admission forecast, not allocated space or Android endurance. Installed package smoke tests use isolated local state and never connect/ARM/AUTO.
