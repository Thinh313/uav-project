"""Pure launch preparation/argv only. Does not start AP, services or send MAVLink."""
from pathlib import Path
import hashlib
import json
import time


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_pins(repository,manifest):
    root=Path(repository);body=json.loads(Path(manifest).read_text())
    mismatches=[name for name,expected in body['sourceSHA256'].items()if digest(root/name)!=expected]
    if mismatches:raise ValueError({'SOURCE_PIN_DRIFT':mismatches})
    return body


def build_config(repository,variant,run,epoch,boot,evidence,case_id,*,maximum_seconds=90,wipe_state=True,state_reuse=None):
    if variant not in ('nominal','loss')or maximum_seconds not in(60,90,1960):raise ValueError('PROFILE_OR_DURATION')
    root=Path(repository);path=root/'pilot/betaintegrated01/cockpit04/profiles'/variant/'run-profile02.json'
    profile=json.loads(path.read_text())
    result={**profile,'run':run,'epoch':epoch,'boot':boot,'evidence':str(Path(evidence).resolve()),
            'maximumSeconds':maximum_seconds,'bind':['127.0.0.1',9012],'caseID':case_id,'wipeState':wipe_state,
            'expectedConfigSHA256':digest(path),'referenceProfile':str(path.relative_to(root))}
    if not wipe_state:
        if state_reuse is None:raise ValueError('REBOOT_STATE_BINDING_REQUIRED')
        result['stateReuse']=state_reuse
    return result


def prepare_fresh_case_state(repository,state,case_id):
    # Exclusive creation deliberately refuses existing state, including abandoned attempts.
    root=Path(repository);state=Path(state);state.mkdir(parents=False,exist_ok=False)
    source=root/'pilot/betaintegrated01/cockpit04/profiles/message-intervals-chan1.txt'
    with(state/'.aeris-control-owner.json').open('x')as f:json.dump({'caseID':case_id},f)
    with(state/source.name).open('xb')as f:f.write(source.read_bytes())
    return {'caseID':case_id,'state':str(state.resolve()),'intervalsSHA256':digest(source)}


def cut_request(run,epoch,boot,nonce,*,observed_host_ns=None):
    return {'run':run,'epoch':epoch,'boot':boot,'action':'CUT_NATIVE_LINK','nonce':nonce,
            'hostNs':time.monotonic_ns()if observed_host_ns is None else observed_host_ns}


def host_argv(config):
    return ['python3','-B','-m','pilot.betaintegrated01.cockpit04.backend','--config',str(Path(config).resolve())]


def supervisor_argv():
    return ['python3','-B','-m','pilot.betaintegrated01.cockpit04.ap_supervisor','--config','/evidence/run-config.json']
