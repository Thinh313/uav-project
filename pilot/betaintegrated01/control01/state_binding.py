"""Caller-owned simulated AP state binding; no proof of physical safe ground."""
from pathlib import Path
import hashlib
import json
import os
import stat


def regular_bytes(path,bound):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode)or st.st_nlink!=1 or st.st_size>bound:
            raise ValueError('STATE_FILE_TYPE_OR_BOUND')
        with os.fdopen(fd,'rb',closefd=False)as f:return f.read(bound+1)
    finally:os.close(fd)


def validate_state(config,state,raw):
    state,raw=Path(state),Path(raw)
    if state.is_symlink()or not state.is_dir():raise ValueError('OWNED_STATE_DIRECTORY')
    case=config['caseID'];wipe=config['wipeState']
    if type(case)is not str or not 1<=len(case)<=64 or type(wipe)is not bool:
        raise ValueError('CASE_OR_WIPE_TYPE')
    owner_raw=regular_bytes(state/'.aeris-control-owner.json',4096)
    owner=json.loads(owner_raw)
    if owner.get('caseID')!=case:raise ValueError('FOREIGN_CASE_STATE_OWNER')
    intervals=regular_bytes(state/'message-intervals-chan1.txt',4096)
    if intervals!=b'245 250\n242 1000\n'or hashlib.sha256(intervals).hexdigest()!=config['passiveIntervalsSHA256']:
        raise ValueError('PASSIVE_INTERVAL_FILE_BINDING')
    result={'caseID':case,'wipeState':wipe,'ownerSHA256':hashlib.sha256(owner_raw).hexdigest(),
            'passiveIntervalsSHA256':hashlib.sha256(intervals).hexdigest(),
            'scope':'LOCAL_CALLER_BOUND_SIMULATOR_STATE_NOT_PHYSICAL_GROUND_AUTHENTICATION'}
    if wipe:
        if (state/'eeprom.bin').exists():raise ValueError('FRESH_CASE_MUST_NOT_WIPE_EXISTING_EEPROM')
        result['stateMode']='FRESH_CASE_FACTORY_WIPE'
    else:
        reuse=config['stateReuse']
        if type(reuse)is not dict or set(reuse)!={'previousBoot','eepromSHA256','eepromBytes','groundDisarmedReceiptSHA256'}:
            raise ValueError('STATE_REUSE_SCHEMA')
        if type(reuse['previousBoot'])is not str or reuse['previousBoot']==config['boot']:
            raise ValueError('REBOOT_REQUIRES_NEW_BOOT')
        eeprom=regular_bytes(state/'eeprom.bin',4*1024*1024)
        if type(reuse['eepromBytes'])is not int or len(eeprom)!=reuse['eepromBytes'] or hashlib.sha256(eeprom).hexdigest()!=reuse['eepromSHA256']:
            raise ValueError('EEPROM_BEFORE_REBOOT_MISMATCH')
        receipt=regular_bytes(raw/'caller-ground-disarmed.json',16384)
        if hashlib.sha256(receipt).hexdigest()!=reuse['groundDisarmedReceiptSHA256']:
            raise ValueError('GROUND_RECEIPT_BINDING')
        observation=json.loads(receipt)
        if observation.get('caseID')!=case or observation.get('previousBoot')!=reuse['previousBoot']or observation.get('groundDisarmedObserved')is not True:
            raise ValueError('GROUND_REBOOT_CALLER_GATE')
        result.update(stateMode='NO_WIPE_PERSISTENT_CASE_STATE',previousBoot=reuse['previousBoot'],
                      eepromBeforeSHA256=reuse['eepromSHA256'],eepromBytes=len(eeprom),
                      groundDisarmedReceiptSHA256=reuse['groundDisarmedReceiptSHA256'],
                      groundEvidenceRequiresIndependentRawCheck=True)
    return result
