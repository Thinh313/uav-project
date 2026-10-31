"""Single-owner balanced matrix; no retries, frozen AP v2 and nominal speedup1."""
from pathlib import Path
import os
import sys
import subprocess
import time
import json
import shutil
import signal
import urllib.request
import datetime
import socket

R = Path(__file__).resolve().parents[2]
M = R / 'pilot/sim32-pipe03'
E = R / 'evidence/sim32-pipe03'
ENV = dict(os.environ, SIM32_ENGINE='optimized', SIM32_SPEEDUP='1', AERIS_INSTRUMENT='1')
server = None
child = None
workers = []
records = []
aborted = None
active_probe = None
floor = 20 * 2**30


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, d):
    with path.open('x') as f:
        json.dump(d, f, indent=2)
        f.write('\n')


def call(args):
    return subprocess.check_output(args, text=True, timeout=5).strip()


def status():
    with urllib.request.urlopen('http://127.0.0.1:8799/api/state', timeout=4) as f:
        return json.load(f)


def stop_workers():
    global workers
    stopped = []
    for p in workers:
        if p.poll() is None:
            p.terminate()
        p.wait(timeout=8)
        stopped.append({'pid': p.pid, 'exitCode': p.returncode})
    workers = []
    return stopped


def samples(pids):
    return {'utc': stamp(), 'hostNs': time.monotonic_ns(), 'freeBytes': shutil.disk_usage(R).free,
            'hostLoadAverage': os.getloadavg(),
            'workerPs': subprocess.run(['ps', '-p', ','.join(map(str, pids)), '-o', 'pid=,%cpu=,rss=,etime='],
                                       capture_output=True, text=True).stdout.strip() if pids else '',
            'power': call(['pmset', '-g', 'batt'])}


def run_child(args, name, limit, pids):
    global child
    log = (E / (name + '-console.txt')).open('x')
    child = subprocess.Popen(args, cwd=R, env=ENV, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    log.close()
    started = time.monotonic()
    telemetry = (E / (name + '-host.jsonl')).open('x')
    minimum = shutil.disk_usage(R).free
    try:
        while child.poll() is None:
            row = samples(pids)
            minimum = min(minimum, row['freeBytes'])
            telemetry.write(json.dumps(row, separators=(',', ':')) + '\n')
            telemetry.flush()
            if row['freeBytes'] < floor + 768 * 2**20:
                raise RuntimeError('Host disk reserve reached; stop owned matrix')
            if time.monotonic() - started > limit:
                raise RuntimeError('Owned case wall-time watchdog')
            if any(p.poll() is not None for p in workers):
                raise RuntimeError('CPU injection worker died before case completion')
            time.sleep(1)
        return {'exitCode': child.returncode, 'wallSeconds': time.monotonic() - started,
                'minimumFreeBytes': minimum, 'childPid': child.pid}
    finally:
        telemetry.flush()
        os.fsync(telemetry.fileno())
        telemetry.close()
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=10)


try:
    assert shutil.disk_usage(R).free > floor + 5.5*2**30 + 512*2**20, 'Full peak resource admission'
    with socket.socket() as port_check:
        port_check.bind(('127.0.0.1',8799))
    write(E / 'matrix-v2-admission.json', {'at': stamp(), 'freeBytes': shutil.disk_usage(R).free,
          'floorBytes': floor, 'peakTaskBudgetBytes': int(5.5*2**30), 'hostMarginBytes': 512*2**20,
          'cpuLogical': int(call(['sysctl','-n','hw.logicalcpu'])), 'memoryBytes': int(call(['sysctl','-n','hw.memsize'])),
          'power': call(['pmset','-g','batt']), 'speedup': 1, 'rateHz': 1200,
          'maximumNegativeDebtUs': 500000, 'automaticRetries': 0})
    # Counterbalanced pairs: same UI/mission, host physics, identical AP/resources.
    case=0
    for rep,loads in enumerate([[0,2,6],[6,2,0]],1):
        for added in loads:
            engines=['optimized','fused'] if (rep+added//2)%2 else ['fused','optimized']
            for engine in engines:
                ENV=dict(os.environ,SIM32_ENGINE=engine,SIM32_SPEEDUP='1',AERIS_INSTRUMENT='1')
                case+=1;name=f'c{case:02d}w{added}r{rep}{engine[:1]}'
                if(E/'matrix-v2-stop-request.json').exists():raise RuntimeError('Explicit controlled stop request at case boundary')
                print('START',name,stamp(),flush=True)
                with(E/(name+'-server-console.txt')).open('x')as log:
                    server=subprocess.Popen(['node',str(M/'server.mjs')],cwd=R,env=ENV,stdout=log,stderr=subprocess.STDOUT)
                for _ in range(70):
                    try:
                        state=status();assert state['run'] is None and not state['busy'];break
                    except Exception:
                        if server.poll()is not None:raise RuntimeError('Preview startup failed')
                        time.sleep(.1)
                else:raise RuntimeError('Preview admission timeout')
                for index in range(added):
                    with(E/f'{name}-worker{index}.txt').open('x')as log:
                        workers.append(subprocess.Popen([sys.executable,'-B',str(M/'cpu_worker.py'),str(index+1)],cwd=R,stdout=log,stderr=subprocess.STDOUT))
                pids=[p.pid for p in workers];time.sleep(3)
                record={'name':name,'replicate':rep,'addedCpuWorkers':added,'engine':engine,'workerPids':pids,'startedAt':stamp(),'profile':{'load':'offset','wind':'gust'},'automaticRetries':0}
                try:
                    record.update(run_child(['node',str(E/'live-ui.mjs'),name,'offset','gust'],name,280,pids))
                    qa=json.loads((E/f'live-browser-qa{name}.json').read_text());record.update(run=qa['run'],uiStatus=qa['status'])
                    state=status()
                    if state['run']is not None or state['busy']or state['starting']:raise RuntimeError('Case not closed')
                    if not qa['run']or not(E/'runs'/qa['run']/'closure.json').exists():raise RuntimeError('Missing owned closure')
                finally:
                    record['workersStopped']=stop_workers();record['completedAt']=stamp();records.append(record);write(E/(name+'-orchestration.json'),record)
                    if server and server.poll()is None:server.terminate();server.wait(timeout=35)
                    server=None
                print('END',name,record.get('uiStatus'),record.get('run'),flush=True)
                if record.get('uiStatus')!='PASS':raise RuntimeError('UI gate failed; stop new-case admission for diagnosis, no automatic retry')
except BaseException as e:
    aborted=str(e)
    print('MATRIX_STOP',repr(e),flush=True)
    raise
finally:
    stop_workers()
    if active_probe and (E/'runs'/active_probe/'launch.json').exists() and not (E/'runs'/active_probe/'closure.json').exists():
        launch=json.loads((E/'runs'/active_probe/'launch.json').read_text())
        pid=launch['backendPid']
        cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
        if f'/pilot/sim32-pipe03/backend.py {active_probe} ' in cmd:
            os.kill(pid,signal.SIGCONT)
        closure=subprocess.run([sys.executable,'-B',str(M/'runtime.py'),'stop',active_probe],cwd=R,env=ENV,capture_output=True,text=True,timeout=30)
        write(E/(active_probe+'-emergency-closure.json'),{'at':stamp(),'exitCode':closure.returncode,'stdout':closure.stdout,'stderr':closure.stderr})
    if server and server.poll() is None:
        server.terminate()
        server.wait(timeout=35)
    write(E/'matrix-v2-completion.json',{'at':stamp(),'status':'CAPTURED'if not aborted else 'ABORTED',
          'error':aborted,'cases':records,'serverPid':server.pid if server else None,
          'serverStopped':not server or server.poll() is not None,'automaticRetries':0,
          'freeBytes':shutil.disk_usage(R).free,'acceptance':'NOT_FINAL_UNTIL_RAW_REPLAY_AND_PRESERVATION'})
