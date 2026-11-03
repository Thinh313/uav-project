#!/usr/bin/env python3
"""Root-only explicit maintenance entry; same owner/guards, never Activity/AP."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import sys
import time
import traceback

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--candidate", required=True); parser.add_argument("--candidate-sha", required=True)
parser.add_argument("--spec", required=True); parser.add_argument("--node", required=True)
parser.add_argument("--run", required=True)
parser.add_argument("--campaign-slot", required=True, choices=("m303",))
parser.add_argument("--storage-anchor", required=True); parser.add_argument("--storage-anchor-sha", required=True)
parser.add_argument("--inspect", action="store_true")
args = parser.parse_args()
repo = Path(__file__).resolve().parents[3]; candidate = Path(args.candidate).resolve()
os.environ.update(AERIS_REPOSITORY_ROOT=str(repo), AERIS_CANDIDATE_DIR=str(candidate),
                  AERIS_CANDIDATE_SHA256=args.candidate_sha, PYTHONDONTWRITEBYTECODE="1")
sys.path[:0] = [str(candidate / "source"), str(repo)]
from aeris_runtime.candidate import load
from aeris_runtime.entry import module_origin_receipt
from aeris_runtime.product_inputs import validate
from aeris_runtime.product_runtime import WorkbenchRuntime
from aeris_runtime.preview10 import preview
from planning.betarc01.archive.common_rc01 import need
from planning.betarc01.tar_profile_h7.maintenance import perform

manifest = load(candidate, args.candidate_sha); module_origin_receipt(candidate)
graph = validate(manifest["productInputClosure"])
entry = Path(__file__).resolve()
need(graph["pins"].get(str(entry.relative_to(repo))) == hashlib.sha256(entry.read_bytes()).hexdigest(),
     "EXACT_SOURCE_HELD_MAINTENANCE_ENTRY")
need(Path(args.node).is_absolute() and Path(args.node).is_file(), "EXPLICIT_NODE")
evidence = repo / "evidence/betarc01" / args.campaign_slot
forecast = preview(candidate, args.candidate_sha, evidence, repo / "planning/betarc01", Path(args.spec), seconds=180)
need(all(forecast[k] for k in ("metadataAdmitted", "artifactAdmitted", "diskAdmitted")),
     "PURE_MAINTENANCE_ADMISSION_NO_SLOT")
if args.inspect:
    print(json.dumps({"status": "MAINTENANCE_SOURCE_AND_PREVIEW_ONLY_NO_ACTORS", "forecast": forecast}))
    raise SystemExit(0)
owner = WorkbenchRuntime(candidate, args.candidate_sha, evidence=evidence,
                         planning=repo / "planning/betarc01", spec=args.spec, seconds=180)
owner.root.mkdir(exist_ok=False); stopped = False


def stop(sig, frame):
    global stopped
    stopped = True


def check():
    need(not stopped, "MAINTENANCE_TERMINATION")
    owner.check()


signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
try:
    owner.bootstrap(); case = owner.create_case(args.run, seconds=180); owner.start_writer()
    device = case["device"]; device.live_check = check
    device.wait_owned_ready(deadline_ns=time.monotonic_ns() + 60_000_000_000)
    device.prepare_content_reader(deadline_ns=time.monotonic_ns() + 30_000_000_000)
    result = perform(owner, case, args.storage_anchor, args.storage_anchor_sha, args.node,
                     deadline_ns=time.monotonic_ns() + 150_000_000_000)
    closure = owner.close_maintenance(); owner.close_guardian()
    owner.write("owner-terminal.json", {"format": "aeris-betarc01-maintenance-owner-terminal", "version": 1,
        "status": "NATIVE_MAINTENANCE_CLOSED_AWAITING_ROOT_REVIEW", "candidateSHA256": args.candidate_sha,
        "normalCompletedClosureClaimed": False, "maintenanceClosed": True,
        "originalPrivateBytesConserved": result["originalPrivateBytesConserved"],
        "activityStarted": False, "APStarted": False, "flightAcceptance": False,
        "authorityRestorable": False}, closing=True)
    print(json.dumps({"status": "NATIVE_MAINTENANCE_CLOSED_AWAITING_ROOT_REVIEW", "evidence": str(owner.root)}))
except BaseException as primary:
    try: owner.revoke_failure_ingress()
    except BaseException as secondary: primary.add_note("MAINTENANCE_INGRESS_SECONDARY:" + str(secondary))
    if owner.budget is not None:
        try: owner.persist_owner_error(traceback.format_exc())
        except BaseException as secondary: primary.add_note("MAINTENANCE_TRACE_SECONDARY:" + str(secondary))
        try: owner.fail_case(primary)
        except BaseException as secondary: primary.add_note("MAINTENANCE_DISPOSAL_SECONDARY:" + str(secondary))
    try:
        if not owner.closed: owner.close_guardian(failed=True)
    except BaseException as secondary: primary.add_note("MAINTENANCE_GUARDIAN_SECONDARY:" + str(secondary))
    print(json.dumps({"status": "FAILED_PRESERVED_MAINTENANCE_NOT_ACCEPTANCE", "error": str(primary),
                      "notes": getattr(primary, "__notes__", [])}))
    raise
