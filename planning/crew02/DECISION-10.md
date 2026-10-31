# L2: bounded causal runtime replan

{
  "at": "2026-10-20T07:37:45.129959+07:00",
  "decision": "L2_CAUSAL_BUDGET_REASSESSMENT",
  "windowBudgetTotal": 4,
  "maximumAdditionalWindows": 2,
  "pilotLossReplacement": "sba631d2af67b4408b8a5",
  "finalNominalRun": "sbf8851e0c6ff4bc48e8d",
  "window2": "sb58be0f62a1645bdb19f",
  "window2Result": "UNKNOWN_NO_AUTO_NOT_PILOT_LOSS",
  "provenCause": "extra params already older than10s at Home issuance; no AUTO transmitted",
  "laterDeliveryStallCause": "UNKNOWN",
  "harnessRepair": "Explicit fresh preflight after upload/readback; single bounded passive ADBrawtail instead of repeated fullraw pulls",
  "noMetricRelaxation": true,
  "sourceId": "24e1749957027eced065ca47a3260a457f811f657c4bfc737fc2b15bd61cd020",
  "guardsUnchanged": true,
  "windowLimitS": 900,
  "minFreeGiB": 20,
  "stopGuardGiB": 20.5,
  "admissionGiB": 26,
  "aggregateLimitGiB": 2,
  "evidenceLimitMiB": 768,
  "noAutomaticRetry": true,
  "fifthWindowAllowed": false,
  "newHarnessSHA256": "068db7dcc5614de666342e48c58c1cc282c9a5b1e0e3ead62197f5b630410481",
  "freeBytes": 26146951168,
  "independentQA": "operator_milestone_qa approved bounded replan with no fifth automaticwindow; stale recurrence remains NOTREADY"
}

TIP and all original failures remain unchanged. No expired Home confirmation or flight guard is relaxed. A later delivery stall is distinct and its cause is unknown.
