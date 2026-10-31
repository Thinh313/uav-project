"""Read-only fullruntime entry10 policy probe; no realprime or launch."""
from pathlib import Path
from importlib import import_module
import json,shutil
R=Path(__file__).resolve().parents[4]
H='planning.betaintegrated01.cockpit05-entry10.host'
p=import_module(H+'.policy02')

def inspect():
    return {'budget':p.task_budget(shutil.disk_usage(R).free),'externalRecordingPolicy':p.amendment(),
      'runtimeWiring':'WIRED_CODE_MOCK_ONLY','actualRuntimeLaunched':False,
      'newActualControllerResourcesFullGuardian':'NOT_IMPLEMENTED','full30Actual':'NOT_RUN'}
if __name__=='__main__':print(json.dumps(inspect(),indent=2))
