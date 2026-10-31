/** HOST01 deterministic synthetic capture metadata. Browser-safe, no I/O/crypto.
 * bindCapture(input) returns BOUND with a sidecar or QUARANTINE with reason codes.
 * validateSidecar(sidecar) recomputes the binding; it does not attest image bytes.
 * All times are monotonic milliseconds in the explicit source clock domain.
 */
export const LIMITS = Object.freeze({ maxSamples: 256, maxJsonBytes: 131072,
  maxImageBytes: 4 * 1024 * 1024, maxSampleAgeMs: 1000,
  maxBracketSpanMs: 2000, maxTimeUncertaintyMs: 50 });
export const CONTEXT_KEYS = Object.freeze(['runId', 'aircraftId', 'cameraId', 'bootId', 'clockDomain', 'feedId']);
const own = (v, k) => Object.prototype.hasOwnProperty.call(v, k);
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v) &&
  [Object.prototype, null].includes(Object.getPrototypeOf(v));
const exact = (v, keys) => plain(v) && Object.keys(v).length === keys.length && keys.every(k => own(v, k));
export const validId = v => typeof v === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$/.test(v);
const finite = v => typeof v === 'number' && Number.isFinite(v);
const time = v => finite(v) && v >= 0 && v <= Number.MAX_SAFE_INTEGER;
export const sameContext = (a, b) => CONTEXT_KEYS.every(k => a[k] === b[k]);
const validContext = c => exact(c, CONTEXT_KEYS) && CONTEXT_KEYS.every(k => validId(c[k]));

/** Canonical JSON: sorted object keys; plain JSON values only; bounded depth. */
export function canonicalize(value) {
  let remaining = LIMITS.maxJsonBytes;
  const ancestors = new Set();
  const take = text => {
    remaining -= new TextEncoder().encode(text).length;
    if (remaining < 0) throw new Error('JSON_SIZE');
    return text;
  };
  const visit = (v, depth) => {
    if (depth > 20) throw new Error('JSON_DEPTH');
    if (v === null || typeof v === 'boolean' || finite(v)) return take(JSON.stringify(v));
    if (typeof v === 'string') {
      if (v.length > LIMITS.maxJsonBytes) throw new Error('JSON_SIZE');
      return take(JSON.stringify(v));
    }
    if ((!Array.isArray(v) && !plain(v)) || ancestors.has(v)) throw new Error('JSON_TYPE_OR_CYCLE');
    ancestors.add(v);
    let result;
    if (Array.isArray(v)) {
      if (v.length > 1024) throw new Error('JSON_ARRAY_SIZE');
      const items = [];
      take('[]');
      for (let i = 0; i < v.length; i++) {
        if (i) take(',');
        items.push(visit(v[i], depth + 1));
      }
      result = '[' + items.join(',') + ']';
    } else {
      const keys = Object.keys(v).sort();
      if (keys.length > 64) throw new Error('JSON_TYPE');
      const items = [];
      take('{}');
      for (let i = 0; i < keys.length; i++) {
        if (i) take(',');
        const prefix = take(JSON.stringify(keys[i]) + ':');
        items.push(prefix + visit(v[keys[i]], depth + 1));
      }
      result = '{' + items.join(',') + '}';
    }
    ancestors.delete(v);
    return result;
  };
  return visit(value, 0);
}
const boundedJSON = v => {
  try { return new TextEncoder().encode(canonicalize(v)).length <= LIMITS.maxJsonBytes; }
  catch { return false; }
};
const quarantine = reason => ({ status: 'QUARANTINE', reasons: [reason], actualImages: 0,
  integrity: 'ORIGINAL_BYTES_NOT_ASSESSED_BY_METADATA_CORE' });
const normLon = x => ((x + 180) % 360 + 360) % 360 - 180;

export function bindCapture(input) {
  if (!boundedJSON(input)) return quarantine('INPUT_NOT_BOUNDED_JSON');
  if (!exact(input, ['schemaVersion', 'sourceKind', 'context', 'event', 'gnss', 'file', 'policy']) ||
    input.schemaVersion !== 1 || input.sourceKind !== 'SYNTHETIC') return quarantine('INPUT_SCHEMA');
  const { context, event, gnss, file, policy } = input;
  if (!validContext(context)) return quarantine('CONTEXT_INVALID');
  if (!exact(event, ['kind', 'captureId', 'frameId', 'exposureMonotonicMs', 'timeUncertaintyMs', ...CONTEXT_KEYS]) ||
    event.kind !== 'CAPTURE_EVENT') return quarantine('CAPTURE_EVENT_REQUIRED_ACK_INSUFFICIENT');
  if (!validId(event.captureId) || !validId(event.frameId) || !sameContext(context, event)) return quarantine('EVENT_IDENTITY');
  if (!time(event.exposureMonotonicMs) || !finite(event.timeUncertaintyMs) || event.timeUncertaintyMs < 0)
    return quarantine('EXPOSURE_TIME_INVALID');
  if (!exact(policy, ['maxSampleAgeMs', 'maxBracketSpanMs', 'maxTimeUncertaintyMs']) ||
    Object.keys(policy).some(k => !finite(policy[k]) || policy[k] <= 0 || policy[k] > LIMITS[k]))
    return quarantine('POLICY_INVALID_OR_EXCEEDS_HARD_CAP');
  if (event.timeUncertaintyMs > policy.maxTimeUncertaintyMs) return quarantine('EXPOSURE_TIME_UNCERTAIN');
  if (!exact(file, ['name', 'mime', 'sizeBytes', 'sha256']) || file.name !== 'original.jpg' || file.mime !== 'image/jpeg' ||
    !Number.isSafeInteger(file.sizeBytes) || file.sizeBytes < 4 || file.sizeBytes > LIMITS.maxImageBytes ||
    typeof file.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(file.sha256)) return quarantine('FILE_DESCRIPTOR_INVALID');
  if (!Array.isArray(gnss) || gnss.length < 2 || gnss.length > LIMITS.maxSamples) return quarantine('GNSS_TIMELINE_REQUIRED');
  for (let i = 0; i < gnss.length; i++) {
    const s = gnss[i];
    if (!exact(s, [...CONTEXT_KEYS, 'monotonicMs', 'timeUncertaintyMs', 'quality', 'latitudeDeg', 'longitudeDeg', 'altitude']))
      return quarantine('GNSS_SAMPLE_SCHEMA');
    if (!sameContext(context, s)) return quarantine('GNSS_IDENTITY');
    if (s.quality !== 'VALID_3D') return quarantine('GNSS_QUALITY');
    if (!time(s.monotonicMs) || (i && s.monotonicMs <= gnss[i - 1].monotonicMs)) return quarantine('GNSS_TIME_ORDER');
    if (!finite(s.timeUncertaintyMs) || s.timeUncertaintyMs < 0 ||
      s.timeUncertaintyMs > policy.maxTimeUncertaintyMs) return quarantine('GNSS_TIME_UNCERTAIN');
    if (!finite(s.latitudeDeg) || Math.abs(s.latitudeDeg) > 90 || !finite(s.longitudeDeg) || Math.abs(s.longitudeDeg) > 180)
      return quarantine('GNSS_COORDINATES');
    if (!exact(s.altitude, ['value', 'unit', 'datum']) || !finite(s.altitude.value) ||
      s.altitude.value < -1000 || s.altitude.value > 100000 || s.altitude.unit !== 'm' ||
      s.altitude.datum !== 'WGS84_ELLIPSOID') return quarantine('ALTITUDE_DATUM_OR_UNITS');
  }
  const t = event.exposureMonotonicMs;
  // Require a genuine bracket even when the event coincides with one sample.
  let right = gnss.findIndex(s => s.monotonicMs >= t);
  if (right === 0 && gnss[0].monotonicMs === t) right = 1;
  if (right <= 0) return quarantine('EXPOSURE_OUTSIDE_GNSS_TIMELINE');
  const a = gnss[right - 1], b = gnss[right];
  if (t < a.monotonicMs || t > b.monotonicMs) return quarantine('EXPOSURE_OUTSIDE_GNSS_TIMELINE');
  const uncertainty = event.timeUncertaintyMs + Math.max(a.timeUncertaintyMs, b.timeUncertaintyMs);
  if (uncertainty > policy.maxTimeUncertaintyMs) return quarantine('COMBINED_TIME_UNCERTAIN');
  if (Math.max(t - a.monotonicMs, b.monotonicMs - t) + uncertainty > policy.maxSampleAgeMs ||
    b.monotonicMs - a.monotonicMs > policy.maxBracketSpanMs) return quarantine('GNSS_STALE');
  const fraction = (t - a.monotonicMs) / (b.monotonicMs - a.monotonicMs);
  const longitudeDelta = normLon(b.longitudeDeg - a.longitudeDeg);
  if (Math.abs(longitudeDelta) === 180) return quarantine('GNSS_ANTIPODAL_LONGITUDE_AMBIGUITY');
  const position = {
    reference: 'AIRCRAFT_GNSS_AT_EXPOSURE', horizontalDatum: 'WGS84', angleUnit: 'degree',
    latitudeDeg: a.latitudeDeg + (b.latitudeDeg - a.latitudeDeg) * fraction,
    longitudeDeg: normLon(a.longitudeDeg + longitudeDelta * fraction),
    altitude: { value: a.altitude.value + (b.altitude.value - a.altitude.value) * fraction,
      unit: 'm', datum: 'WGS84_ELLIPSOID' },
    interpolation: 'LINEAR_LATITUDE_SHORTEST_LONGITUDE_ALTITUDE', bracketMonotonicMs: [a.monotonicMs, b.monotonicMs],
    timeUncertaintyMs: uncertainty, spatialAccuracy: 'UNKNOWN', cameraLeverArm: 'UNKNOWN', targetLocation: 'NOT_DETERMINED'
  };
  // Copy all evidence; callers cannot mutate the accepted result through the input.
  let sidecar;
  try { sidecar = JSON.parse(canonicalize({ schemaVersion: 1, kind: 'AERIS_SYNTHETIC_CAPTURE_SIDECAR',
    sourceKind: 'SYNTHETIC', actualImages: 0, binding: input, position })); }
  catch { return quarantine('SIDECAR_SIZE'); }
  return { status: 'BOUND', reasons: [], actualImages: 0, sidecar };
}

export function validateSidecar(sidecar) {
  if (!boundedJSON(sidecar) || !exact(sidecar, ['schemaVersion', 'kind', 'sourceKind', 'actualImages', 'binding', 'position']) ||
    sidecar.schemaVersion !== 1 || sidecar.kind !== 'AERIS_SYNTHETIC_CAPTURE_SIDECAR' ||
    sidecar.sourceKind !== 'SYNTHETIC' || sidecar.actualImages !== 0) return quarantine('SIDECAR_SCHEMA');
  const bound = bindCapture(sidecar.binding);
  if (bound.status !== 'BOUND') return bound;
  if (canonicalize(sidecar) !== canonicalize(bound.sidecar)) return quarantine('SIDECAR_DERIVATION_MISMATCH');
  return { status: 'VALID', reasons: [], actualImages: 0 };
}
