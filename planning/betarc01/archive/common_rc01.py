"""Bounded original references for explicit Root-approved administrative replay.

This module supplies no live observation, authority, retry, repair or acceptance.
An expected capsule digest is an external administrative trust input; a digest
stored inside an untrusted capsule is never used as its own approval.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import stat

HASH = re.compile(r"[a-f0-9]{64}")
GEN = re.compile(r"[a-f0-9]{32}")
MAX_CAPSULE = 32768
MAX_OPTIONS = 256 * 1024


def need(value, name):
    if not value:
        raise ValueError("BETARC01_ARCHIVE_" + name)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            need(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NONFINITE_JSON")))


def repository():
    return Path(__file__).resolve().parents[3]


def regular(path, maximum, *, within=None):
    path = Path(path).absolute()
    need(path == path.resolve() and not any(p.is_symlink() for p in (path, *path.parents)),
         "NO_SYMLINK_OR_DOT_PATH")
    if within is not None:
        need(path.is_relative_to(Path(within).resolve()), "ORIGINAL_REFERENCE_SCOPE")
    info = path.stat()
    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= maximum,
         "REGULAR_SINGLE_LINK_BOUND")
    with path.open("rb") as source:
        before = os.fstat(source.fileno())
        raw = source.read(maximum + 1)
        after = os.fstat(source.fileno())
    need(len(raw) == info.st_size and
         (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns) ==
         (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns),
         "ORIGINAL_CHANGED_DURING_READ")
    return raw


def original_ref(ref, maximum, *, within=None):
    need(type(ref) is dict and set(ref) == {"path", "bytes", "sha256"} and
         type(ref["path"]) is str and Path(ref["path"]).is_absolute() and
         type(ref["bytes"]) is int and 0 < ref["bytes"] <= maximum and
         type(ref["sha256"]) is str and HASH.fullmatch(ref["sha256"]),
         "EXPLICIT_ORIGINAL_REF")
    raw = regular(ref["path"], maximum, within=within)
    need(len(raw) == ref["bytes"] and sha(raw) == ref["sha256"], "ORIGINAL_REF_BYTES_SHA")
    return raw


def source_request(ref):
    root = repository()
    raw = original_ref(ref, MAX_CAPSULE, within=root / "evidence/betarc01")
    value = decode(raw)
    need(type(value) is dict and set(value) == {
        "format", "version", "status", "authorityRestorable", "candidatePath",
        "candidateSHA256", "caseRoot", "androidEvidenceRoot", "productRoot", "optionsRef"
    }, "ROOT_CAPSULE_SCHEMA")
    need(value["format"] == "aeris-betarc01-native-cold-replay-request" and
         type(value["version"]) is int and value["version"] == 1 and
         value["status"] == "UNVERIFIED_REPLAY_REQUEST_NOT_AUTHORITY" and
         value["authorityRestorable"] is False and HASH.fullmatch(value["candidateSHA256"]),
         "ROOT_CAPSULE_IDENTITY")
    case = Path(value["caseRoot"])
    candidate = Path(value["candidatePath"])
    need(case.is_absolute() and case == case.resolve() and case.is_dir() and
         case.parent in (root / "evidence/betarc01", root / "evidence/nativejournal17"),
         "EXACT_PRIOR_CASE_SCOPE")
    need(candidate == (root / "evidence/nativejournal17/candidates" / value["candidateSHA256"])
         and candidate.is_dir(), "EXACT_PRIOR_CANDIDATE_SCOPE")
    android = Path(value["androidEvidenceRoot"])
    product = Path(value["productRoot"])
    need(android.is_absolute() and product.is_absolute() and
         android == android.resolve() and product == product.resolve() and
         android.parent == product.parent and android.parent.parent == case / "sessions" and
         product.name == "product" and android.is_dir() and product.is_dir(),
         "EXACT_PRIOR_ANDROID_PRODUCT_SCOPE")
    options_raw = original_ref(value["optionsRef"], MAX_OPTIONS, within=case)
    options = decode(options_raw)
    need(type(options) is dict and set(options) == {
        "reference", "descriptor", "productRoot", "sourceSeal", "reviews"
    } and options["productRoot"] == str(product), "ORIGINAL_COLD_REPLAY_OPTIONS")
    need(options["descriptor"].get("candidateSHA256") == value["candidateSHA256"] and
         options["descriptor"].get("native", {}).get("package") == "vn.rtr.aeris.betasim09",
         "OPTIONS_CANDIDATE_AND_PACKAGE")
    return value, options, raw


def approved_capsule(ref):
    root = repository()
    raw = original_ref(ref, MAX_CAPSULE, within=root / "evidence/betarc01")
    value = decode(raw)
    need(type(value) is dict and set(value) == {
        "format", "version", "status", "authorityRestorable", "requestRef", "replayRef", "inventoryRef"
    } and value["format"] == "aeris-betarc01-root-approved-closed-native-source" and
         type(value["version"]) is int and value["version"] == 2 and
         value["status"] == "ROOT_COLD_VERIFIED_NATIVE_SIGNED_SOURCE_NOT_FLIGHT_CERTIFICATION" and
         value["authorityRestorable"] is False, "ROOT_APPROVED_CAPSULE_V2_SCHEMA")
    request, options, _ = source_request(value["requestRef"])
    return request, options, raw, value


def file_fact(path):
    path = Path(path).absolute()
    need(path == path.resolve() and not any(p.is_symlink() for p in (path, *path.parents)),
         "INVENTORY_NO_SYMLINK")
    info = path.stat()
    need(stat.S_ISREG(info.st_mode) and info.st_size <= 192 * 2 ** 20, "INVENTORY_REGULAR_FILE192M")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    after = path.stat()
    need((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
         "INVENTORY_ORIGINAL_CHANGED_DURING_HASH")
    return {"path": str(path), "bytes": info.st_size, "mode": stat.S_IMODE(info.st_mode),
            "sha256": digest.hexdigest()}


def verify_inventory(inventory, request, request_sha):
    need(type(inventory) is dict and set(inventory) == {
        "format", "version", "caseRoot", "candidateSHA256", "requestSHA256", "files"
    } and inventory["format"] == "aeris-betarc01-offline-original-replay-inventory" and
         type(inventory["version"]) is int and inventory["version"] == 1 and
         inventory["caseRoot"] == request["caseRoot"] and
         inventory["candidateSHA256"] == request["candidateSHA256"] and
         inventory["requestSHA256"] == request_sha and type(inventory["files"]) is list and
         1 <= len(inventory["files"]) <= 4096, "ORIGINAL_REPLAY_INVENTORY_SCHEMA")
    seen = set(); total = 0
    for row in inventory["files"]:
        need(type(row) is dict and set(row) == {"path", "bytes", "mode", "sha256"} and
             row["path"] not in seen and Path(row["path"]).is_relative_to(repository()),
             "ORIGINAL_REPLAY_INVENTORY_EXACT_SCOPE")
        seen.add(row["path"]); total += row["bytes"]
        need(total <= 1024 * 2 ** 20 and file_fact(row["path"]) == row,
             "ORIGINAL_REPLAY_FILE_BYTES_MODE_SHA_UNCHANGED")
    required = {request["optionsRef"]["path"],
                str(Path(request["caseRoot"]) / "reports/product-descriptor-01.json"),
                str(Path(request["productRoot"]) / "journal/workspace.jsonl"),
                str(Path(request["productRoot"]).parent / "native-closed.tar"),
                str(Path(request["caseRoot"]) / "reports/owner-terminal.json"),
                str(Path(request["caseRoot"]) / "guardian/closure.json")}
    need(required <= seen, "REQUIRED_ORIGINAL_SOURCE_FILES_INVENTORIED")
    return seen
