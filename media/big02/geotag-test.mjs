/** Builder self-checks. QA's separate receiver/tests supply independent checks. */
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { bindCapture, validateSidecar, canonicalize } from './geotag.mjs';
import { buildCapturePackage, verifyCapturePackage, sha256, inspectJpeg } from './capture-package.mjs';
import { captureFixture, syntheticJpegBytes } from './geotag-fixtures.mjs';

const results = [];
const fixture = () => {
  const originalBytes = syntheticJpegBytes();
  const input = captureFixture();
  input.file = { name: 'original.jpg', mime: 'image/jpeg', sizeBytes: originalBytes.length, sha256: sha256(originalBytes) };
  return input;
};
const make = (input = captureFixture(), transferId = 'transfer-fixture-001') => buildCapturePackage({ input,
  originalBytes: syntheticJpegBytes(), transferId, senderId: 'rtr-host01-sender', receiverId: 'rtr-host01-evaluator' });
const pkgOnly = p => ({ manifest: p.manifest, originalBytes: p.originalBytes, sidecarBytes: p.sidecarBytes });
const receiver = () => ({ receiverId: 'rtr-host01-evaluator', expectedSenderId: 'rtr-host01-sender',
  seenTransferIds: new Set(), seenCaptureIds: new Set() });
const test = (name, run) => { try { run(); results.push({ name, status: 'PASS' }); }
  catch (error) { results.push({ name, status: 'FAIL', error: error.message }); } };
const negative = (name, mutate, reason) => test(name, () => {
  const input = fixture(); mutate(input); const result = bindCapture(input);
  assert.equal(result.status, 'QUARANTINE'); if (reason) assert.equal(result.reasons[0], reason);
  results[results.length] = { name: `${name}:retained-input`, status: 'EVIDENCE', input, observed: result };
});

test('synthetic JPEG structure and untouched original roundtrip', () => {
  const original = syntheticJpegBytes(); assert(inspectJpeg(original));
  const p = make(); assert.equal(p.status, 'PACKAGED');
  assert.deepEqual(p.originalBytes, Buffer.from(original));
  const accepted = verifyCapturePackage(pkgOnly(p), receiver()); assert.equal(accepted.status, 'ACCEPTED');
  assert.equal(accepted.actualImages, 0); assert.equal(accepted.receipt.authenticity, 'NOT_ATTESTED');
});
test('dateline interpolation, explicit units/datum/unknown lever arm', () => {
  const result = bindCapture(fixture()); assert.equal(result.status, 'BOUND');
  const p = result.sidecar.position;
  assert.equal(p.longitudeDeg, -180); assert.equal(p.latitudeDeg, 11); assert.equal(p.altitude.value, 105);
  assert.equal(p.altitude.datum, 'WGS84_ELLIPSOID'); assert.equal(p.timeUncertaintyMs, 5);
  assert.equal(p.cameraLeverArm, 'UNKNOWN'); assert.equal(p.targetLocation, 'NOT_DETERMINED');
  assert.equal(validateSidecar(result.sidecar).status, 'VALID');
});
negative('ACK alone', i => { i.event.kind = 'ACK'; }, 'CAPTURE_EVENT_REQUIRED_ACK_INSUFFICIENT');
negative('missing event', i => { delete i.event; }, 'INPUT_SCHEMA');
negative('missing original descriptor', i => { delete i.file; }, 'INPUT_SCHEMA');
negative('missing exposure time', i => { delete i.event.exposureMonotonicMs; });
negative('GNSS missing', i => { i.gnss = []; }, 'GNSS_TIMELINE_REQUIRED');
negative('GNSS stale', i => { i.gnss[0].monotonicMs = 0; }, 'GNSS_STALE');
negative('invalid GNSS fix', i => { i.gnss[1].quality = 'NO_FIX'; }, 'GNSS_QUALITY');
for (const key of ['runId', 'aircraftId', 'cameraId', 'bootId', 'clockDomain', 'feedId']) {
  negative(`wrong GNSS ${key}`, i => { i.gnss[0][key] = 'different'; }, 'GNSS_IDENTITY');
  negative(`wrong event ${key}`, i => { i.event[key] = 'different'; }, 'EVENT_IDENTITY');
}
negative('relative altitude cannot become MSL', i => { i.gnss[1].altitude.datum = 'RELATIVE_HOME'; }, 'ALTITUDE_DATUM_OR_UNITS');
negative('MSL without supported datum rejected', i => { i.gnss[1].altitude.datum = 'MSL'; }, 'ALTITUDE_DATUM_OR_UNITS');
negative('altitude feet rejected', i => { i.gnss[1].altitude.unit = 'ft'; }, 'ALTITUDE_DATUM_OR_UNITS');
negative('missing altitude is not zero', i => { delete i.gnss[1].altitude.value; }, 'ALTITUDE_DATUM_OR_UNITS');
negative('NaN rejected', i => { i.gnss[1].latitudeDeg = NaN; }, 'INPUT_NOT_BOUNDED_JSON');
negative('combined clock uncertainty bounded', i => { i.event.timeUncertaintyMs = 49; }, 'COMBINED_TIME_UNCERTAIN');
negative('outside timeline no extrapolation', i => { i.event.exposureMonotonicMs = 2100; }, 'EXPOSURE_OUTSIDE_GNSS_TIMELINE');
negative('reversed time', i => { i.gnss.reverse(); }, 'GNSS_TIME_ORDER');
negative('duplicate sample time', i => { i.gnss[1].monotonicMs = 1000; }, 'GNSS_TIME_ORDER');
negative('ambiguous antipodal interpolation', i => { i.gnss[0].longitudeDeg = 0; i.gnss[1].longitudeDeg = 180; });
negative('policy may tighten but never relax cap', i => { i.policy.maxSampleAgeMs = 1001; }, 'POLICY_INVALID_OR_EXCEEDS_HARD_CAP');
negative('input timeline cap', i => { i.gnss = Array.from({ length: 257 }, () => i.gnss[0]); }, 'GNSS_TIMELINE_REQUIRED');
test('result owns copied binding', () => { const i = fixture(); const r = bindCapture(i); i.event.captureId = 'mutated';
  assert.equal(r.sidecar.binding.event.captureId, 'synthetic-capture-001'); });
test('bounded JSON rejects cycles and shared exponential expansion', () => {
  const cycle = {}; cycle.self = cycle;
  assert.equal(bindCapture(cycle).status, 'QUARANTINE');
  let expanded = 'x'.repeat(1024); for (let i = 0; i < 18; i++) expanded = [expanded, expanded];
  assert.throws(() => canonicalize(expanded), /JSON_SIZE/);
});
test('tampered derived location rejected', () => { const r = bindCapture(fixture()); r.sidecar.position.longitudeDeg = 0;
  assert.equal(validateSidecar(r.sidecar).status, 'QUARANTINE'); });
test('invalid original and wrong predeclared original hash quarantined', () => {
  const bad = buildCapturePackage({ input: captureFixture(), originalBytes: new Uint8Array([255, 216, 255, 217]),
    transferId: 'bad', senderId: 'sender', receiverId: 'receiver' }); assert.equal(bad.status, 'QUARANTINE');
  const i = fixture(); i.file.sha256 = '0'.repeat(64); assert.equal(make(i).status, 'QUARANTINE');
});
test('corrupt swapped truncated extra files and wrong identities', () => {
  const p = make();
  const cases = [ ['corrupt-original', q => { q.originalBytes[30] ^= 1; }],
    ['truncated-original', q => { q.originalBytes = q.originalBytes.subarray(0, 20); }],
    ['swapped-sidecar', q => { const i = captureFixture(); i.event.frameId = 'other-frame'; q.sidecarBytes = make(i).sidecarBytes; }],
    ['extra-file', q => { q.rogue = new Uint8Array(); }], ['wrong-receiver', q => { q.manifest.receiverId = 'wrong'; }],
    ['wrong-sender', q => { q.manifest.senderId = 'wrong'; }] ];
  for (const [name, mutate] of cases) {
    const q = { manifest: structuredClone(p.manifest), originalBytes: Uint8Array.from(p.originalBytes), sidecarBytes: Uint8Array.from(p.sidecarBytes) };
    mutate(q); const observed = verifyCapturePackage(q, receiver()); assert.equal(observed.status, 'QUARANTINE', name);
    results.push({ name, status: 'EVIDENCE', observed });
  }
});
test('transfer and capture replay gates; rejected receive does not consume state', () => {
  const p = make(), r = receiver(); const wrong = { ...r, receiverId: 'wrong' };
  assert.equal(verifyCapturePackage(pkgOnly(p), wrong).status, 'QUARANTINE'); assert.equal(r.seenTransferIds.size, 0);
  assert.equal(verifyCapturePackage(pkgOnly(p), r).status, 'ACCEPTED');
  assert.equal(verifyCapturePackage(pkgOnly(p), r).reasons[0], 'TRANSFER_REPLAY');
  assert.equal(verifyCapturePackage(pkgOnly(make(captureFixture(), 'new-transfer')), r).reasons[0], 'CAPTURE_REPLAY');
  const changedFrame = captureFixture(); changedFrame.event.frameId = 'changed-frame';
  assert.equal(verifyCapturePackage(pkgOnly(make(changedFrame, 'new-transfer-2')), r).reasons[0], 'CAPTURE_REPLAY');
  assert.equal(verifyCapturePackage(pkgOnly(p), { receiverId: 'rtr-host01-evaluator' }).status, 'QUARANTINE');
});

const directory = resolve(dirname(fileURLToPath(import.meta.url)), '../../evidence/big02');
mkdirSync(directory, { recursive: true });
const p = make();
if (p.status === 'PACKAGED') {
  writeFileSync(resolve(directory, 'geotag-original.jpg'), p.originalBytes);
  writeFileSync(resolve(directory, 'geotag-sidecar.json'), p.sidecarBytes);
  writeFileSync(resolve(directory, 'geotag-manifest.json'), canonicalize(p.manifest));
  const received = verifyCapturePackage(pkgOnly(p), receiver());
  writeFileSync(resolve(directory, 'geotag-receipts.json'), JSON.stringify({ sender: p.receipt, receiver: received.receipt }, null, 2));
}
const summary = { scope: 'BUILDER_SELF_CHECK_SYNTHETIC_HOST01', actualImages: 0,
  independentReview: false, passed: results.filter(r => r.status === 'PASS').length,
  failed: results.filter(r => r.status === 'FAIL').length,
  limitations: ['No actual camera/GNSS/exposure-clock measurements', 'JPEG structure check, not decoder security validation',
    'No signing or production identity attestation', 'Receiver replay sets are session-scoped unless caller persists them'], results };
writeFileSync(resolve(directory, 'geotag-builder-tests.json'), JSON.stringify(summary, null, 2));
console.log(JSON.stringify({ passed: summary.passed, failed: summary.failed, evidence: directory }));
if (summary.failed) { console.error(results.filter(r => r.status === 'FAIL')); process.exitCode = 1; }
