"""Bounded owner of exactly one pinned, loopback-only internal SITL instance."""
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import signal
import socket
import subprocess
import sys
import time

R=pathlib.Path(__file__).resolve().parents[2];P=R/'pilot/simdrop77';E=R/'evidence/simdrop77'
IMAGE='ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55'
BINARY='011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482'
NAME='aeris-simdrop77';FLOOR=20*2**30;MINIMUM=22*2**30;QUOTA=256*2**20;PORT=5897


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def put(p,d):
    if shutil.disk_usage(R).free < FLOOR+65536:raise RuntimeError('DISK_FLOOR_WRITE_REFUSED')
    with p.open('x') as f:
        json.dump(d,f,indent=2);f.flush();os.fsync(f.fileno())


def command(args):
    c=subprocess.run(args,text=True,capture_output=True,timeout=30)
    if c.returncode:raise RuntimeError(str(args)+':'+c.stderr)
    return c.stdout.strip()


def admitted(free,allocated):
    return free>=MINIMUM and allocated<QUOTA


def missing_object(returncode,stderr):
    return returncode!=0 and 'no such object:' in stderr.lower() and NAME in stderr


def serial_listening(text):
    return any(len(parts)>3 and parts[1].endswith(':1680') and parts[3]=='0A'
               for parts in (line.split() for line in text.splitlines()))


def main():
    run=sys.argv[1];assert run in ['run01','run02','run03','run04','run05','run06'];rep=sys.argv[2];assert rep in ['rep01','rep02','rep03','rep04']
    allocated=sum(p.stat().st_size for d in [E,R/'.local/simdrop77'] if d.exists() for p in d.rglob('*') if p.is_file())
    free=shutil.disk_usage(R).free
    admission={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeBytes':free,'requiredFreeBytes':MINIMUM,'floorBytes':FLOOR,'forecastCampaignBytes':QUOTA,'hostMarginBytes':1536*2**20,'admitted':admitted(free,allocated),'allocatedEvidenceBytes':allocated,'run':run,'replication':rep}
    put(E/(run+'-admission.json'),admission)
    assert admission['admitted'],'RESOURCE_GATE_NO_SITL_STARTED'
    assert not (E/run).exists(),'EXISTING_ATTEMPT_NO_RETRY'
    gate=json.loads((E/'mock-gate.json').read_text());assert gate['status']=='PASS' and gate['exitCode']==0
    pins=json.loads((E/'source-pins-v2.json').read_text())['files'];assert all(sha(R/n)==h for n,h in pins.items()),'SOURCE_PIN'
    existing=set()
    for pattern in ['run*/closure.json','run*/launch.json','run*/container-created.json']:
        for f in E.glob(pattern):existing.add(json.loads(f.read_text())['containerId'])
    assert len(existing)<6,'MAX_SIX_ACTUAL_CONTAINERS'
    attempts=[json.loads(f.read_text()) for f in E.glob('run*/launch.json') if json.loads(f.read_text()).get('replication')==rep]
    assert len(attempts)<2 and not any((E/f['run']/'driver-result.json').exists() for f in attempts),'REPLICATION_ALREADY_DONE_OR_ATTEMPT_BOUND'
    assert sha(R/'runtime/sitl/arducopter')==BINARY
    before=subprocess.run(['docker','inspect',NAME],text=True,capture_output=True,timeout=30)
    assert missing_object(before.returncode,before.stderr),'OWNED_NAME_EXISTS_OR_DOCKER_UNAVAILABLE'
    image=json.loads(command(['docker','image','inspect',IMAGE]))[0];assert image['Id']==IMAGE.split('@')[1]
    with socket.socket() as sock:sock.bind(('127.0.0.1',PORT))
    out=E/run;out.mkdir();state=R/'.local/simdrop77'/run;state.mkdir(parents=True,exist_ok=False)
    archive=out/'source';archive.mkdir()
    for f in P.iterdir():
        if f.is_file():
            with (archive/f.name).open('xb') as target:target.write(f.read_bytes())
    put(out/'source-pins.json',{'files':pins,'archivedModule':{p.name:sha(p) for p in archive.iterdir()}})
    args=['docker','run','--rm','-d','--name',NAME,'--label','aeris.task=simdrop77','--label','aeris.run='+run,
          '--platform','linux/amd64','--pull','never','--read-only','--tmpfs','/tmp:rw,size=16m','--network','bridge',
          '--cpus','1','--memory','256m','--cap-drop','ALL','--security-opt','no-new-privileges',
          '--log-opt','max-size=2m','--log-opt','max-file=2','-p',f'127.0.0.1:{PORT}:5760',
          '-v',str(R/'runtime/sitl')+':/aeris:ro','-v',str(P)+':/task:ro','-v',str(state)+':/state','-w','/state',
          IMAGE,'/aeris/arducopter','-w','--model','quad','--home','10.854,106.807,10,0',
          '--defaults','/aeris/copter.parm,/task/sitl.parm','--speedup','1']
    assert shutil.disk_usage(R).free>=MINIMUM,'LIVE_RECHECK'
    cid=command(args);child=None;error=None;stopping=False;driver_code=None;minimum=free;parent=os.getppid()
    def stop_signal(*_):
        nonlocal stopping
        stopping=True
    signal.signal(signal.SIGTERM,stop_signal);signal.signal(signal.SIGINT,stop_signal)
    def inspect():
        info=json.loads(command(['docker','inspect',NAME]))[0]
        assert info['Id']==cid and info['Image']==image['Id'] and info['Config']['Labels']['aeris.run']==run
        return info
    try:
        put(out/'container-created.json',{'containerId':cid,'imageId':image['Id'],'command':args})
        info=inspect();assert info['State']['Running'];deadline=time.monotonic()+25
        while True:
            console=command(['docker','logs',NAME])
            sockets=command(['docker','exec',cid,'cat','/proc/net/tcp','/proc/net/tcp6'])
            if serial_listening(sockets):break
            assert time.monotonic()<deadline and inspect()['State']['Running'],'GUEST_READY'
            time.sleep(.2)
        (out/'guest-before-connect.txt').write_text(console)
        (out/'guest-listen-sockets.txt').write_text(sockets)
        put(out/'launch.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'containerId':cid,'imageId':image['Id'],
            'pid':info['State']['Pid'],'startedAt':info['State']['StartedAt'],'binarySha256':BINARY,'command':args,'port':PORT,'replication':rep,'run':run,
            'physics':'ARDUPILOT_INTERNAL_QUAD_NOT_HERA_OR_SIM32','speedup':1,'hardDeadlineS':420,'freeBytes':shutil.disk_usage(R).free,'noTCPProbe':True})
        put(out/'inspect-before-driver.json',info)
        with (out/'driver-console.txt').open('x') as log:
            child=subprocess.Popen(['node',str(P/'driver.mjs'),str(out.relative_to(R))],cwd=R,stdout=log,stderr=subprocess.STDOUT)
            start=time.monotonic();last_check=0
            while child.poll() is None:
                current=shutil.disk_usage(R).free;minimum=min(minimum,current)
                if stopping or os.getppid()!=parent:raise RuntimeError('OWNER_STOP_OR_PARENT_LOSS')
                if time.monotonic()-start>420:raise RuntimeError('HARD_DEADLINE')
                if current<20.5*2**30:raise RuntimeError('HEADROOM_LOST')
                if time.monotonic()-last_check>2:
                    last_check=time.monotonic();assert inspect()['State']['Running'],'GUEST_DIED'
                    assert sum(p.stat().st_size for p in state.rglob('*') if p.is_file())<32*2**20,'STATE_QUOTA'
                    assert sum(p.stat().st_size for d in [E,R/'.local/simdrop77'] if d.exists() for p in d.rglob('*') if p.is_file())<QUOTA,'CAMPAIGN_QUOTA'
                time.sleep(.2)
            driver_code=child.returncode
            if driver_code:raise RuntimeError('DRIVER_FAILED:'+str(driver_code))
    except BaseException as exc:
        error=str(exc)
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        removed=False
        try:
            info=inspect();put(out/'inspect-before-stop.json',info);console=command(['docker','logs',NAME])
            assert len(console.encode())<=4*2**20
            with (out/'ap-console.txt').open('x') as f:f.write(console)
            command(['docker','stop','-t','3',NAME]);deadline=time.monotonic()+10
            while subprocess.run(['docker','inspect',NAME],capture_output=True,timeout=30).returncode==0:
                assert time.monotonic()<deadline,'REMOVAL_TIMEOUT';time.sleep(.2)
            removed=True
        except BaseException as exc:error=(error+'; ' if error else '')+str(exc)
        prune=command(['docker','image','prune','-f'])
        put(out/'closure.json',{'containerId':cid,'containerRemoved':removed,'driverExitCode':driver_code,'error':error,
            'minimumObservedFreeBytes':minimum,'replication':rep,'freeBytes':shutil.disk_usage(R).free,'stateRetained':str(state.relative_to(R)),
            'imagePrune':prune,'containerStopIsNotLandingEvidence':True})
    print(json.dumps({'run':run,'driverExitCode':driver_code,'containerRemoved':removed,'error':error,'minimumFreeGiB':minimum/2**30}),flush=True)
    if error:raise SystemExit(1)


if __name__=='__main__':main()
