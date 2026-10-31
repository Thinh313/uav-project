"""Pure/fake-wire checks; never creates a real socket or starts AP/Android."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import time
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control01.mavlink import Framer,FramingError,observe,DEFINITIONS
from pilot.betaintegrated01.control01.transport import Context,FaultState,PassiveObservation
from pilot.betaintegrated01.control01.state_binding import validate_state


def packet(ident,payload,seq=0,system=42,component=1):
    # Separate test encoder; production code contains no encode/transmit API.
    head=bytes([0xfd,len(payload),0,0,seq,system,component])+ident.to_bytes(3,'little')
    value=0xffff
    for byte in head[1:]+payload+bytes([DEFINITIONS[ident][2]]):
        tmp=byte^(value&255);tmp=(tmp^((tmp<<4)&255))&255
        value=((value>>8)^(tmp<<8)^(tmp<<3)^(tmp>>4))&65535
    return head+payload+struct.pack('<H',value)


def main():
    cases=[];log=[]
    h=packet(0,struct.pack('<IBBBBB',5,2,3,128|1,4,3),seq=250)
    f=Framer();assert f.feed(h[:5],100)==[];p=f.feed(h[5:],200);assert len(p)==1
    assert observe(p[0])['fields']['armed']is True
    cases.append({'case':'fragmented_crc_verified_heartbeat','status':'PASS'})
    corrupt=h[:-1]+bytes([h[-1]^1])
    try:Framer().feed(corrupt,100);raise AssertionError('CRC_MUST_FAIL')
    except FramingError:pass
    partial=Framer();partial.feed(h[:5],100)
    try:partial.tick(1_500_000_101);raise AssertionError('PARTIAL_STALE_MUST_FAIL')
    except FramingError:pass
    cases.append({'case':'crc_and_partial_age_fences','status':'PASS'})
    monitor=PassiveObservation(lambda kind,data:log.append((kind,data)))
    monitor.receive(h,1000);at=monitor.latest['HEARTBEAT']['observedHostNs']
    monitor.receive(h,2000)
    assert monitor.latest['HEARTBEAT']['observedHostNs']==at and monitor.duplicate_frames==1
    monitor.receive(packet(0,struct.pack('<IBBBBB',9,2,3,1,4,3),seq=249),3000)
    assert monitor.latest['HEARTBEAT']['customMode']==5 and monitor.older_frames==1
    assert all(item[0]in('PASSIVE_RX','PASSIVE_FRAME')for item in log)and monitor.snapshot()['applicationTXBytes']==0
    assert log[0][0]=='PASSIVE_RX'and log[1][0]=='PASSIVE_FRAME'
    cases.append({'case':'passive_zero_TX_raw_before_parse_duplicate_and_old_do_not_refresh','status':'PASS'})
    b=PassiveObservation(lambda *a:None)
    b.receive(packet(33,struct.pack('<IiiiihhhH',5000,108540000,1068070000,13000,3000,0,0,0,0),seq=1),1)
    try:b.receive(packet(33,struct.pack('<IiiiihhhH',100,108540000,1068070000,10000,0,0,0,0,0),seq=2),2);raise AssertionError('BOOT_REGRESSION')
    except RuntimeError:pass
    cases.append({'case':'boot_regression_requires_new_epoch','status':'PASS'})
    context=Context('rcontrol','econtrol','bcontrol');fault=FaultState(context)
    request={'run':'rcontrol','epoch':'econtrol','boot':'bcontrol','action':'CUT_NATIVE_LINK','nonce':'n01','hostNs':100}
    for change in ({'epoch':'foreign'},{'hostNs':-3000000000},{'hostNs':True},{'action':'RESTORE_LINK'}):
        invalid={**request,**change}
        try:FaultState(context).cut(invalid,200);raise AssertionError('CUT_FAULT_MUST_FAIL')
        except ValueError:pass
    fault.cut(request,200);assert fault.cut_latched
    try:fault.cut(request,201);raise AssertionError('CUT_NOT_REPEATABLE')
    except ValueError:pass
    cases.append({'case':'foreign_stale_bool_cut_fenced_one_shot_no_restore','status':'PASS'})
    out=R/'evidence/betaintegrated01-m1control01/host/mock01';out.mkdir()
    state=out/'owned-state';state.mkdir();(state/'.aeris-control-owner.json').write_text(json.dumps({'caseID':'case03'}))
    first=validate_state({'caseID':'case03','wipeState':True,'boot':'b1'},state,out)
    assert first['stateMode']=='FRESH_CASE_FACTORY_WIPE'
    eeprom=b'actual-mock-eeprom';(state/'eeprom.bin').write_bytes(eeprom)
    receipt=json.dumps({'caseID':'case03','previousBoot':'b1','groundDisarmedObserved':True}).encode()
    (out/'caller-ground-disarmed.json').write_bytes(receipt)
    config={'caseID':'case03','wipeState':False,'boot':'b2','stateReuse':{'previousBoot':'b1','eepromSHA256':hashlib.sha256(eeprom).hexdigest(),'eepromBytes':len(eeprom),'groundDisarmedReceiptSHA256':hashlib.sha256(receipt).hexdigest()}}
    restored=validate_state(config,state,out);assert restored['stateMode']=='NO_WIPE_PERSISTENT_CASE_STATE'
    try:validate_state({**config,'boot':'b1'},state,out);raise AssertionError('BOOT_MUST_DIFFER')
    except ValueError:pass
    cases.append({'case':'ground_new_boot_same_owned_state_no_wipe_hash_binding','status':'PASS'})
    pins={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest()for p in(R/'pilot/betaintegrated01/control01').glob('*.py')}
    (out/'results.json').open('x').write(json.dumps({'status':'PASS_BUILDER_MOCK','cases':cases,'sourceSHA256':pins,
                            'APStarts':0,'AndroidStarts':0,'realSocketsCreated':0,'physicalOrFlightAcceptance':False},indent=2)+'\n')
    print(json.dumps({'status':'PASS','cases':len(cases)}))


if __name__=='__main__':main()
