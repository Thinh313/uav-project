"""Explicit unchanged entry10 real-host guard; no mutation/injection."""
from importlib import import_module
_guard=import_module('planning.betaintegrated01.cockpit05-entry10.host.admission')
DiskGuard=_guard.DiskGuard
DiskGuardError=_guard.DiskGuardError
DISK_POLICY=_guard.DISK_POLICY
