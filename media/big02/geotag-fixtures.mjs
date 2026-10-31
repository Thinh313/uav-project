/** Entirely synthetic deterministic fixtures, no actual camera/GNSS measurements. */
export const SYNTHETIC_CONTEXT = Object.freeze({ runId: 'host01-fixture-run', aircraftId: 'synthetic-aircraft',
  cameraId: 'synthetic-camera', bootId: 'synthetic-boot', clockDomain: 'fixture-monotonic', feedId: 'rgb-synthetic' });

/** A complete 1x1 gray baseline JPEG, constant DCT coefficients, generated here.
 * Tiny fixtures prove byte/context handling, never real photography or quality.
 */
export function syntheticJpegBytes() {
  const table = [1, ...Array(15).fill(0), 0];
  return new Uint8Array([255, 216,
    255, 219, 0, 67, 0, ...Array(64).fill(1),
    255, 192, 0, 11, 8, 0, 1, 0, 1, 1, 1, 17, 0,
    255, 196, 0, 20, 0, ...table,
    255, 196, 0, 20, 16, ...table,
    255, 218, 0, 8, 1, 1, 0, 0, 63, 0, 63, 255, 217]);
}

/** Omit file for Node buildCapturePackage to compute from actual original bytes.
 * Browser bindCapture users must add a sizeBytes/sha256 original file descriptor.
 */
export function captureFixture(overrides = {}) {
  const context = { ...SYNTHETIC_CONTEXT };
  return { schemaVersion: 1, sourceKind: 'SYNTHETIC', context,
    event: { kind: 'CAPTURE_EVENT', captureId: 'synthetic-capture-001', frameId: 'synthetic-frame-015',
      exposureMonotonicMs: 1500, timeUncertaintyMs: 2, ...context },
    gnss: [
      { ...context, monotonicMs: 1000, timeUncertaintyMs: 3, quality: 'VALID_3D',
        latitudeDeg: 10, longitudeDeg: 179.8, altitude: { value: 100, unit: 'm', datum: 'WGS84_ELLIPSOID' } },
      { ...context, monotonicMs: 2000, timeUncertaintyMs: 3, quality: 'VALID_3D',
        latitudeDeg: 12, longitudeDeg: -179.8, altitude: { value: 110, unit: 'm', datum: 'WGS84_ELLIPSOID' } }
    ],
    policy: { maxSampleAgeMs: 1000, maxBracketSpanMs: 2000, maxTimeUncertaintyMs: 50 }, ...overrides };
}
