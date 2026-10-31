"""Constructor capacity only; every receive/model/send/failure method inherited exactly."""
from pathlib import Path
import time
from pilot.betaintegrated01.runtime02.frame_adapter import FrameAdapter as AcceptedFrameAdapter
from .journal import SegmentedJournal
from pilot.betaintegrated01.cockpit04.capacity import journal_policy

class FrameAdapter(AcceptedFrameAdapter):
    def __init__(self, root, run, epoch, model, *, max_frames, maximum_seconds=90, peer=None, io=None):
        if type(max_frames) is not int or not 1 <= max_frames <= 2**32:
            raise ValueError('FRAME_BOUND')
        self.model, self.max_frames, self.peer = model, max_frames, peer
        self.root = Path(root)
        self.frames = 0
        self.stage_rows = 0
        self.current = None
        self.origin_ns = time.monotonic_ns()
        self.failed = self.closed = False
        self.first_rx = self.last_rx = None
        self.journal = SegmentedJournal(root, run, epoch, journal_policy(maximum_seconds), io=io)
        self.journal.append_event('TIMING_ORIGIN', {'hostMonotonicNs': self.origin_ns,
                                  'stageDomain': 'HOST_MONOTONIC_RELATIVE_TO_ORIGIN'})
