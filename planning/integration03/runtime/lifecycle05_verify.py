"""Verify retained Builder receipts; does not execute a controller or a case."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
from pathlib import Path
from lifecycle05_cases import CASES05

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/"evidence/integration03-lifecycle05/builder"
selected={i:E/("corrected-"+str(i).zfill(2)+".json"if i in(4,10,18)else"new-"+str(i).zfill(2)+".json")for i in range(len(CASES05))}
checked=[]
for i,p in selected.items():
    r=json.loads(p.read_text());c=r["receipts"].get("closure.json",{});events=r["events"]
    assert r["scenario"]==CASES05[i] and r["syntheticOnly"]is True
    assert r["containmentGuardsRestoredAfterQuiescence"]is True
    assert r["exception"]is None and not r["workerErrors"]
    assert all(not v for v in r["leaksBeforeHarnessCleanup"].values())
    assert r["bootstrapConnects"]<=1 and r["socketTXBytes"]==0
    seal_line=next(x for x in r["stdout"].splitlines()if x.startswith("CLOSURE05 "))
    seal=json.loads(seal_line[len("CLOSURE05 "):]);assert seal["exitCode"]==r["exitCode"]
    assert r["exitCode"]==(0 if i==0 else 2)
    assert seal["status"]==("CLOSED_SUCCESSFULLY"if i==0 else"CLOSED_WITH_FAILURE")
    assert all(e["args"][-1]=="a"*64 for e in events if e["name"]=="COMMAND"and e["args"][:2]==["docker","stop"])
    if i==0:
        assert c["stopped"]and c["error"]is None and c["lastHeartbeat"][1]==0 and c["lastLand"][1]==1
    if i in(1,2,3,4,12):
        assert c["firstFailure05"]["source"]=="BOOTSTRAP"
    if i==3:
        state=r["receipts"]["prestop-diagnostics04.json"]["probes"]["inspect"]["value"]
        assert state["Running"]is False and state["OOMKilled"]is True and state["ExitCode"]==137
    if i==4:
        assert not c["stopped"]and not r["receipts"]["prestop-diagnostics04.json"]["probes"]["inspect"]["ok"]
    if i==5:assert r["bootstrapConnects"]==0 and c["error"]=="OWNED_CONTAINER_IDENTITY_MISMATCH"
    if i==6:
        assert any(e["name"]=="PEER_POPEN"for e in events)
        assert any(e["name"]=="FILE_CLOSE"and e["file"]=="peer-console.txt"for e in events)
    if i==7:assert c["error"]=="OBSERVER_THREAD_START_FAILURE05"
    if i==8:assert c["firstFailure05"]["source"]=="OBSERVER"and c["error"]=="OBSERVER_CRC"
    if i in(9,10,11):assert c["error"]=="RESOURCE_OR_DEADLINE"
    if i==11:assert c["everArmed"]and c["lastLand"][1]==2
    if i==12:assert c["error"]=="BOOTSTRAP_EOF"and any(x["reason"]=="SECONDARY_LOGS_FAILURE05"for x in c["secondaryFailures05"])
    if i==13:assert c["error"]=="OBSERVER_CRC"and any(x["reason"]=="SECONDARY_POLL_FAILURE05"for x in c["secondaryFailures05"])
    if i in(14,15):
        assert seal["closurePersisted"]is False and seal["firstFailure"]["source"]=="CLOSURE_PERSISTENCE"
        assert "CLOSED None"not in r["stdout"]
    if i==16:assert any(x.startswith("PRESTOP_CAPTURE:")for x in c["cleanupErrors"])and any(x.startswith("OWNED_STOP:")for x in c["cleanupErrors"])
    if i==17:assert any(e["name"]=="PEER_KILL"for e in events)and any(x.startswith("PEER_WAIT:")for x in c["cleanupErrors"])
    if i==18:assert c["cleanupErrors"]and any(e["name"]=="COMMAND"and e["args"][:2]==["docker","stop"]for e in events)
    checked.append({"name":CASES05[i]["name"],"receipt":str(p.relative_to(ROOT)),"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"status":"PASS_SYNTHETIC_ONLY","exitCode":r["exitCode"]})
report={"status":"PASS_BUILDER_OFFLINE_LIFECYCLE_SCOPE","distinctSelectedScenarios":len(checked),"builderControllerExecutions":26,"accounting":{"preFixExecutions":4,"firstNewExecutions":19,"targetedFixtureReruns":3,"notCreditedAsProductFailures":["pre-console01: premature existing-run fixture","new-10: safe-ground stop preempted deadline","new-18: bind-only close fault preempted AP lifecycle","new-04: absent-container stop fixture responded success"]},"results":checked,"remaining":"Independent QA and actual M1 I01-I10 are not represented by these injected results."}
(E/"builder-verification01.json").open("x").write(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:report[k]for k in("status","distinctSelectedScenarios","builderControllerExecutions")}))
