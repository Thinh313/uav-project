# HANDOFF09 · linked survey results and delivery package

Owner-authorized local increment, 2026-10-12. Eight required REQ/AC; no SDK/device dependency. SHA-256 establishes byte integrity, not signed origin or capture authenticity.

| REQ / AC | Required outcome |
|---|---|
| H09-1 | Append-only versioned associations bind exact closed record ID/digest. Original source, summary/outcome and journal remain unchanged. Stale digest and duplicate association refuse before mutation. |
| H09-2 | Imported PNG/JPEG/MP4, GeoJSON and UTF-8 text reports are bounded and verified by bytes, magic/schema, size and SHA. Required declared provenance distinguishes imported-file from synthetic-fixture. Imported files do not establish capture on this flight. |
| H09-3 | Durable no-overwrite blob/revision publications share exclusive archive writer, queue and capacity/reserve. Restart validates associations; incomplete/corrupt stages remain visible. Capacity/IO faults never acknowledge a saved association or delete evidence. |
| H09-4 | Review separates planned camera commands in simulator from files imported, synthetic fixtures and unverified physical capture. Reached/completed do not prove survey coverage, image quality or processing results. |
| H09-5 | Self-contained .aeris-handoff.json contains original record, retained v3 spool, complete association chain, all attachment bytes and review notes. Derived inventory is recomputed. Export validates all references before returning; bounded importer rejects missing/substituted bytes, rehashed false summaries, traversal names or incomplete checkpoint. No extraction paths or execution. |
| H09-6 | Review supports association intake, file download and handoff export/open offline. Invalid import retains previous valid selection. Historical record import remains supported. Shared controls align at responsive sizes. Import/export causes zero flight writes. |
| H09-7 | Actual filesystem restart, partial-publication/storage faults and adversarial package tests pass; synthetic media is explicitly labeled. No real payload capture is fabricated. |
| H09-8 | Existing mission/QGC/profile/journal correctness remains valid. Bounded real loopback SITL regression and browser/offline/source/SOT gates pass. |

Limits: 8 MiB per attachment, 32 MiB total / 32 files per record, 64 MiB JSON package, 64 revisions per record. PNG/JPEG signature and MP4 ftyp verification identifies supported containers, not forensic authenticity or full codec validity. GeoJSON is operator-supplied WGS84 data; no orthomosaic/DEM generation, automatic EXIF matching, quality certification, media streaming or signed recipient acceptance. Larger field datasets and hardware timestamp/camera integration remain next gates. Imported bundles are local review only, never written into live execution archive automatically. Segmented records retain per-segment UNKNOWN; delivery does not aggregate them into a completed mission.
