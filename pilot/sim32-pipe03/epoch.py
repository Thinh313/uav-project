"""Sticky per-run lease. No queued packet can reset a stale/suspended epoch."""
import time
import json
import os
import uuid


class Epoch:
    def __init__(self, state, out, run, mono=time.monotonic_ns, wall=time.time_ns):
        self.state, self.out, self.run = state, out, run
        self.mono, self.wall = mono, wall
        self.id = str(uuid.uuid4())
        self.last_mono, self.last_wall = mono(), wall()
        self.active = False
        self.terminal = False
        self.reason = None
        self.draining = False
        self.publish('LIVE')

    def publish(self, status):
        d = {'run': self.run, 'epoch': self.id, 'status': status, 'reason': self.reason,
             'backendMonotonicNs': self.mono(), 'backendWallNs': self.wall()}
        p = self.state / 'epoch.pending'
        p.write_text(json.dumps(d))
        os.replace(p, self.state / 'epoch.json')

    def drain(self):
        self.check()
        self.draining = True
        self.publish('DRAINING')

    def invalidate(self, reason, **detail):
        if not self.terminal:
            self.terminal, self.reason = True, reason
            self.publish('TERMINAL')
            with (self.out / 'epoch-terminal.json').open('x') as f:
                json.dump({'run': self.run, 'epoch': self.id, 'reason': reason,
                           'backendMonotonicNs': self.mono(), 'backendWallNs': self.wall(),
                           **detail}, f, indent=2)
                f.write('\n')
        raise RuntimeError('Epoch invalid: ' + self.reason)

    def check(self):
        if self.terminal:
            raise RuntimeError('Epoch invalid: ' + self.reason)
        m, w = self.mono(), self.wall()
        dm, dw = m-self.last_mono, w-self.last_wall
        limit = 3_000_000_000 if self.active else 30_000_000_000
        if dm < 0 or dw < 0:
            self.invalidate('CLOCK_REGRESSION', deltaMonotonicNs=dm, deltaWallNs=dw)
        if dm > limit or dw > limit:
            self.invalidate('STALE_OR_SUSPENDED', deltaMonotonicNs=dm, deltaWallNs=dw)
        if self.active and abs(dw-dm) > 250_000_000:
            self.invalidate('CLOCK_DISCONTINUITY', deltaMonotonicNs=dm, deltaWallNs=dw)

    def progress(self):
        self.check()
        self.last_mono, self.last_wall = self.mono(), self.wall()
        self.active = True

    def close(self):
        if not self.terminal:
            self.publish('CLOSED')
