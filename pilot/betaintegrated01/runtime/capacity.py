"""Declared format bounds, not empirical bitrate or a waiver of live guards."""
def estimate(seconds, free_bytes, *, evidence_remaining=3 * 2**30):
    for value in (seconds, free_bytes, evidence_remaining):
        if type(value) is not int or value < 0:
            raise ValueError('INTEGER_BOUND')
    if not 1 <= seconds <= 1800:
        raise ValueError('DURATION_BOUND')
    frames = seconds * 1200
    # Three max2048 frame records and one max2048 stage record per frame.
    host_records = frames * 4 * 2048
    # Single AP producer, max10 fixed64-byte events per frame, one pendingframe.
    ap_records = (frames + 1) * 10 * 64
    # At most8 responses +tick+request+expiry per100ms poll, plus failure reserve.
    clock_records = ((seconds + 15) * 120 + 100) * 2048
    metadata_and_native = 160 * 2**20
    primary = host_records + ap_records + clock_records + metadata_and_native
    peak = primary * 3  # original + independent copy + export, simultaneously.
    floor = 10 * 2**30 + 256 * 2**20
    admitted = free_bytes >= 20 * 2**30 and free_bytes >= floor + peak and peak <= evidence_remaining
    return {'format': 'aeris-m1-runtime-capacity', 'version': 1, 'seconds': seconds,
            'declaredMaximumFrames': frames, 'hostFrameRecordBytesBound': host_records,
            'APStageEventBytesBound': ap_records, 'clockRecordBytesBound': clock_records,
            'metadataAndNativeReserveBytes': metadata_and_native, 'primaryBytesBound': primary,
            'originalCopyExportPeakBytesBound': peak, 'evidenceRemainingBytes': evidence_remaining,
            'hostFreeBytes': free_bytes, 'entryBytes': 20 * 2**30, 'floorAndReserveBytes': floor,
            'admittedByArithmetic': admitted, 'actualLaunchAuthorizedByArithmetic': False,
            'boundStatus': 'DECLARED_AND_ENFORCED_FORMAT_COUNTS_NOT_EMPIRICAL_AVERAGE',
            'requiresLive15sForecastAndSourceRuntimeGate': True}
