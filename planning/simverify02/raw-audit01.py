#!/usr/bin/env python3
"""Read-only cold audit of one retained simulator run; never starts a runtime.

Usage from the project root:
    python3 -B planning/simverify02/raw-audit01.py \
        --receiver .local/simverify02/receiver04 \
        --run rfebb3af9a261492cabd8 \
        --out evidence/simverify02/raw-audit01.json

The output is created exclusively. A valid prefix is not a completed flight.
The original-model byte oracle and physical training validity are not checked here.
"""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import struct
import subprocess
import time
import zlib


def sha256_file(filename):
    digest = hashlib.sha256()
    with filename.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_wal(filename):
    header = struct.Struct("<BBHIIQQ")
    chain = bytes(32)
    sequence = 0
    kinds = collections.Counter()
    previous_frame = None
    first_frame = None
    gaps = 0
    phase = "HEADER"
    with filename.open("rb") as source:
        assert source.read(8) == b"AERISJ04", "WAL magic is invalid."
        while True:
            raw = source.read(header.size)
            if not raw:
                break
            assert len(raw) == header.size, "WAL header is torn."
            kind, flags, reserved, frame, length, index, stamp = header.unpack(raw)
            assert length <= 16384, "WAL payload exceeds its bound."
            body = source.read(length)
            tail = source.read(36)
            assert len(body) == length and len(tail) == 36, "WAL payload is torn."
            assert index == sequence and flags == reserved == 0, "WAL sequence or flags differ."
            digest = hashlib.sha256(chain + raw + body).digest()
            assert struct.unpack_from("<I", tail)[0] == zlib.crc32(raw + body), "WAL CRC differs."
            assert tail[4:] == digest, "WAL hash chain differs."
            kinds[kind] += 1
            chain = digest
            sequence += 1
            if kind == 1:
                assert phase == "HEADER", "Duplicate WAL header."
                phase = "RX"
            elif kind == 2:
                assert phase == "RX", "RX is out of order."
                gaps += int(previous_frame is not None and frame != previous_frame + 1)
                first_frame = frame if first_frame is None else first_frame
                previous_frame = frame
                phase = "INTENT"
            elif kind == 3:
                assert phase == "INTENT", "INTENT is out of order."
                assert frame == previous_frame, "INTENT frame differs."
                size, snapshot_size = struct.unpack_from("<II", body)
                assert len(body) == size + snapshot_size + 8, "INTENT envelope differs."
                row = json.loads(body[8:8 + size])
                assert row["frame"] == frame and row["rate"] == 1200, "INTENT identity differs."
                assert row["hostReceiveNs"] <= row["computeStartNs"] <= row["computeEndNs"] <= stamp
                phase = "SENT"
            elif kind == 4:
                assert phase == "SENT" and frame == previous_frame, "SENT frame is out of order."
                sent = json.loads(body)
                assert sent["returnedBytes"] == sent["expectedBytes"], "Local UDP return differs."
                phase = "RX"
            elif kind == 6:
                assert phase == "RX", "CLOSE interrupts a pending frame."
                phase = "CLOSED"
            else:
                raise AssertionError("Unexpected WAL record kind: " + str(kind))
    return {
        "prefixIntegrity": "VALID_PREFIX",
        "records": sequence,
        "recordKinds": {str(key): value for key, value in kinds.items()},
        "firstFrame": first_frame,
        "lastFrame": previous_frame,
        "admittedFrames": kinds[2],
        "frameGaps": gaps,
        "phaseAtEOF": phase,
        "closeRecords": kinds[6],
        "headSha256": chain.hex(),
        "completeCapture": phase == "CLOSED",
        "interpretation": "CRC, chain and admitted frame order are checked. No CLOSE means the capture is incomplete.",
    }


def audit_ap(filename, admitted_frames):
    event = struct.Struct("<QQIIQQQQq")
    seen = {kind: bytearray(admitted_frames) for kind in (11, 13, 14)}
    tails = collections.Counter()
    duplicates = 0
    with filename.open("rb") as source:
        magic, capacity, count, failed, size = struct.unpack("<8s4Q", source.read(40))
        assert magic == b"AERISD02" and count <= capacity and size == 64
        assert failed == 0, "The AP trace reports a recorder failure."
        source.seek(4096)
        for index in range(count):
            raw = source.read(64)
            assert len(raw) == 64, "The AP trace is torn."
            row = event.unpack(raw)
            assert row[0] == index and row[4] <= row[5], "AP trace sequence or timing differs."
            if row[2] in seen:
                if row[1] < admitted_frames:
                    duplicates += int(bool(seen[row[2]][row[1]]))
                    seen[row[2]][row[1]] = 1
                else:
                    tails[row[2]] += 1
    return {
        "events": count,
        "capacity": capacity,
        "recorderFailures": failed,
        "requiredFrames": admitted_frames,
        "missingStageRecords": {str(kind): rows.count(0) for kind, rows in seen.items()},
        "duplicateStageRecords": duplicates,
        "unadmittedTailStageRecords": {str(kind): value for kind, value in tails.items()},
        "interpretation": "Stages 11, 13 and 14 correlate actual AP servo send, sensor receive and parse. Extra tails are retained, not added to admitted model time.",
    }


def audit_mavlink(filename, run):
    kinds = collections.Counter()
    modes = collections.Counter()
    versions = set()
    last_fields = {}
    parameters = {}
    arms = 0
    rc = 0
    bracket_count = 0
    sequence = 0
    session_ids = set()
    for line in filename.open():
        row = json.loads(line)
        assert row["run"] == run and row["index"] == sequence + 1, "Node capture run or sequence differs."
        sequence += 1
        kinds[row["kind"]] += 1
        if row.get("session"):
            session_ids.add(row["session"])
        data = row["data"]
        if row["kind"] == "AP_RX_DECODED":
            assert data["system"] == 42 and data["component"] == 1
            fields = data["fields"]
            last_fields[data["id"]] = fields
            if data["id"] == 0:
                modes[(fields["custom_mode"], bool(fields["base_mode"] & 128))] += 1
            elif data["id"] == 148:
                versions.add(fields["flight_sw_version"])
            elif data["id"] == 22:
                parameters[fields["param_id"]] = {key: fields[key] for key in ("param_value", "param_type")}
        elif row["kind"] == "GCS_TX_REQUEST" and data["id"] == 76 and data["fields"].get("command") == 400:
            arms += 1
        elif row["kind"] == "RC_TX_INTENT":
            rc += 1
        elif row["kind"] == "CLOCK_NODE_BACKEND_BRACKET" and data["status"] == "MATCHED":
            assert int(data["nodeMinusBackendLowNs"]) == int(data["nodeSendNs"]) - int(data["backendReceiveNs"])
            assert int(data["nodeMinusBackendHighNs"]) == int(data["nodeReceiveNs"]) - int(data["backendSendNs"])
            assert int(data["nodeMinusBackendLowNs"]) <= int(data["nodeMinusBackendHighNs"])
            bracket_count += 1
    return {
        "records": sequence,
        "recordKinds": dict(kinds),
        "sessionIds": sorted(session_ids),
        "targetSystem": 42,
        "targetComponent": 1,
        "heartbeatModes": [{"mode": mode, "armed": armed, "observations": count} for (mode, armed), count in modes.items()],
        "firmwareWords": sorted(versions),
        "firmwareVersions": [f"{word >> 24}.{(word >> 16) & 255}.{(word >> 8) & 255}" for word in sorted(versions)],
        "command400Intents": arms,
        "rcIntents": rc,
        "matchedNodeBackendBrackets": bracket_count,
        "typedFailsafeParameters": {name: parameters.get(name) for name in ("FS_GCS_ENABLE", "FS_GCS_TIMEOUT", "FS_OPTIONS", "MAV_GCS_SYSID")},
        "lastObservedGPS": last_fields.get(24),
        "lastObservedEKF": last_fields.get(193),
        "lastObservedHome": last_fields.get(242),
        "interpretation": "These are retained observations before disconnect. They are not current freshness or flight acceptance.",
    }


def audit_mounts(run_root, launch):
    try:
        process = subprocess.run(["docker", "inspect", launch["containerId"]], capture_output=True, text=True, timeout=5, check=True)
        info = json.loads(process.stdout)[0]
        origin = "READ_ONLY_DOCKER_INSPECT_OF_RETAINED_CONTAINER"
    except Exception:
        info = json.loads((run_root / "container-before-stop.json").read_text())
        if isinstance(info, list):
            info = info[0]
        origin = "SAVED_CONTAINER_BEFORE_STOP_ONLY"
    assert info["Id"] == launch["containerId"] and info["Image"] == launch["imageId"]
    labels = info["Config"]["Labels"]
    assert labels["aeris.task"] == "simhand01" and labels["aeris.run"] == run_root.name
    mounts = {row["Destination"]: row for row in info["Mounts"]}
    assert mounts["/aeris"]["RW"] is False and mounts["/aeris/arducopter"]["RW"] is False
    binary = pathlib.Path(mounts["/aeris/arducopter"]["Source"])
    assert sha256_file(binary) == launch["apSha256"]
    receiver = run_root.parents[3]
    assert pathlib.Path(mounts["/aeris"]["Source"]) == receiver / "runtime/sitl"
    assert binary == receiver / "runtime/sim32-instrument01-build/ardupilot/build/sitl/bin/arducopter"
    return {"provenance": origin, "id": info["Id"], "image": info["Image"], "state": info["State"], "mounts": info["Mounts"], "labels": labels, "mountedBinarySha256": launch["apSha256"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receiver", default=".local/simverify02/receiver04")
    parser.add_argument("--run", default="rfebb3af9a261492cabd8")
    parser.add_argument("--out", default="evidence/simverify02/raw-audit01.json")
    args = parser.parse_args()
    receiver = pathlib.Path(args.receiver).resolve()
    run_root = receiver / "evidence/simhand01/runs" / args.run
    assert run_root.parent == receiver / "evidence/simhand01/runs"
    start = time.monotonic()
    launch = json.loads((run_root / "launch.json").read_text())
    closure = json.loads((run_root / "closure.json").read_text())
    backend = json.loads((run_root / "backend-result.json").read_text())
    before = {name: sha256_file(run_root / name) for name in ("frames.wal", "ap-timing.bin", "mavlink.jsonl", "launch.json", "closure.json", "backend-result.json")}
    wal = audit_wal(run_root / "frames.wal")
    ap = audit_ap(run_root / "ap-timing.bin", wal["admittedFrames"])
    mavlink = audit_mavlink(run_root / "mavlink.jsonl", args.run)
    mounts = audit_mounts(run_root, launch)
    after = {name: sha256_file(run_root / name) for name in before}
    assert before == after, "An input changed during the cold audit."
    assert wal["admittedFrames"] == backend["frames"]
    report = {
        "format": "aeris-simverify02-cold-raw-audit",
        "version": 1,
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run": args.run,
        "receiver": str(receiver),
        "status": "INCOMPLETE_NOT_ACCEPTED",
        "scriptSha256": sha256_file(pathlib.Path(__file__)),
        "inputSha256": before,
        "inputsUnchangedDuringAudit": True,
        "wal": wal,
        "actualAPTrace": ap,
        "mavlink": mavlink,
        "mounts": mounts,
        "backendResult": backend,
        "closure": closure,
        "operatorReviewPresent": (run_root / "operator-review.json").exists(),
        "stopRequestPresent": (run_root / "stop-request.json").exists(),
        "originalModelByteOracle": "NOT_RUN",
        "manualFlightAcceptance": "NOT_CHECKED_NO_ARM_OR_MANUAL_INPUT",
        "fullG1Accepted": False,
        "physicalPhoneHeraOrProjectorAcceptance": "NOT_CHECKED",
        "scope": "Read-only verification of admitted raw lineage and actual AP stage correlation, not complete mission or pacing acceptance.",
        "explanation": "The admitted prefix is intact, but the run failed at its deadline without a WAL CLOSE or operator review. The recorded real-time factor is about 0.919977. This is not a passing flight.",
        "elapsedSeconds": time.monotonic() - start,
    }
    with pathlib.Path(args.out).open("x") as output:
        json.dump(report, output, ensure_ascii=False, indent=2)
        output.write("\n")
    print(json.dumps({"status": report["status"], "frames": wal["admittedFrames"], "closeRecords": wal["closeRecords"], "armIntents": mavlink["command400Intents"], "rtf": backend["activeReceiveRTF"], "inputsUnchanged": True, "out": args.out}))


if __name__ == "__main__":
    main()
