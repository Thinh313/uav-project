# ADR: bounded input scheduling and pre-socket refusal

Accepted for isolated NativeIO07, user authorization27/10/2026.

Keep single journal/wire owner, cooperative global16 checkpoints, all original barriers,200ms inputlease and250ms framefreshness. Move sampler scheduling away from UI render queue using immutable event state plus separately enforced UI-liveness/foreground/focus/context. This improves availability during benign UIwork; it does not attest a new physical event or bypass stale UI. Any over200ms stall still failsclosed.

Make pre-socket approval an explicit phase after durable intent, outside the sender callback. Known approvalrefusal with healthy storage may close a FAILED journal with distinct unsent disposition. Actual callback failure remains unknown, and storage failure remains uncommitted. New reader tests distinguish these cases. No oldjournal/releasehistory rewrite.

Do not redesign storage/batchfsync/retime/dropframe/relaxlease. New APK and actual short provide evidence before30min. Outcome is bounded validated improvement, not guarantee under arbitrary filesystem or host stalls.

L2 clarification: remove the Activity monitor only from the new Activity writeCheckpoint method. Root verified its sole invocation is the existing single serial worker with an immutable current String; the method only converts local bytes and writes/renames/syncs files. Holding the Activity monitor across that worker fsync can block main-thread render/update and UI liveness. Preserve the serial worker, exact file format/order/atomic rename and barriers. No View access moves off main and no broader UI storage rewrite is included. Independent QA verifies callsites and generation/closure boundaries.

Before long, also project native journal usage from closed short raw records because each input now carries sampler provenance. Use the maximum of full-run and every rolling-at-least5s byte rate without interpolation, times projected long native duration including startup/hold/landing, plus2MiB closure reserve. Require this to fit unchanged160MiB journal quota, in addition to existing duration and fresh whole-case admission gates. This is conditional capacity planning, not a guarantee or permission to weaken any guard. No shortPASS means no long or projected acceptance.

Known availability boundary: queued held samples whose atomic release fence has become stale after UP/CANCEL failclosed and close FAILED with no further socket entry. This is safety behavior, not proof of a completed nominal BRAKE/regrant flow. Actual short must still complete that flow; no test waiver or fence relaxation.
