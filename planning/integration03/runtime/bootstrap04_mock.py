"""Bounded injected mocks only. Never invokes Docker, sockets or APK tools."""
import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import json
import pathlib
import shutil
import socket
from bootstrap04 import *

ROOT = pathlib.Path(__file__).resolve().parents[3]
E = ROOT / "evidence/integration03-bootstrap04"
CID = "a" * 64
RUN = "s" + "b" * 20
RESULTS = []


def inspect(**state):
    value = {"Id": CID, "Name": "/aeris-integration03", "RestartCount": 0,
             "Config": {"Labels": {"aeris.task": "integration03", "aeris.run": RUN}},
             "State": {"Running": True, "Status": "running", "Pid": 17, "ExitCode": 0,
                       "OOMKilled": False, "Error": "", "Paused": False, "Restarting": False,
                       "StartedAt": "2026-10-20T01:00:00.000000001Z", "FinishedAt": "0001-01-01T00:00:00Z"}}
    value["State"].update(state)
    return json.dumps([value]).encode()


HEADER = b"  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n"


def tcp(family=4, addr=None, listen=True):
    local = addr or ("00000000" if family == 4 else "0"*32)
    raw = HEADER.replace(b"rem_address", b"remote_address") if family == 6 else HEADER
    return raw + (" 0: " + local + ":1680 " + "0"*len(local) + ":0000 " + ("0A" if listen else "01") + " 00000000:00000000 00:00000000 00000000 0 0 1\n").encode()


def rejects(fn, text=None):
    try:
        fn()
    except Exception as error:
        if text:
            assert text in str(error), (text, str(error))
        return str(error)
    raise AssertionError("EXPECTED_REFUSAL")


class Clock:
    def __init__(self): self.value = 10.0
    def now(self): return self.value
    def sleep(self, duration): self.value += duration


class Runner:
    def __init__(self, clock, pending=0, malformed=None):
        self.clock, self.pending, self.calls, self.guest_round = clock, pending, [], 0
        self.malformed = malformed
    def __call__(self, cmd, timeout, limit):
        assert 0 < timeout <= 3 and 0 < limit <= 262144
        assert cmd[0] == "docker" and CID in cmd
        self.calls.append(list(cmd))
        if cmd[1] == "inspect": return inspect()
        if cmd[1] == "logs": return b"bounded guest console\n"
        assert cmd[:4] == ["docker", "exec", CID, "cat"]
        if cmd[-1] == "/proc/net/tcp":
            self.guest_round += 1
            return tcp(listen=self.guest_round > self.pending)
        assert cmd[-1] == "/proc/net/tcp6"
        return self.malformed if self.malformed is not None else tcp(6)


def case(name, fn):
    fn()
    RESULTS.append({"name": name, "status": "PASS"})


def parser_cases():
    assert validate_inspect04(inspect(), CID, RUN)["Running"] is True
    rejects(lambda: validate_inspect04(inspect(), "c"*64, RUN), "IDENTITY")
    rejects(lambda: validate_inspect04(inspect(Pid=True), CID, RUN), "SCHEMA")
    rejects(lambda: validate_inspect04(inspect(OOMKilled="false"), CID, RUN), "SCHEMA")
    rejects(lambda: validate_inspect04(inspect().replace(b'"Running": true', b'"Running": false, "Running": true'), CID, RUN), "SCHEMA")
    rejects(lambda: validate_inspect04(b" "*65537, CID, RUN), "SIZE")
    assert parse_tcp04(tcp(), 4)["ready"]
    assert not parse_tcp04(tcp(addr="0100007F"), 4)["ready"]
    assert not parse_tcp04(tcp(6), 6)["ready"]  # IPv6 alone does not prove IPv4 Docker route.
    assert not parse_tcp04(tcp(6, "0"*24+"01000000"), 6)["ready"]
    rejects(lambda: parse_tcp04(tcp().replace(b"0A", b"ZZ"), 4), "SCHEMA")
    rejects(lambda: parse_tcp04(b"x"*262145, 4), "SIZE")


def readiness_cases():
    clock = Clock(); runner = Runner(clock, pending=1); records=[]
    proof = await_ready04(DockerProbe04(CID, RUN, runner), records.append, clock.now, clock.sleep)
    assert proof["observations"] == 2 and len(records) == 2 and proof["txBytes"] == 0
    assert records[-1]["ready"] and records[-1]["state"]["containerId"] == CID
    assert runner.calls.count(["docker", "inspect", CID]) == 4
    for abnormal in ({"OOMKilled":True}, {"Error":"guest failure"}):
        probe = DockerProbe04(CID, RUN, lambda *args:inspect(**abnormal))
        seen=[];rejects(lambda:await_ready04(probe, seen.append, clock.now, clock.sleep), "NOT_HEALTHY")
        assert seen[-1]["kind"] == "READINESS_REFUSED"
    def slow(cmd, timeout, limit):
        data = runner(cmd, timeout, limit)
        if cmd[1] == "exec": clock.value += 31
        return data
    rejects(lambda:await_ready04(DockerProbe04(CID, RUN, slow), lambda x:None, clock.now, clock.sleep), "DEADLINE")
    clock = Clock()
    def regress(cmd, timeout, limit):
        if cmd[1] == "exec": clock.value -= 1
        return Runner(clock)(cmd, timeout, limit)
    rejects(lambda:await_ready04(DockerProbe04(CID, RUN, regress), lambda x:None, clock.now, clock.sleep), "CLOCK")


class FakeSocket:
    def __init__(self, values, close_error=False): self.values=list(values);self.close_error=close_error;self.closed=0;self.timeout=None
    def settimeout(self, value): self.timeout=value
    def recv(self, bound):
        assert bound == 4096
        value=self.values.pop(0)
        if isinstance(value, Exception): raise value
        return value
    def close(self):
        self.closed += 1
        if self.close_error: raise OSError("CLOSE_FAILURE")
    def send(self, *args): raise AssertionError("UNAUTHORIZED_TX")
    sendall=send


def stream_cases():
    for fault in (ConnectionRefusedError("REFUSED"), socket.timeout("CONNECT_TIMEOUT")):
        clock=Clock(); runner=Runner(clock); calls=[]; progress={}
        def connector(*args): calls.append(args);raise fault
        rejects(lambda:bootstrap_stream04(DockerProbe04(CID,RUN,runner),lambda x:None,lambda b:None,lambda:False,progress,connector,clock.now,clock.sleep),str(fault))
        assert len(calls)==1 and progress["connectAttempts"]==1 and progress["txBytes"]==0
    clock=Clock(); runner=Runner(clock); sock=FakeSocket([b"data",b""],close_error=True); calls=[];chunks=[];progress={}
    def connector(*args): calls.append(args);return sock
    rejects(lambda:bootstrap_stream04(DockerProbe04(CID,RUN,runner),lambda x:None,chunks.append,lambda:False,progress,connector,clock.now,clock.sleep),"BOOTSTRAP_EOF")
    assert len(calls)==1 and chunks==[b"data"] and sock.closed==1 and progress["closeError"]=="CLOSE_FAILURE"
    stopped=[False];sock=FakeSocket([socket.timeout("IDLE"),b"fresh"]);calls=[];progress={}
    def connector(*args):calls.append(args);return sock
    def sink(data): assert data==b"fresh";stopped[0]=True
    bootstrap_stream04(DockerProbe04(CID,RUN,runner),lambda x:None,sink,lambda:stopped[0],progress,connector,clock.now,clock.sleep)
    assert len(calls)==1 and sock.timeout==.5 and progress["lastPollStatus"]=="DATA" and progress["txBytes"]==0


def cleanup_cases():
    clock=Clock();calls=[]
    def fail(cmd, timeout, limit):calls.append(cmd);raise RuntimeError("PROBE_FAILURE")
    probe=DockerProbe04(CID,RUN,fail);stops=[]
    def capture(value):assert value["originalReason"]=="BOOTSTRAP_EOF";raise OSError("DISK_FAILURE")
    def stop(cid):stops.append(cid);raise OSError("STOP_FAILURE")
    result=stop_owned04(probe,"BOOTSTRAP_EOF",False,capture,stop,clock.now)
    assert result["originalReason"]=="BOOTSTRAP_EOF" and stops==[CID] and not result["stopSucceeded"]
    assert all(not x["ok"] for x in result["preStop"]["probes"].values()) and len(result["cleanupErrors"])==2
    assert result["preStop"]["externalStopRequested"]is False and result["preStop"]["controllerStopInitiated"]is True and result["preStop"]["stopTrigger"]=="BOOTSTRAP_EOF"
    assert calls[0]==["docker","inspect",CID] and calls[-1][-1]==CID


def sidecar_case():
    scratch=ROOT/"planning/integration03/runtime/.mock-bootstrap04"
    assert not scratch.exists();scratch.mkdir()
    try:
        journal=ReadinessJournal04(scratch/"readiness.jsonl")
        journal.append({"kind":"READINESS","txBytes":0});rejects(lambda:journal.append({"x":"x"*17000}),"BOUND");journal.close()
        assert len((scratch/"readiness.jsonl").read_text().splitlines())==1
    finally:
        shutil.rmtree(scratch)


if __name__=="__main__":
    case("strict inspect and both TCP-family parsers",parser_cases)
    case("passive readiness, abnormal-state and clock/deadline guards",readiness_cases)
    case("single connect, EOF/refusal/initialtimeout terminal, idle polling0TX",stream_cases)
    case("all prestop probes/stop/capture faults preserve originalerror",cleanup_cases)
    case("exclusive bounded readiness sidecar and scratch cleanup",sidecar_case)
    files=[pathlib.Path(__file__),pathlib.Path(__file__).with_name("bootstrap04.py"),pathlib.Path(__file__).with_name("runtime04.py")]
    report={"status":"PASS_OFFLINE_ONLY","noDockerAPAndroidNetworkBuild":True,"cases":RESULTS,"files":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files},"oldActualCause":"UNKNOWN; synthetic readiness test is not a reproduction","removedScratch":"planning/integration03/runtime/.mock-bootstrap04"}
    suffix=sys.argv[1]if len(sys.argv)>1 else"01";assert re.fullmatch(r"[0-9]{2}",suffix);target=E/("builder-mock"+suffix+".json");target.open("x").write(json.dumps(report,indent=2)+"\n");print(json.dumps(report))
