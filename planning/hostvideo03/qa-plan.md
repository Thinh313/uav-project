# HOSTVIDEO03 independent QA plan

Mock/source first; runtime measurements only from root-collected evidence.

- **H01** Receiver source/import graph never loads producer iframe, publisher module, VideoEncoder or a local encoding probe. Only frozen viewer/relay dependencies and receiver controls are present. Negative: Attempt publisher/control/native/SAF/mirror routes; reject without saved-workspace mutation.
- **H02** No source, viewer, measurement or retry starts automatically on page load, foreground or restoration. Each start/measure/pause/stop is explicit. Negative: Late asynchronous start after background/stop; old generation must close and cannot restart.
- **H03** Receiver coverage uses its own visible canvas and current foreground lifecycle. Hidden/clipped/offscreen viewport invalidates measurement. Negative: Background during measurement retains failed/partial report; no silent denominator reset.
- **H04** Host producer visibility is separate evidence. Unmodified publisher stops on hidden/pagehide; receiver visibility does not attest source visibility. Negative: Missing or mismatched host attestation remains NOT_CHECKED, never implied by decoded frames.
- **H05** Frozen exact run/boot/config/feed/profile/server identity, clock, key dependencies and stale-frame fences stay intact. Negative: Wrong identity or stale async callback cannot render or publish accepted counters.
- **H06** Wrapper binds exact localhost host/origin/path/method/MIME and bounded JSON/log/output; no flight/payload/workspace API. Negative: Traversal/encoded slash, unknown query, cross-origin, POST mutation, over-size body and mirrored native operation do not produce side effects.
- **H07** Raw report remains immutable and topology sidecar names its exact SHA and identities. Declared host producer and Android decoder have distinct actual user-agent evidence. Negative: Wrong report SHA/run/config, report replay, excess reports, incomplete host visibility or mislabelled topology is rejected or marked unverified.
- **H08** Each actual window recomputes every sample bound, FPS over full outage duration, calibrated p95 upper, first-config initial-ready and fresh post-resume recovery. Negative: No source diagnostics or successful mock may become runtime FPS, coldness or camera acceptance.
- **H09** Two distinct owned emulator/app cold boots and two declared 30 s windows are separately evidenced. Host source may intentionally be warm. Negative: Warm page navigation, explicit restart or codec probe cannot be relabelled as emulator/app cold.
- **H10** Resource admission and 28 GiB stop buffer, closure, budgets and all declared old hashes are independent gates. Negative: Any observed 20 GiB breach fails the floor even after guards close or capacity recovers.

Both actual windows and cold starts must pass unchanged gates. Missing runtime evidence remains NOT_CHECKED. FIELD02 flight and active-lease gates remain separate.
