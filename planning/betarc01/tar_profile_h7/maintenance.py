"""One explicit owned native maintenance transaction, no Activity or flight.

The caller owns WorkbenchRuntime and physical lifecycle. Unknown administrative
outcomes remain failures; this function never resends a request or deletes data.
"""
from pathlib import Path
import base64
import json
import re
import secrets
import sys
import time

from planning.betarc01.archive.common_rc01 import canonical, decode, need, sha
from planning.betarc01.tar_profile_h7.archive import verify_storage
from planning.betarc01.tar_profile_h7.reader import native_tar


def enrolled_admin(owner, case, operation, *, deadline_ns):
    """Enrolled PREVIEW is durable; it is not the initial-enrollment special case."""
    from aeris_runtime.native17 import ADMIN_ACTION, ADMIN_COMPONENT, PACKAGE
    need(operation in ("PREVIEW", "APPLY") and case.get("maintenanceCurrentProofRC01") is not None,
         "ENROLLED_MAINTENANCE_PROOF_BEFORE_ADMIN")
    attempted = case.setdefault("maintenanceAdminAttemptsRC01", set())
    need(operation not in attempted, "ADMIN_NO_RETRY_AFTER_UNKNOWN_OUTCOME")
    attempted.add(operation); device = case["device"]; nonce = secrets.token_hex(16)
    plan = case["receiver17"]["plan"]
    args = ["shell", "am", "broadcast", "-a", ADMIN_ACTION, "-n", ADMIN_COMPONENT,
            "--es", "requestNonce", nonce, "--es", "operation", operation,
            "--es", "planBase64", base64.b64encode(plan).decode()]
    with device.live_log("AERIS_PRODUCT_STATUS", deadline_ns=deadline_ns) as rows:
        device.command(args, deadline_ns=deadline_ns, maximum_bytes=2048)
        command_ref = device.last_command_ref; ack = None
        for row in rows:
            if row.get("requestNonce") == nonce: ack = row; break
        need(type(ack) is dict, "ENROLLED_ADMIN_ORIGINAL_NONCE_ACK")
        ack_ref = device.observer.last_ref
        expected = "files/product-input-lifecycle17/request-" + nonce + ".json"
        status = "PREVIEW_ONLY_NO_ARCHIVE_OR_AUTHORITY" if operation == "PREVIEW" else "ARCHIVED_VERIFIED_NO_AUTHORITY"
        need(ack.get("path") == expected and ack.get("durableReceipt") is True and
             type(ack.get("bytes")) is int and 0 < ack["bytes"] <= 4096 and
             re.fullmatch(r"[a-f0-9]{64}", ack.get("registryHead", "")) and ack.get("status") == status,
             "ENROLLED_ADMIN_DURABLE_RECEIPT_SCOPE")
        raw = device.read_admin_receipt17(ack, nonce, deadline_ns=deadline_ns)
        receipt_ref = device.last_command["stdoutRef"]
        need(len(raw) == ack["bytes"] and sha(raw) == ack["sha256"], "ENROLLED_ADMIN_ORIGINAL_ACK_RECEIPT_SHA")
        value = decode(raw)
        need(value.get("format") == "aeris-native-journal17-administrative-receipt" and
             value.get("version") == 1 and value.get("requestNonce") == nonce and
             value.get("operation") == operation and value.get("package") == PACKAGE and
             value.get("status") == status and value.get("planSHA256") == case["receiver17"]["planSHA256"] and
             value.get("independentReceiverSHA256") == case["receiver17"]["reportSHA256"] and
             value.get("backupTARSHA256") == case["backup17"]["sha256"] and
             value.get("sourceSHA256") == owner.manifest["native"]["sourceSHA256"] and
             value.get("authorityRestorable") is False and value.get("flightAuthorityGranted") is False,
             "ENROLLED_ADMIN_EXACT_CASE_SOURCE_PLAN_RESULT")
    result = {"ACK": ack, "ACKRef": ack_ref, "commandRef": command_ref, "receiptRef": receipt_ref,
              "receipt": value, "registryHead": ack["registryHead"], "authorityRestorable": False}
    owner.write("maintenance-" + operation.lower() + ".json", result)
    if operation == "APPLY": case["admin17"] = result
    return result


def _conserved(before, after):
    prefix = "files/product-input01/"
    after_journals = {}
    for name, value in after["files"].items():
        if name.endswith(".aj02") and (name.startswith(prefix) or
                                      name.startswith("files/product-input-archives17/")):
            generation = name.rsplit("/", 1)[-1]
            need(generation not in after_journals, "CONSERVATION_UNIQUE_ORIGINAL_GENERATION")
            after_journals[generation] = value
    index = "files/product-input-registry17/highwater.aj17"
    for name, value in before["files"].items():
        if name.startswith(prefix):
            need(after_journals.get(name.rsplit("/", 1)[-1]) == value,
                 "MOVED_ORIGINAL_BYTES_CONSERVED")
        elif name == index:
            old, new = before["inputOriginals"][name], after["inputOriginals"].get(name)
            need(type(new) is bytes and new.startswith(old), "ORIGINAL_INDEX_APPEND_ONLY_PREFIX")
        else:
            need(after["files"].get(name) == value, "ALL_PRIOR_PRIVATE_ORIGINAL_BYTES_CONSERVED:" + name)
    need(not after["journals"], "ALL_DIRECT_GENERATIONS_ARCHIVED_NO_NEW_ACTIVITY")
    return True


def perform(owner, case, anchor_path, anchor_sha, node, *, deadline_ns):
    from aeris_runtime.rc01 import storage_anchor
    from aeris_runtime.native17 import preserve_legacy, PACKAGE
    from aeris_runtime.metadata_budget import capture_command, encoded
    need(not case.get("APStarted") and not case["resources"].children and
         case.get("companion") is None and case["device"].observer.process is None and
         not case.get("maintenanceAttemptedRC01"), "ONE_MAINTENANCE_WITHOUT_NATIVE_OR_AP_ACTORS")
    case["maintenanceAttemptedRC01"] = True
    anchor = storage_anchor(anchor_path, anchor_sha, owner.manifest)
    device = case["device"]
    preserve_legacy(owner, case, deadline_ns=deadline_ns)
    device.command(["shell", "am", "force-stop", PACKAGE], deadline_ns=deadline_ns)
    before_ref = device._cold_absence(deadline_ns)
    path_ref, digest_ref = device._installed_sha(owner.manifest["native"]["APK_SHA256"], deadline_ns)
    with device.budget.operation({"commands": 16385 + 16384, "command_receipts": 4096 + 8192}):
        backup = device._export_private(case["context"]["run"],
            case["root"] / "native-restart-metadata.tar", deadline_ns=deadline_ns,
            metadata_only=True, maximum_bytes=64 * 2 ** 20, product_full_closed=True)
    after_ref = device._cold_absence(deadline_ns)
    before_scan = native_tar(backup["path"], backup["sha256"])
    storage = verify_storage(backup["path"], backup["sha256"], anchor["registryHead"],
        source_candidate=owner.digest, archive_receivers=anchor["archiveReceivers"],
        approved_sources=anchor["approvedSources"], node=node)
    need(storage["pendingTransactions"] == 0 and storage["allArchiveReceiversVerified"] is True and
         1 <= storage["activeJournals"] <= 8, "COMPLETE_QUIESCENT_CURRENT_STORAGE")
    case["maintenanceCurrentProofRC01"] = storage
    proof = {"format": "aeris-journal17-original-cold-backup", "version": 1,
        "candidatePath": str(owner.candidate), "candidateSHA256": owner.digest,
        "androidEvidenceRoot": str(device.root), "coldBeforeRef": before_ref,
        "coldAfterRef": after_ref, "installedPathRef": path_ref, "installedSHARef": digest_ref,
        "backupCaptureRef": backup["captureReceiptRef"], "backupSHA256": backup["sha256"],
        "backupBytes": backup["bytes"]}
    proof_path = owner.root / "reports/native17-cold-backup-proof.json"
    owner.write(proof_path.name, proof)
    proof_sha = sha(encoded(proof))
    argv = [sys.executable, "-B", str(owner.repo / "planning/betarc01/tar_profile_h7/receiver.py"),
        "--backup", backup["path"], "--cold-proof", str(proof_path), "--cold-proof-sha", proof_sha,
        "--new-source", owner.manifest["native"]["sourceSHA256"],
        "--expected-head", anchor["registryHead"], "--node", str(node)]
    for ref in anchor["approvedSources"]:
        argv += ["--approved-source", canonical(ref).decode()]
    owner.budget.tick("commands")
    started = time.monotonic_ns()
    with owner.budget.operation({"commands": 65536 + 4096 + 8192,
                                 "external_task": 65536 + 4096 + 8192}):
        capture = capture_command(owner.budget, "external_task", argv, deadline_ns=deadline_ns,
                                  stdout_limit=65536, stderr_limit=4096)
    for stream in ("stdout", "stderr"):
        owner.budget.write("external_task", owner.root / ("reports/maintenance-receiver-" + stream + ".bin"),
                           capture[stream])
    owner.write("maintenance-receiver-capture.json", {"argv": argv, "startedHostNs": started,
        "finishedHostNs": time.monotonic_ns(), "exit": capture["exit"],
        "captureComplete": capture["captureComplete"], "pid": capture["pid"],
        "failure": None if capture["failure"] is None else str(capture["failure"]),
        "stdoutSHA256": sha(capture["stdout"]), "stderrSHA256": sha(capture["stderr"]),
        "authorityRestorable": False})
    need(capture["failure"] is None and capture["captureComplete"] is True and
         capture["exit"] == 0 and not capture["stderr"], "FRESH_RECEIVER_COMPLETE_NO_RETRY")
    result = decode(capture["stdout"])
    report_raw = base64.b64decode(result["reportBase64"], validate=True)
    plan_raw = base64.b64decode(result["planBase64"], validate=True)
    need(sha(report_raw) == result["reportSHA256"] and sha(plan_raw) == result["planSHA256"] and
         len(report_raw) <= 32768 and len(plan_raw) <= 4096 and result["readOnly"] is True and
         result["actorsStarted"] is False, "FRESH_RECEIVER_EXACT_REPORT_PLAN_BOUNDS")
    report = decode(report_raw)
    need(report["backupSHA256"] == backup["sha256"] and report["coldProofSHA256"] == proof_sha and
         report["expectedHostRegistryHead"] == anchor["registryHead"] and
         report["newSourceSHA256"] == owner.manifest["native"]["sourceSHA256"] and
         report["oldAPKSHA256"] == owner.manifest["native"]["APK_SHA256"] and
         report["rootApprovedUsedSources"] == anchor["approvedSources"], "EXACT_RECEIVER_CURRENT_ROOT_JOIN")
    owner.budget.write("external_task", owner.root / "reports/native17-receiver-original.json", report_raw)
    owner.budget.write("external_task", owner.root / "reports/native17-plan-original.txt", plan_raw)
    case["backup17"] = backup
    case["receiver17"] = {"raw": report_raw, "value": report, "plan": plan_raw,
        "reportSHA256": sha(report_raw), "planSHA256": sha(plan_raw)}
    # ADMIN never grants input/flight. Every operation is attempted at most once.
    enrolled_admin(owner, case, "PREVIEW", deadline_ns=deadline_ns)
    enrolled_admin(owner, case, "APPLY", deadline_ns=deadline_ns)
    device.command(["shell", "am", "force-stop", PACKAGE], deadline_ns=deadline_ns)
    device._cold_absence(deadline_ns)
    current = device.export17("after-migration", deadline_ns=deadline_ns)
    new_ref = {"path": str(owner.root / "reports/native17-receiver-original.json"),
               "bytes": len(report_raw), "sha256": sha(report_raw)}
    receivers = [*anchor["archiveReceivers"], new_ref]
    after = verify_storage(current["path"], current["sha256"], case["admin17"]["registryHead"],
        source_candidate=owner.digest, archive_receivers=receivers,
        approved_sources=anchor["approvedSources"], node=node)
    after_scan = native_tar(current["path"], current["sha256"], allow_empty_active=True)
    _conserved(before_scan, after_scan)
    need(after["pendingTransactions"] == 0 and after["activeJournals"] == 0 and
         after["archivedJournals"] == storage["archivedJournals"] + storage["activeJournals"],
         "NORMAL_MAINTENANCE_ARCHIVE_ALL_ORIGINALS")
    value = {"format": "aeris-betarc01-controlled-native-maintenance", "version": 1,
        "status": "ORIGINALS_ARCHIVED_WITHOUT_ACTIVITY_OR_FLIGHT_AWAITING_ROOT_REVIEW",
        "candidateSHA256": owner.digest, "registryHead": after["registryHead"],
        "nativeTARSHA256": current["sha256"], "archiveReceivers": receivers,
        "approvedSources": anchor["approvedSources"], "before": storage, "after": after,
        "originalPrivateBytesConserved": True, "pendingTransactions": 0,
        "activityStarted": False, "APStarted": False, "authorityRestorable": False,
        "flightAcceptance": False}
    case["maintenanceRC01"] = value
    owner.write("maintenance-rc01.json", value)
    case["maintenanceObserverClosureRC01"] = device.close_observer()
    return value
