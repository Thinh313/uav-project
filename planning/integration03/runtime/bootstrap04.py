"""Rig-only passive bootstrap admission and owned pre-stop diagnostics.

No MAVLink writer, authority or application policy. Dependencies are injectable for
offline verification. Readiness proves a current guest listener, not end-to-end
TCP health or the cause of a historical failure.
"""
import hashlib
import ipaddress
import json
import math
import os
import re
import selectors
import socket
import subprocess
import time

CID04 = re.compile(r"[a-f0-9]{64}\Z")
RUN04 = re.compile(r"s[a-f0-9]{20}\Z")
STAMP04 = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,9})?Z\Z")


class ProbeError04(RuntimeError):
    pass


class ReadinessJournal04:
    """Small append-only sidecar, never called for MAVLink/data frames."""
    def __init__(self, path):
        self.out = open(path, "xb")
        self.records = self.bytes = 0

    def append(self, value):
        line = json.dumps(value, separators=(",", ":"), allow_nan=False).encode() + b"\n"
        if len(line) > 16384 or self.records >= 256 or self.bytes+len(line) > 2*1024*1024:
            raise ProbeError04("READINESS_JOURNAL_BOUND")
        self.out.write(line)
        self.out.flush()
        os.fsync(self.out.fileno())
        self.records += 1
        self.bytes += len(line)

    def close(self):
        self.out.close()


def bounded_command04(args, timeout, limit):
    """Bound output while reading; kill only this newly created command process."""
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3 or type(limit) is not int or not 1 <= limit <= 262144:
        raise ProbeError04("PROBE_COMMAND_BOUND")
    p = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    output = bytearray()
    end = time.monotonic() + timeout
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ)
    try:
        while sel.get_map():
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise ProbeError04("PROBE_COMMAND_TIMEOUT")
            for key, _ in sel.select(remaining):
                b = os.read(key.fileobj.fileno(), min(4096, limit + 1 - len(output)))
                if not b:
                    sel.unregister(key.fileobj)
                else:
                    output.extend(b)
                    if len(output) > limit:
                        raise ProbeError04("PROBE_COMMAND_OUTPUT_BOUND")
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise ProbeError04("PROBE_COMMAND_TIMEOUT")
        code = p.wait(timeout=remaining)
        if code != 0:
            raise ProbeError04("PROBE_COMMAND_EXIT:" + str(code))
        return bytes(output)
    finally:
        sel.close()
        p.stdout.close()
        if p.poll() is None:
            p.kill()
        p.wait(timeout=1)


def _integer04(v, low, high):
    return type(v) is int and low <= v <= high


def validate_inspect04(raw, cid, run):
    if not isinstance(cid, str) or not isinstance(run, str) or not CID04.fullmatch(cid) or not RUN04.fullmatch(run):
        raise ProbeError04("OWNED_CONTAINER_BINDING")
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 65536:
        raise ProbeError04("INSPECT_SIZE")
    try:
        def unique(pairs):
            obj = {}
            for key, item in pairs:
                if key in obj:
                    raise ValueError("DUPLICATE_JSON_KEY")
                obj[key] = item
            return obj
        value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=unique,
                           parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        if not isinstance(value, list) or len(value) != 1:
            raise ValueError()
        q = value[0]
        labels = q["Config"]["Labels"]
        if q["Id"] != cid or q["Name"] != "/aeris-integration03" or labels.get("aeris.task") != "integration03" or labels.get("aeris.run") != run:
            raise ProbeError04("OWNED_CONTAINER_IDENTITY_MISMATCH")
        s = q["State"]
        if any(type(s[k]) is not bool for k in ("Running", "OOMKilled", "Paused", "Restarting")):
            raise ValueError()
        if s["Status"] not in ("created", "running", "paused", "restarting", "removing", "exited", "dead") or not _integer04(s["Pid"], 0, 2**31-1) or not _integer04(s["ExitCode"], 0, 255):
            raise ValueError()
        if type(s["Error"]) is not str or len(s["Error"].encode()) > 4096 or any(type(s[k]) is not str or not STAMP04.fullmatch(s[k]) for k in ("StartedAt", "FinishedAt")):
            raise ValueError()
        if s["Running"] and (s["Pid"] <= 0 or s["Status"] != "running" or s["Paused"] or s["Restarting"]):
            raise ValueError()
        if not _integer04(q["RestartCount"], 0, 2**31-1):
            raise ValueError()
        return {"containerId": cid, "name": q["Name"], "run": run,
                "RestartCount": q["RestartCount"],
                **{k: s[k] for k in ("Running", "Status", "Pid", "ExitCode", "OOMKilled", "Error", "StartedAt", "FinishedAt", "Paused", "Restarting")}}
    except ProbeError04:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, AttributeError):
        raise ProbeError04("INSPECT_SCHEMA") from None


def parse_tcp04(raw, family):
    if family not in (4, 6) or not isinstance(raw, bytes) or not 1 <= len(raw) <= 262144:
        raise ProbeError04("GUEST_TCP_SIZE_OR_FAMILY")
    try:
        text = raw.decode("ascii", "strict")
        lines = text.splitlines()
        if not 1 <= len(lines) <= 4097 or not re.fullmatch(r"\s*sl\s+local_address\s+(?:rem|remote)_address\s+st\s+.*", lines[0]):
            raise ValueError()
        matches = []
        digits = 8 if family == 4 else 32
        endpoint = re.compile(r"([A-Fa-f0-9]{" + str(digits) + r"}):([A-Fa-f0-9]{4})\Z")
        for line in lines[1:]:
            p = line.split()
            if not p:
                continue
            if len(p) < 10 or not re.fullmatch(r"[0-9]+:", p[0]) or not endpoint.fullmatch(p[1]) or not endpoint.fullmatch(p[2]) or not re.fullmatch(r"[A-Fa-f0-9]{2}", p[3]):
                raise ValueError()
            address, port = p[1].split(":")
            if int(port, 16) != 5760 or p[3].upper() != "0A":
                continue
            # proc prints each host-order32-bit word; the guest is pinned x86_64.
            b = b"".join(bytes.fromhex(address[i:i+8])[::-1] for i in range(0, len(address), 8))
            ip = ipaddress.ip_address(b)
            mapped = getattr(ip, "ipv4_mapped", None)
            reachable_bind = not ip.is_loopback and not (mapped and mapped.is_loopback)
            matches.append({"family": family, "address": str(ip), "port": 5760,
                            "state": "LISTEN", "nonLoopbackBind": reachable_bind,
                            "ipv4PublishedRouteCandidate": family == 4 and reachable_bind})
        return {"family": family, "rows": len(lines)-1, "listeners": matches,
                "ready": any(x["ipv4PublishedRouteCandidate"] for x in matches),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    except (ValueError, UnicodeError):
        raise ProbeError04("GUEST_TCP_SCHEMA") from None


class DockerProbe04:
    def __init__(self, cid, run, runner=bounded_command04):
        if not isinstance(cid, str) or not isinstance(run, str) or not CID04.fullmatch(cid) or not RUN04.fullmatch(run):
            raise ProbeError04("OWNED_CONTAINER_BINDING")
        self.cid, self.run, self.runner = cid, run, runner

    def inspect(self, timeout=2):
        return validate_inspect04(self.runner(["docker", "inspect", self.cid], timeout, 65536), self.cid, self.run)

    def guest(self, timeout=2):
        return [parse_tcp04(self.runner(["docker", "exec", self.cid, "cat", "/proc/net/tcp" + suffix], timeout, 262144), family)
                for suffix, family in (("", 4), ("6", 6))]

    def logs(self, timeout=2):
        raw = self.runner(["docker", "logs", "--timestamps", "--tail", "80", self.cid], timeout, 65536)
        return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode("utf-8", "replace")}


def await_ready04(probe, record, clock=time.monotonic, sleep=time.sleep,
                  stopped=lambda: False, timeout=30):
    if type(timeout) not in (int, float) or not 0 < timeout <= 30:
        raise ProbeError04("READINESS_BUDGET")
    last = None
    def tick():
        nonlocal last
        value = clock()
        if type(value) not in (int, float) or not math.isfinite(value) or last is not None and value < last:
            raise ProbeError04("READINESS_CLOCK_REGRESSION_OR_TYPE")
        last = value
        return value
    start = tick()
    deadline = start + timeout
    def require_healthy(state, n, reason):
        if not state["Running"] or state["OOMKilled"] or state["Error"] or state["RestartCount"]:
            try:
                record({"kind": "READINESS_REFUSED", "n": n, "reason": reason,
                        "state": state, "hostMonoNs": str(int(tick()*1e9)), "txBytes": 0})
            except Exception:
                pass
            raise ProbeError04(reason)
    for n in range(1, 122):
        now = tick()
        if stopped():
            raise ProbeError04("READINESS_CONTROLLER_STOP")
        if now >= deadline:
            raise ProbeError04("BOOTSTRAP_GUEST_READINESS_TIMEOUT")
        probe_started = now
        before = probe.inspect(min(2, deadline-now))
        require_healthy(before, n, "BOOTSTRAP_AP_NOT_HEALTHY_RUNNING")
        now = tick()
        if now < last or now >= deadline:
            raise ProbeError04("READINESS_CLOCK_OR_DEADLINE")
        guest = probe.guest(min(2, (deadline-now)/2))
        now = tick()
        if now < last or now >= deadline:
            raise ProbeError04("READINESS_CLOCK_OR_DEADLINE")
        after = probe.inspect(min(2, deadline-now))
        ended = tick()
        if ended < now or ended >= deadline:
            raise ProbeError04("READINESS_CLOCK_OR_DEADLINE")
        require_healthy(after, n, "BOOTSTRAP_AP_EXIT_OR_ABNORMAL_STATE")
        if before["Pid"] != after["Pid"] or before["StartedAt"] != after["StartedAt"]:
            raise ProbeError04("BOOTSTRAP_AP_EXIT_OR_RESTART")
        observation = {"kind": "READINESS", "n": n, "hostBeforeMonoNs": str(int(probe_started*1e9)),
                       "hostAfterMonoNs": str(int(ended*1e9)), "elapsedMs": (ended-start)*1000,
                       "state": after, "guest": guest,
                       "ready": any(x["ready"] for x in guest),
                       "ipv6PublishedRoute": "UNKNOWN_NOT_ACCEPTED_WITHOUT_IPV4", "txBytes": 0}
        record(observation)
        after_record = tick()
        if after_record >= deadline:
            raise ProbeError04("READINESS_CLOCK_OR_DEADLINE")
        if observation["ready"]:
            return {"status": "OWNED_GUEST_LISTENER_READY", "containerId": probe.cid,
                    "run": probe.run, "pid": after["Pid"], "observedAtMono": ended,
                    "deadlineMono": deadline, "observations": n, "txBytes": 0}
        sleep(min(.25, deadline-after_record))
    raise ProbeError04("READINESS_OBSERVATION_BOUND")


def bootstrap_stream04(probe, record, chunk, stopped, progress,
                       connector=socket.create_connection, clock=time.monotonic,
                       sleep=time.sleep, on_socket=lambda value: None):
    ready = await_ready04(probe, record, clock, sleep, stopped)
    if not ready["observedAtMono"] <= clock() < ready["deadlineMono"] or stopped():
        raise ProbeError04("READINESS_EXPIRED_BEFORE_SINGLE_CONNECT")
    progress.update({"status": "CONNECTING_ONCE", "connectAttempts": 1, "txBytes": 0})
    sock = None
    primary_error = None
    try:
        sock = connector(("127.0.0.1", 5941), 3)
        on_socket(sock)
        sock.settimeout(.5)
        progress.update({"status": "CONNECTED_READONLY", "connectedAtMonoNs": str(int(clock()*1e9))})
        while not stopped():
            try:
                data = sock.recv(4096)
            except socket.timeout:
                # Passive absence only: no reconnect, writer or mutation retry.
                progress["lastPollStatus"] = "READ_IDLE_TIMEOUT"
                continue
            if not data:
                raise ProbeError04("BOOTSTRAP_EOF")
            progress.update({"lastReadAtMonoNs": str(int(clock()*1e9)), "lastPollStatus": "DATA"})
            chunk(data)
    except BaseException as error:
        primary_error = error
        raise
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception as error:
                progress["closeError"] = str(error)[:240]
                if primary_error is None:
                    raise ProbeError04("BOOTSTRAP_CLOSE:" + str(error)[:200]) from error


def capture_pre_stop04(probe, original_reason, requested_stop, clock=time.monotonic):
    """Read every diagnostic independently; failures cannot mask the first cause."""
    try:
        stamp = str(int(clock()*1e9))
        clock_error = None
    except Exception as error:
        stamp, clock_error = None, str(error)[:240]
    result = {"format": "aeris-bootstrap04-prestop", "version": 1,
              "hostMonoNs": stamp, "clockError": clock_error, "containerId": probe.cid,
              "run": probe.run, "originalReason": original_reason,
              "externalStopRequested": bool(requested_stop), "controllerStopInitiated": True,
              "stopTrigger": original_reason or("EXTERNAL_STOP_REQUEST" if requested_stop else "CONTROLLER_SHUTDOWN"), "probes": {}}
    for name, fn in (("inspect", probe.inspect), ("guest", probe.guest), ("logs", probe.logs)):
        try:
            result["probes"][name] = {"ok": True, "value": fn(2)}
        except Exception as error:
            result["probes"][name] = {"ok": False, "error": str(error)[:240]}
    return result


def stop_owned04(probe, original_reason, requested_stop, capture,
                 stopper, clock=time.monotonic):
    diagnostics = capture_pre_stop04(probe, original_reason, requested_stop, clock)
    errors = []
    try:
        capture(diagnostics)
    except Exception as error:
        errors.append("PRESTOP_CAPTURE:" + str(error)[:240])
    attempted = False
    try:
        # CID came from this launch; never resolve a name or stop a replacement.
        if not CID04.fullmatch(probe.cid):
            raise ProbeError04("STOP_OWNED_ID_REQUIRED")
        attempted = True
        stopper(probe.cid)
    except Exception as error:
        errors.append("OWNED_STOP:" + str(error)[:240])
    return {"originalReason": original_reason, "stopAttempted": attempted,
            "stopSucceeded": attempted and not any(x.startswith("OWNED_STOP:") for x in errors),
            "cleanupErrors": errors, "preStop": diagnostics}
