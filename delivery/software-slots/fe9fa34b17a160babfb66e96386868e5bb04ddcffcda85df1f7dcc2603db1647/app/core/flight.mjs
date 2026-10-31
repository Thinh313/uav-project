/** Local rehearsal state machine. No MAVLink encoding, radio or network transport. */
const terminal = new Set(['observed', 'rejected', 'timed-out']);
const modes = new Set(['HOLD', 'AUTO', 'RTL']);
const identity = (id, session) => typeof id === 'string' && id.length > 0 && typeof session === 'string' && session.length > 0;
export class RehearsalFlight {
  constructor({ aircraftId = 'SIM-001', sessionId = 'rehearsal-1', freshnessMs = 3000, timeoutMs = 5000 } = {}) {
    if (!identity(aircraftId, sessionId) || !Number.isFinite(freshnessMs) || freshnessMs <= 0 || !Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error('Invalid session/configuration');
    Object.assign(this, { aircraftId, sessionId, freshnessMs, timeoutMs });
    this.telemetry = null; this.command = null; this.events = []; this.sequence = 0; this.lastClock = -Infinity;
  }
  clock(now) {
    if (!Number.isFinite(now) || now < this.lastClock) throw new Error('Clock must be finite and monotonic');
    this.lastClock = now;
  }
  event(type, now, detail = {}) {
    this.events.push({ sequence: ++this.sequence, atMs: now, aircraftId: this.aircraftId, sessionId: this.sessionId, type, ...detail });
    // Rehearsal event retention is bounded. A production append-only recorder is deferred.
    if (this.events.length > 2000) this.events.shift();
  }
  isFresh(now) { return !!this.telemetry && now >= this.telemetry.receivedAtMs && now - this.telemetry.receivedAtMs < this.freshnessMs; }
  receiveTelemetry(t, now) {
    this.clock(now);
    if (!t || t.aircraftId !== this.aircraftId || t.sessionId !== this.sessionId) return false;
    // M0 samples use the same monotonic clock as the local adapter. Remote clocks need mapping in M2.
    if (!Number.isFinite(t.sampleMs) || t.sampleMs < 0 || t.sampleMs > now || !modes.has(t.mode)) return false;
    for (const key of ['altitude', 'speed', 'battery']) if (typeof t[key] !== 'number' || !Number.isFinite(t[key])) return false;
    if (t.battery < 0 || t.battery > 100 || t.altitude < 0 || t.speed < 0) return false;
    if (this.telemetry && t.sampleMs <= this.telemetry.sampleMs) return false;
    this.telemetry = { ...t, receivedAtMs: now };
    this.reconcile(now);
    return true;
  }
  request(mode, now) {
    this.clock(now); this.tick(now);
    if (!modes.has(mode)) throw new Error('Chế độ diễn tập không được hỗ trợ.');
    if (!this.isFresh(now)) throw new Error('Telemetry đã cũ hoặc chưa có. Khôi phục dữ liệu trước khi gửi lệnh.');
    if (this.command && !terminal.has(this.command.state)) throw new Error('Một lệnh đang chờ kết quả.');
    if (this.telemetry.mode === mode) throw new Error('Phương tiện đã ở chế độ này.');
    this.command = { id: `${this.sessionId}:${this.sequence + 1}`, mode, state: 'sent', sentAtMs: now, ackAtMs: null, deadlineMs: now + this.timeoutMs, aircraftId: this.aircraftId, sessionId: this.sessionId };
    this.event('command-sent', now, { commandId: this.command.id, requestedMode: mode });
    return { ...this.command };
  }
  ack({ commandId, aircraftId, sessionId, result }, now) {
    this.clock(now); this.tick(now);
    const c = this.command;
    if (!c || terminal.has(c.state) || c.id !== commandId || aircraftId !== this.aircraftId || sessionId !== this.sessionId) return false;
    if (!['accepted', 'in-progress', 'rejected'].includes(result)) return false;
    if (c.state === result) return false;
    if (c.state === 'accepted' && result === 'in-progress') return false;
    c.state = result; c.ackAtMs = now;
    this.event(`command-${result}`, now, { commandId: c.id });
    // An earlier sample cannot certify execution; wait for a newer observation after ACK.
    return true;
  }
  reconcile(now) {
    const c = this.command;
    if (!c || !['accepted', 'in-progress'].includes(c.state)) return;
    if (now >= c.deadlineMs) { this.tick(now); return; }
    if (this.isFresh(now) && this.telemetry.sampleMs > c.ackAtMs && this.telemetry.mode === c.mode) {
      c.state = 'observed'; this.event('command-observed', now, { commandId: c.id, observedMode: this.telemetry.mode });
    }
  }
  tick(now) {
    this.clock(now);
    const c = this.command;
    if (c && !terminal.has(c.state) && now >= c.deadlineMs) {
      c.state = 'timed-out'; this.event('command-timed-out', now, { commandId: c.id });
    }
  }
  exportLog() { return { format: 'aeris-rehearsal-events', version: 1, operational: false, aircraftId: this.aircraftId, sessionId: this.sessionId, retentionLimit: 2000, events: this.events.map(e => ({ ...e })) }; }
}
