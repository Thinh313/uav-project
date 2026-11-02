#!/usr/bin/env python3
"""Fresh-process replay of a Root-approved prior native closed-source capsule.

The subprocess is a bounded offline verifier, never an Android/AP/runtime actor.
No trusted modules from another candidate may be cached in this process.
"""
from pathlib import Path
import argparse
import json
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from planning.betarc01.archive.common_rc01 import source_request, canonical, decode, need, original_ref, regular, repository, sha, file_fact
from planning.betarc01.archive.offline_capture import capture


def original_inventory(request, options, manifest, request_sha):
    case = Path(request['caseRoot']); product = Path(request['productRoot'])
    terminal_path = case / 'reports/owner-terminal.json'
    terminal = decode(regular(terminal_path, 4096, within=case))
    need(terminal.get('status') == 'UI_WORKLOAD_CLOSED_AWAITING_INDEPENDENT_BETA_ACCEPTANCE' and
         terminal.get('candidateSHA256') == request['candidateSHA256'] and
         terminal.get('normalCompletedClosureClaimed') is True and terminal.get('flightAcceptance') is False,
         'ORIGINAL_NORMAL_CASE_TERMINAL_NOT_EXPECTED_FAULT_DISPOSAL')
    closure_path = case / 'guardian/closure.json'; closure = decode(regular(closure_path, 65536, within=case))
    need(closure.get('exit') == 0 and closure.get('failure') is None and
         closure.get('durablyDrained') is True and closure.get('exceptionalPhysicalDisposal') is False,
         'ORIGINAL_GUARDIAN_NORMAL_PHYSICAL_CLOSURE')
    descriptor_path = case / 'reports/product-descriptor-01.json'
    need(decode(regular(descriptor_path, 32768, within=case)) == options['descriptor'],
         'OPTIONS_EXACT_ORIGINAL_PRODUCT_DESCRIPTOR')
    paths = {terminal_path, closure_path, descriptor_path, Path(request['optionsRef']['path']),
             Path(options['reference']['descriptorPath']), product.parent / 'native-closed.tar',
             case / 'reports/product-clock-proofs.jsonl', product / 'journal/workspace.jsonl',
             case / ('diagnostics/product-' + options['descriptor']['context']['run']) / 'launch.json'}
    for base in [Path(request['androidEvidenceRoot']), case / 'reports', product / 'journal',
                 product / 'state', product / 'reports']:
        for path in base.rglob('*'):
            need(not path.is_symlink(), 'ORIGINAL_INVENTORY_NO_SYMLINK')
            if path.is_file(): paths.add(path)
    for name in manifest['sourceSHA256']: paths.add(Path(request['candidatePath']) / 'source' / name)
    for name in manifest['productSourceSHA256']: paths.add(repository() / name)
    for name in manifest['externalFrozenSHA256']: paths.add(repository() / name)
    for name in ('candidate.json', 'candidate.sha256', 'native.apk', 'native-inputs.tar.gz',
                 'native-build-receipt.json', 'qa-gate.json'):
        paths.add(Path(request['candidatePath']) / name)
    need(len(paths) <= 4096, 'ORIGINAL_INVENTORY_FILES4096')
    rows = [file_fact(path) for path in sorted(paths)]
    need(sum(row['bytes'] for row in rows) <= 1024 * 2 ** 20, 'ORIGINAL_INVENTORY_TOTAL1G')
    return {'format': 'aeris-betarc01-offline-original-replay-inventory', 'version': 1,
            'caseRoot': request['caseRoot'], 'candidateSHA256': request['candidateSHA256'],
            'requestSHA256': request_sha, 'files': rows}


def replay(ref, node):
    capsule, options, raw = source_request(ref)
    repo = repository()
    candidate = Path(capsule["candidatePath"])
    need(not any(n == "aeris_runtime" or n.startswith("aeris_runtime.") for n in sys.modules),
         "FRESH_PRIOR_CANDIDATE_PROCESS_REQUIRED")
    os.environ.update(AERIS_REPOSITORY_ROOT=str(repo), AERIS_CANDIDATE_DIR=str(candidate),
                      AERIS_CANDIDATE_SHA256=capsule["candidateSHA256"], PYTHONDONTWRITEBYTECODE="1")
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(candidate / "source"), str(repo)]
    from aeris_runtime.candidate import load
    from aeris_runtime.product_native09 import verify_originals
    from aeris_runtime.once_reader import read_ref, read_receipts
    manifest = load(candidate, capsule["candidateSHA256"])
    expected_native = manifest["native"]
    descriptor = options["descriptor"]
    need(descriptor["native"] == expected_native and
         descriptor["candidateSHA256"] == capsule["candidateSHA256"], "PRIOR_DESCRIPTOR_NATIVE_SOURCE")
    own_files = [Path(__file__), Path(__file__).with_name("common_rc01.py"),
                 Path(__file__).with_name("verify_used.mjs")]
    for path in own_files:
        need(manifest["productSourceSHA256"].get(str(path.relative_to(repo))) == sha(path.read_bytes()),
             "SOURCE_HELD_ARCHIVE_REPLAY_CODE:" + path.name)
    android = Path(capsule["androidEvidenceRoot"])
    original_proof = verify_originals(android, manifest)
    need(original_proof["status"] == "ORIGINAL_PRODUCT_NATIVE_OBSERVATIONS_VERIFIED_NOT_FLIGHT_ACCEPTANCE",
         "PRIOR_ORIGINAL_ADB_STATUS_ACK_REQUIRED")
    reference = options["reference"]
    path = Path(reference["descriptorPath"])
    closed_raw = regular(path, 16384, within=Path(capsule["caseRoot"]) / "reports")
    need(len(closed_raw) == reference["descriptorBytes"] and sha(closed_raw) == reference["descriptorSHA256"],
         "PRIOR_CLOSED_DESCRIPTOR_ORIGINAL_BYTES")
    closed = decode(closed_raw)
    request_rows = read_receipts(android, "request")
    for generation in closed["generations"]:
        need(generation["originalStoreRoot"] == str(android), "PRIOR_EXACT_ANDROID_STORE")
        observation = decode(read_ref(android, generation["originalObservationRef"]))
        need(observation in request_rows and observation["snapshotRef"] == generation["snapshotOriginalRef"],
             "CLOSED_OBSERVATION_IN_COMPLETE_ONCESTORE")
        regref = generation["registrationRootRef"]
        regpath = Path(capsule["caseRoot"]) / regref["path"]
        registration_raw = regular(regpath, 8192, within=Path(capsule["caseRoot"]) / "reports")
        need(regref["offset"] == 0 and len(registration_raw) == regref["bytes"] and
             sha(registration_raw) == regref["sha256"], "ORIGINAL_ROOT_REGISTRATION_WHOLE_FILE")
        registration = decode(registration_raw)
        enrolled = decode(read_ref(android, registration["originalObservationRef"]))
        need(enrolled in request_rows and enrolled["actualPID"] == generation["pid"],
             "ROOT_KEY_REGISTERED_FROM_GENUINE_PRIOR_OBSERVATION")
        enrolled_snapshot = decode(read_ref(android, enrolled["snapshotRef"]))
        need(enrolled_snapshot["processEpoch"] == generation["processEpoch"] and
             enrolled_snapshot["input"]["producerKeyId"] == generation["keyId"] and
             enrolled_snapshot["input"]["producerPublicKeyX509Base64"] == generation["publicKeyX509Base64"],
             "ROOT_ENROLLED_ORIGINAL_KEY_NOT_BUNDLE_KEY")
    for name, module in list(sys.modules.items()):
        if name == "aeris_runtime" or name.startswith("aeris_runtime."):
            origin = Path(getattr(module, "__file__", "")).resolve()
            need(origin.is_relative_to(candidate / "source/aeris_runtime") and
                 manifest["sourceSHA256"].get(str(origin.relative_to(candidate / "source"))) ==
                 sha(origin.read_bytes()), "PRIOR_LOADED_SOURCE_ORIGIN_SHA")
    node = Path(node)
    need(node.is_absolute() and node.is_file() and not node.is_symlink(), "EXPLICIT_NODE_EXECUTABLE")
    inventory = original_inventory(capsule, options, manifest, ref['sha256'])
    captured, stdout, stderr = capture(
        [str(node), str(Path(__file__).with_name("verify_used.mjs"))], canonical(options), cwd=repo)
    if captured['captureComplete'] is not True or captured['exit'] != 0 or stderr:
        error = ValueError("BETARC01_ARCHIVE_ORIGINAL_CRYPTO_RC_CLOCK_REPLAY_FAILED")
        error.offlineCapture = {"capture": captured,
            "stdoutBase64": __import__('base64').b64encode(stdout).decode(),
            "stderrBase64": __import__('base64').b64encode(stderr).decode()}
        raise error
    value = decode(stdout)
    need(value["status"] == "ORIGINAL_SIGNATURES_STATUS_REGISTRATION_RC_CLOCK_REPLAYED_NOT_FLIGHT" and
         value["candidateSHA256"] == capsule["candidateSHA256"] and
         value["sourceSHA256"] == expected_native["sourceSHA256"] and
         value["APKSHA256"] == expected_native["APK_SHA256"] and
         value["authorityRestorable"] is False and value["actorsStarted"] is False,
         "CRYPTO_REPLAY_EXACT_SCOPE")
    need(original_inventory(capsule, options, manifest, ref['sha256']) == inventory,
         "ORIGINAL_INVENTORY_UNCHANGED_DURING_OFFLINE_REPLAY")
    replay_value = {**value, "format": "aeris-betarc01-offline-original-native-replay", "version": 2,
            "sourceRequestSHA256": ref['sha256'], "originalInventorySHA256": sha(canonical(inventory) + b"\n"),
            "originalNativeObservationCount": original_proof["count"],
            "offlineNodeCapture": captured, "runtimeActorsStarted": False,
            "originalNodeResultBase64": __import__('base64').b64encode(stdout).decode(),
            "sourceVerifierSHA256": sha(Path(__file__).read_bytes()),
            "signatureVerifierSHA256": sha(Path(__file__).with_name("verify_used.mjs").read_bytes())}
    need(len(canonical(replay_value)) + 1 <= 65536, "OFFLINE_REPLAY_RECEIPT64K")
    return {"format": "aeris-betarc01-offline-original-source-results", "version": 2,
            "replay": replay_value, "inventory": inventory,
            "nodeStdoutBase64": __import__('base64').b64encode(stdout).decode(),
            "nodeStderrBase64": __import__('base64').b64encode(stderr).decode(),
            "rootApprovalNotIssuedByThisVerifier": True}



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capsule", required=True)
    parser.add_argument("--capsule-sha", required=True)
    parser.add_argument("--capsule-bytes", required=True, type=int)
    parser.add_argument("--node", required=True)
    args = parser.parse_args()
    try:
        value = replay({"path": args.capsule, "sha256": args.capsule_sha, "bytes": args.capsule_bytes}, args.node)
    except BaseException as error:
        value = {"format": "aeris-betarc01-offline-original-source-failure", "version": 2,
                 "status": "FAILED_PRESERVED_NO_ROOT_APPROVAL", "error": str(error),
                 "runtimeActorsStarted": False, "authorityRestorable": False,
                 "offlineCapture": getattr(error, "offlineCapture", None)}
        raw = canonical(value) + b"\n"
        need(len(raw) <= 2 * 1024 * 1024, "OFFLINE_FAILURE_OUTPUT2M")
        sys.stdout.buffer.write(raw)
        raise SystemExit(1)
    raw = canonical(value) + b"\n"
    need(len(raw) <= 2 * 1024 * 1024, "OFFLINE_REPLAY_OUTPUT2M")
    sys.stdout.buffer.write(raw)
