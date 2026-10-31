# ADR077 — correct SITL gyro source rate

b3 reached actual firmware discovery/20typed parameters but correctly blocked AP_PREARM_NOT_HEALTHY. Raw STATUSTEXT: Gyro0 rate400Hz < loop rate*1.8 720Hz. Initial task SIM_RATE_HZ400 was an incorrect internal-physics test preset; it is not a hardware defect or a reason to disable checks. Original b3 raw/blocked preflight/abort and source are retained.

sitl-v4.parm explicitly sets SIM_RATE_HZ1200. Same Copter4.7.1 binary, loop/mission coordinates, profile, camera and FS checks, speedup1, resource limits and logging. No ARMING_SKIPCHK or force-arm change. Fourth fresh qualification attempt is admitted only after mock and source pins; this explicit amendment to the engineering attempt budget includes all three prior failures, all before upload/arm. It is not HTTP/flight mutation retry or campaign resume. No external SIM32 pacing/source/candidate/ENDURE change.
