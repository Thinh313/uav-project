/** Node-only capture package hashing, JPEG structure gate and receiver receipt.
 * No file/network writes. Package integrity is not source authenticity/signing.
 * buildCapturePackage({input,originalBytes,transferId,senderId,receiverId})
 * verifyCapturePackage(package,{receiverId,expectedSenderId,seenTransferIds,seenCaptureIds})
 * Replay sets must be retained by the receiver for the entire receiver session.
 */
import { createHash } from 'node:crypto';
import { bindCapture, validateSidecar, canonicalize, LIMITS, validId, sameContext } from './geotag.mjs';
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const exact = (v, keys) => v && typeof v === 'object' && !Array.isArray(v) &&
  Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v, k));
const reject = reason => ({ status: 'QUARANTINE', reasons: [reason], actualImages: 0,
  integrity: 'RECEIVER_GATE_NOT_SATISFIED_OR_NOT_CHECKED' });
const bytes = v => v instanceof Uint8Array && v.byteLength <= LIMITS.maxImageBytes;
const jsonBytes = v => Buffer.from(canonicalize(v), 'utf8');
export const captureReplayKey = sidecar => canonicalize({ context: sidecar.binding.context,
  captureId: sidecar.binding.event.captureId });

/** Bounded JPEG marker structure check, not an image-decoder/safety certificate. */
export function inspectJpeg(data) {
  if (!bytes(data) || data.length < 20 || data[0] !== 255 || data[1] !== 216 ||
    data[data.length - 2] !== 255 || data[data.length - 1] !== 217) return false;
  let offset = 2, sawFrame = false, sawScan = false, markers = 0;
  while (offset < data.length && ++markers <= 65536) {
    if (data[offset++] !== 255) return false;
    while (data[offset] === 255) offset++;
    const marker = data[offset++];
    if (marker === 217) return offset === data.length && sawFrame && sawScan;
    if (marker === undefined || marker === 0 || marker === 216 || (marker >= 208 && marker <= 215)) return false;
    if (marker === 1) continue;
    if (offset + 2 > data.length) return false;
    const length = data[offset] * 256 + data[offset + 1];
    if (length < 2 || offset + length > data.length) return false;
    if ([192, 193, 194].includes(marker)) {
      if (length < 11 || sawFrame) return false;
      const height = data[offset + 3] * 256 + data[offset + 4];
      const width = data[offset + 5] * 256 + data[offset + 6];
      const components = data[offset + 7];
      if (!width || !height || width > 8192 || height > 8192 || ![1, 3, 4].includes(components) ||
        length !== 8 + 3 * components) return false;
      sawFrame = true;
    } else if (marker >= 195 && marker <= 207 && ![196, 200, 204].includes(marker)) return false;
    if (marker === 218) {
      if (!sawFrame || length < 6 || length !== 6 + 2 * data[offset + 2]) return false;
      sawScan = true;
      offset += length;
      while (offset < data.length) {
        if (data[offset] !== 255) { offset++; continue; }
        const next = data[offset + 1];
        if (next === 0 || (next >= 208 && next <= 215)) { offset += 2; continue; }
        if (next === 255) { offset++; continue; }
        break;
      }
    } else offset += length;
  }
  return false;
}

export function buildCapturePackage({ input, originalBytes, transferId, senderId, receiverId } = {}) {
  try {
    if (![transferId, senderId, receiverId].every(validId)) return reject('TRANSFER_IDENTITY');
    if (!inspectJpeg(originalBytes)) return reject('ORIGINAL_JPEG_STRUCTURE');
    const original = Buffer.from(originalBytes);
    const file = { name: 'original.jpg', mime: 'image/jpeg', sizeBytes: original.length, sha256: sha256(original) };
    if (!input || (input.file !== undefined && canonicalize(input.file) !== canonicalize(file))) return reject('ORIGINAL_DESCRIPTOR_MISMATCH');
    const result = bindCapture({ ...input, file });
    if (result.status !== 'BOUND') return result;
    const sidecarBytes = jsonBytes(result.sidecar);
    if (sidecarBytes.length > LIMITS.maxJsonBytes) return reject('SIDECAR_SIZE');
    const base = { schemaVersion: 1, kind: 'AERIS_SYNTHETIC_CAPTURE_PACKAGE', sourceKind: 'SYNTHETIC', actualImages: 0,
      transferId, senderId, receiverId, context: result.sidecar.binding.context,
      captureId: result.sidecar.binding.event.captureId, frameId: result.sidecar.binding.event.frameId,
      files: [{ path: 'original.jpg', sizeBytes: original.length, sha256: file.sha256 },
        { path: 'sidecar.json', sizeBytes: sidecarBytes.length, sha256: sha256(sidecarBytes) }] };
    const manifest = { ...base, packageId: sha256(jsonBytes(base)) };
    return { status: 'PACKAGED', manifest, originalBytes: original, sidecarBytes,
      receipt: { kind: 'LOCAL_SYNTHETIC_SENDER_RECEIPT', transferId, packageId: manifest.packageId,
        originalSha256: file.sha256, actualImages: 0, authenticity: 'NOT_ATTESTED' } };
  } catch { return reject('PACKAGE_INPUT_INVALID'); }
}

export function verifyCapturePackage(pkg, options = {}) {
  try {
    const { receiverId, expectedSenderId, seenTransferIds, seenCaptureIds } = options;
    if (!validId(receiverId) || !validId(expectedSenderId) || !(seenTransferIds instanceof Set) ||
      !(seenCaptureIds instanceof Set) || seenTransferIds.size >= 10000 || seenCaptureIds.size >= 10000)
      return reject('RECEIVER_IDENTITY_OR_REPLAY_STATE_REQUIRED');
    if (!exact(pkg, ['manifest', 'originalBytes', 'sidecarBytes'])) return reject('PACKAGE_FILES_EXACT');
    const { manifest: m, originalBytes, sidecarBytes } = pkg;
    if (!exact(m, ['schemaVersion', 'kind', 'sourceKind', 'actualImages', 'transferId', 'senderId', 'receiverId',
      'context', 'captureId', 'frameId', 'files', 'packageId']) || m.schemaVersion !== 1 ||
      m.kind !== 'AERIS_SYNTHETIC_CAPTURE_PACKAGE' || m.sourceKind !== 'SYNTHETIC' || m.actualImages !== 0 ||
      ![m.transferId, m.senderId, m.receiverId, m.captureId, m.frameId].every(validId) ||
      !/^[a-f0-9]{64}$/.test(m.packageId)) return reject('MANIFEST_SCHEMA');
    if (m.receiverId !== receiverId || m.senderId !== expectedSenderId) return reject('RECEIVER_OR_SENDER_MISMATCH');
    if (seenTransferIds.has(m.transferId)) return reject('TRANSFER_REPLAY');
    const { packageId, ...base } = m;
    if (jsonBytes(m).length > LIMITS.maxJsonBytes || sha256(jsonBytes(base)) !== packageId) return reject('MANIFEST_HASH');
    if (!Array.isArray(m.files) || m.files.length !== 2) return reject('MANIFEST_FILES');
    for (let i = 0; i < 2; i++) {
      const f = m.files[i], data = i ? sidecarBytes : originalBytes;
      if (!exact(f, ['path', 'sizeBytes', 'sha256']) || f.path !== ['original.jpg', 'sidecar.json'][i] ||
        !Number.isSafeInteger(f.sizeBytes) || f.sizeBytes < 1 || !/^[a-f0-9]{64}$/.test(f.sha256) ||
        !bytes(data) || (i && data.length > LIMITS.maxJsonBytes) || data.length !== f.sizeBytes || sha256(data) !== f.sha256)
        return reject('FILE_HASH_SIZE_OR_PATH');
    }
    if (!inspectJpeg(originalBytes)) return reject('ORIGINAL_JPEG_STRUCTURE');
    const sidecar = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(sidecarBytes));
    if (!jsonBytes(sidecar).equals(Buffer.from(sidecarBytes))) return reject('SIDECAR_NONCANONICAL');
    const validation = validateSidecar(sidecar);
    if (validation.status !== 'VALID') return validation;
    const binding = sidecar.binding;
    if (!sameContext(m.context, binding.context) || canonicalize(m.context) !== canonicalize(binding.context) ||
      m.captureId !== binding.event.captureId || m.frameId !== binding.event.frameId ||
      binding.file.sha256 !== m.files[0].sha256 || binding.file.sizeBytes !== m.files[0].sizeBytes)
      return reject('SIDECAR_MANIFEST_BINDING');
    const captureKey = captureReplayKey(sidecar);
    if (seenCaptureIds.has(captureKey)) return reject('CAPTURE_REPLAY');
    seenTransferIds.add(m.transferId); seenCaptureIds.add(captureKey);
    return { status: 'ACCEPTED', actualImages: 0, sidecar, receipt: {
      kind: 'LOCAL_SYNTHETIC_RECEIVER_RECEIPT', transferId: m.transferId, packageId, receiverId,
      originalSha256: m.files[0].sha256, sidecarSha256: m.files[1].sha256,
      integrity: 'EXACT_BYTES_AND_CONTEXT_VERIFIED', authenticity: 'NOT_ATTESTED', actualImages: 0 } };
  } catch { return reject('PACKAGE_PARSE_OR_INPUT_INVALID'); }
}
