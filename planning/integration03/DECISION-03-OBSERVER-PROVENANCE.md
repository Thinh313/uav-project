# Observer provenance clarification03

Fixed before observer execution,2026-10-20. Existing RX journal elapsedMs records native WAL append-start time. It is not exact AP sensor acquisition or socket receipt time. The frozen WAL schema remains unchanged.

I06 age thresholds apply to the declared Native-WAL-feed age proxy with host/guest clock bracket uncertainty. Both position and attitude must be considered; a newer heartbeat cannot restamp the pose. The observer must label this source and proxy, and retain UNKNOWN for AP acquisition and receipt-to-append delay. It must not call this a conservative actual-age bound: append delay can make the proxy underestimate actual age.

Thresholds stay unchanged: nominal≤1000ms, visible stale after1000ms and no unbounded live motion after2000ms. A valid/invalid clock bracket is itself visible. The observer has no authority or GCS command path. These measures qualify an engineering journal-fed visualization, not safety-critical sensor latency or a calibrated training simulator.
