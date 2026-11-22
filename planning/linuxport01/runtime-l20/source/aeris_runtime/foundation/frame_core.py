"""Exact inherited recording methods; no inherited constructor/policy chain."""
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
import hashlib,json,time
class FrameAdapter:
    def event(self, kind, data):
        if self.failed or self.closed:
            raise RuntimeError('FRAME_ADAPTER_CLOSED')
        self.journal.append_event(kind, data)
    def reject(self, raw, peer, reason, *, socket_truncated=False, receive_context=None):
        self.failed = True
        body = raw if type(raw) is bytes else b''
        context = receive_context or {'phase':'REJECTED_BEFORE_FRAME_API','journalAdmissionAttempted':False,
                    'localCallbackInvoked':False,'localReturnKnown':False,'SENTGroupAcknowledged':False,'attemptedStage':None}
        try:
            exclusive(self.root.parent / (self.root.name + '-rejected.json'), canonical({
                'reason': reason[:512], 'rawHex': body[:1025].hex(), 'inputBytes': len(body),
                'rawSHA256': hashlib.sha256(body).hexdigest(), 'peer': repr(peer)[:256],
                'socketTruncated': bool(socket_truncated), 'exactReceivedBytesRetained': not socket_truncated and len(body) <= 1025,
                'retainedPrefixBytes': min(len(body), 1025), 'completedFrames': self.frames,
                'completedStageRows':self.stage_rows, 'journalCompletedFrames':self.journal.frames,
                'journalPhaseAtFailure':self.journal.phase, 'frameAttempt':dict(context),
                'alreadyAdmitted': True if context['SENTGroupAcknowledged'] else None if context['journalAdmissionAttempted'] else False,
                'inputAdmissionClassification': 'COMPLETE_SENT_GROUP_ACKNOWLEDGED' if context['SENTGroupAcknowledged'] else 'JOURNAL_ATTEMPTED_OR_PARTIAL' if context['journalAdmissionAttempted'] else 'NOT_ADMITTED_VALIDATION_REJECTION',
                'sensorReplay': False, 'rejectionIsNotAdmittedFrame': not context['journalAdmissionAttempted']}) + b'\n')
        finally:
            self.journal.abort('FRAME_ADAPTER:' + reason[:512])
    def close(self):
        if self.failed or self.closed:
            raise RuntimeError('FRAME_ADAPTER_CLOSED')
        result = self.journal.close()
        self.closed = True
        wall = (self.last_rx - self.first_rx) / 1e9 if self.frames > 1 else None
        return {**result, 'frames': self.frames, 'modelSeconds': self.model.t,
                'stageRows':self.stage_rows,
                'receiveWallSeconds': wall,
                'actualRTF': ((self.frames - 1) / 1200 / wall) if wall else None,
                'requestedSpeedup': 1, 'capMs': 500, 'framesDropped': 0,
                'APExecutionAccepted': False, 'HeraCalibrated': False}
