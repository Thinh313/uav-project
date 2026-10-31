# ADR-100 — Shared viewport and glass layout contract

Use isolated COCKPIT85 derived assets. A final scoped stylesheet owns the viewport geometry and component spacing so historical media-query padding no longer shifts telemetry away from brand. Keep source semantics and operations unchanged. Browser harness exposes an explicitly mock journey and the disconnected SITL presentation separately, without flight transport. Real Android and SITL acceptance remain separate gates.
