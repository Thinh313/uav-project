"""Explicit METAVAL15 host + immutable Observer05 cadence composition, never relabeling actual policy."""
from importlib import import_module
from pilot.betaintegrated01.runtime.ap_stage import canonical
OBS=import_module('planning.betaintegrated01.cockpit05-observer05.policy')
R=OBS.R;INTERVAL_BYTES=OBS.INTERVAL_BYTES;INTERVAL_PATH=OBS.INTERVAL_PATH
amendment=OBS.amendment;feature_proof=OBS.feature_proof
def runtime():return import_module('planning.betaintegrated01.cockpit05-metaval15.runtime.policy')
def source_binding():return runtime().source_binding()
def validate_observer_policy(config):
 runtime().validate_recording_policy(config)
 if canonical(config.get('externalObserverRecordingPolicy'))!=canonical(amendment()):raise ValueError('METAVAL15_EXACT_CADENCE_AMENDMENT_REQUIRED')
 return amendment()
