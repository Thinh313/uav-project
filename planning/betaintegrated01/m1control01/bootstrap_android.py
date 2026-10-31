"""Explicitly bound reuse of the closed M1 owned emulator fixture, new receipts.

Imports only the pinned prior verification helper, not a flight/application
projection. All evidence destinations are redirected to this task before main.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys

R=Path(__file__).resolve().parents[3]
os.chdir(R)
sys.path.insert(0,str(R))
import planning.betaintegrated01.m1runtime.bootstrap_emulator as fixture


def main():
    source=Path(fixture.__file__).resolve()
    seal=json.loads((R/'evidence/betaintegrated01-m1runtime/handoff-final01.json').read_text())
    expected=seal['inventory'][str(source.relative_to(R))]['sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected, 'PREVIOUS_FIXTURE_DRIFT'
    fixture.E=R/'evidence/betaintegrated01-m1control01/emulator01'
    assert fixture.W==R/'.local/betaintegrated01/android'
    assert not fixture.E.exists()
    # The retained helper's explicit02 mode checks/reuses its own exact AVD,
    # without rewriting config, wiping userdata or deleting any lock.
    sys.argv=[str(source),'02']
    fixture.STOP=False
    signal.signal(signal.SIGTERM,fixture.halt)
    signal.signal(signal.SIGINT,fixture.halt)
    fixture.main()


if __name__=='__main__':
    main()
