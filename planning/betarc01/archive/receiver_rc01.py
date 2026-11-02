#!/usr/bin/env python3
"""Explicit complete-byte receiver for bounded UNUSED/CLOSED native archival.

All used generations need a separately Root-approved original-source capsule.
This helper never mutates Android, retries, grants rights or declares flight.
"""
from pathlib import Path
import argparse
import base64
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from planning.nativejournal17.receiver17 import cold_originals, native_tar, MAGIC
from planning.betarc01.archive.common_rc01 import canonical, decode, need, original_ref, repository, sha
from planning.betarc01.archive.closed_sources import closed_sources


def qualify_active(scan, manifest, proofs):
    originals = []
    for generation, journal in sorted(scan["journals"].items()):
        need(journal["unresolvedIntent"] is None, "UNRESOLVED_CURRENT_ACTIVE_BLOCKS_ARCHIVE")
        if journal["raw"] == MAGIC:
            proof = {"disposition": "UNUSED", "sourceClosedStatusBound": False,
                     "reason": "EXACT_MAGIC_NO_INPUT_HISTORY"}
            proof_sha = sha(canonical(proof))
            disposition = "UNUSED"
            status_bound = False
        else:
            proof = proofs.get(generation)
            need(proof is not None and proof["disposition"] == "CLOSED_VERIFIED" and
                 proof["sourceClosedStatusBound"] is True and
                 proof["APKSHA256"] == manifest["native"]["APK_SHA256"] and
                 proof["sourceSHA256"] == manifest["native"]["sourceSHA256"] and
                 all(proof[key] == journal[key] for key in ("bytes", "sha256", "records", "head")),
                 "USED_CURRENT_BYTES_REQUIRE_ORIGINAL_APPROVED_CLOSED_SOURCE")
            proof_sha = proof["proofSHA256"]
            disposition = "CLOSED_VERIFIED"
            status_bound = True
        originals.append({"generation": generation, "bytes": journal["bytes"],
                          "sha256": journal["sha256"], "records": journal["records"],
                          "disposition": disposition, "proofSHA256": proof_sha,
                          "sourceClosedStatusBound": status_bound})
    need(1 <= len(originals) <= 8, "COMPLETE_ACTIVE_SET1_8")
    return originals


def receive(backup, cold_proof_path, cold_proof_sha, new_source, expected_head,
            *, approved_sources, node):
    repo = repository()
    proof_path = Path(cold_proof_path).absolute()
    proof_raw = original_ref({"path": str(proof_path), "bytes": proof_path.stat().st_size,
                              "sha256": cold_proof_sha}, 32768, within=repo / "evidence")
    proof = decode(proof_raw)
    manifest, _ = cold_originals(proof, backup)
    scan = native_tar(backup, proof["backupSHA256"])
    need(re.fullmatch(r"[a-f0-9]{64}", new_source) and
         (expected_head == "ROOT" or re.fullmatch(r"[a-f0-9]{64}", expected_head)),
         "EXPLICIT_NEW_SOURCE_AND_EXTERNAL_HEAD")
    need(new_source == manifest["native"]["sourceSHA256"], "SAME_INSTALLED_SOURCE_FOR_ROTATION")
    if expected_head == "ROOT":
        need(len(scan["journals"]) == 8 and all(j["raw"] == MAGIC for j in scan["journals"].values()),
             "INITIAL_ROOT_ENROLL_EXACT8_UNUSED_ONLY")
    proofs = closed_sources(approved_sources, node)
    originals = qualify_active(scan, manifest, proofs)
    report = {
        "format": "aeris-journal17-independent-full-byte-receiver", "version": 1,
        "status": "COMPLETE_COLD_BACKUP_AND_ORIGINAL_GENERATIONS_VERIFIED_NOT_FLIGHT",
        "package": manifest["native"]["package"], "oldAPKSHA256": manifest["native"]["APK_SHA256"],
        "oldSourceSHA256": manifest["native"]["sourceSHA256"], "newSourceSHA256": new_source,
        "backupSHA256": scan["tarSHA256"], "backupBytes": scan["tarBytes"],
        "coldProofSHA256": cold_proof_sha, "expectedHostRegistryHead": expected_head,
        "allPrivateFiles": len(scan["files"]), "allPrivateLogicalBytes": scan["logicalBytes"],
        "totalInputArchiveIndexControlBytes": scan["inputBytes"], "originals": originals,
        "authorityRestorable": False, "actualFlightAccepted": False,
        "rootApprovedUsedSources": approved_sources,
        "closedSourceQualification": "ORIGINAL_ADB_STATUS_ACK_P256_RC_CLOCK_REPLAY_NOT_ASSERTED_DISPOSITION"
    }
    raw = canonical(report) + b"\n"
    need(len(raw) <= 32768, "RECEIVER_REPORT32K")
    lines = ["AERIS_JOURNAL_LIFECYCLE17\t1", "package\t" + manifest["native"]["package"],
             "oldAPK\t" + manifest["native"]["APK_SHA256"],
             "oldSource\t" + manifest["native"]["sourceSHA256"], "newSource\t" + new_source,
             "backup\t" + scan["tarSHA256"] + "\t" + str(scan["tarBytes"]),
             "receiver\t" + sha(raw), "cold\t" + cold_proof_sha, "expectedHead\t" + expected_head]
    lines += ["generation\t" + row["generation"] + "\t" + str(row["bytes"]) + "\t" +
              row["sha256"] + "\t" + row["disposition"] + "\t" + row["proofSHA256"]
              for row in originals]
    plan = ("\n".join(lines + ["end", ""])).encode("ascii")
    need(len(plan) <= 16384, "PLAN16K")
    return raw, plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--cold-proof", required=True)
    parser.add_argument("--cold-proof-sha", required=True)
    parser.add_argument("--new-source", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--node", required=True)
    parser.add_argument("--approved-source", action="append", default=[],
                        help="JSON exact path/bytes/sha256 reference approved independently by Root")
    args = parser.parse_args()
    refs = [decode(value) for value in args.approved_source]
    report, plan = receive(args.backup, args.cold_proof, args.cold_proof_sha, args.new_source,
                           args.expected_head, approved_sources=refs, node=args.node)
    result = {"format": "aeris-journal17-fresh-cold-receiver-result", "version": 1,
              "reportBase64": base64.b64encode(report).decode(), "reportSHA256": sha(report),
              "planBase64": base64.b64encode(plan).decode(), "planSHA256": sha(plan),
              "readOnly": True, "actorsStarted": False, "authorityRestorable": False}
    raw = canonical(result) + b"\n"
    need(len(raw) <= 65536, "RECEIVER_CLI64K")
    sys.stdout.buffer.write(raw)
