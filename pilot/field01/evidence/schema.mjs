/** FIELD01 byte/context integrity only. Synthetic payload + SITL reference, no authenticity. */
import { createHash } from 'node:crypto';
import { canonicalize } from '../../../media/big02/geotag.mjs';
export { canonicalize };
export { inspectJpeg } from '../../../media/big02/capture-package.mjs';
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export const jsonBytes = value => Buffer.from(canonicalize(value), 'utf8');
export const validId = value => typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$/.test(value);
export const validSha = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
export const exact = (v, keys) => v && typeof v === 'object' && !Array.isArray(v) &&
  Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v, k));
export const fail = code => { throw new Error(code); };
const finite = v => typeof v === 'number' && Number.isFinite(v);
export const CONTEXT_KEYS = ['gatewaySession','stationId','modelSha256','planSha256','flightRun','flightBoot',
  'payloadId','sourceRun','sourceBoot','configId','feed'];
export const REFERENCE_METHODS = Object.freeze(['HOST_RECEIPT_BRACKET_REFERENCE_ONLY','NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC']);
export function validateSidecar(s, captureId, original) {
  if (!exact(s, ['schemaVersion','kind','sourceKind','actualImages','captureId','frameId','context','position','timing','file']) ||
      s.schemaVersion !== 1 || s.kind !== 'FIELD01_SYNTHETIC_CAPTURE' || s.sourceKind !== 'SYNTHETIC' ||
      s.actualImages !== 0 || s.captureId !== captureId || !validId(captureId) || !validId(s.frameId)) fail('SIDECAR_SCHEMA');
  if (!exact(s.context, CONTEXT_KEYS) || !CONTEXT_KEYS.every(k =>
      k.endsWith('Sha256') ? validSha(s.context[k]) : validId(s.context[k]))) fail('SIDECAR_CONTEXT');
  if (!exact(s.file, ['name','mime','sizeBytes','sha256']) || s.file.name !== 'original.jpg' ||
      s.file.mime !== 'image/jpeg' || s.file.sizeBytes !== original.length || s.file.sha256 !== sha256(original)) fail('SIDECAR_FILE');
  const t = s.timing, tk = ['sourceTimestampUs','sourceToHostLowerMs','sourceToHostUpperMs','referenceHostMonoMs','method','physicalExposureTime'];
  if (!t || !exact(t, [...tk, ...(Object.hasOwn(t,'reason') ? ['reason'] : [])]) ||
      t.method !== 'BOUND_SOURCE_CLOCK_TO_HOST_RECEIPT' || t.physicalExposureTime !== 'UNKNOWN' ||
      !Number.isSafeInteger(t.sourceTimestampUs) || t.sourceTimestampUs < 0 ||
      ![t.sourceToHostLowerMs,t.sourceToHostUpperMs,t.referenceHostMonoMs].every(finite) ||
      t.sourceToHostLowerMs > t.sourceToHostUpperMs || t.referenceHostMonoMs < 0 ||
      (Object.hasOwn(t,'reason') && (typeof t.reason !== 'string' || !t.reason.length || t.reason.length > 512))) fail('SIDECAR_TIMING');
  if (s.position === null) { if (!t.reason) fail('UNLOCATED_REASON_REQUIRED'); return; }
  const p = s.position, pk = ['latitudeDeg','longitudeDeg','altitudeMslM','relativeHomeM','datum','method',
    'qualifiedForSurvey','sensorTimeUncertaintyMs','hostMonoMs'];
  if (!exact(p,[...pk,...['observationBefore','observationAfter'].filter(k=>Object.hasOwn(p,k))]) ||
      ![p.latitudeDeg,p.longitudeDeg,p.altitudeMslM,p.relativeHomeM,p.hostMonoMs].every(finite) ||
      Math.abs(p.latitudeDeg)>90 || Math.abs(p.longitudeDeg)>180 || p.hostMonoMs<0 ||
      p.datum !== 'MSL' || !REFERENCE_METHODS.includes(p.method) ||
      p.qualifiedForSurvey !== false || p.sensorTimeUncertaintyMs !== null) fail('SIDECAR_REFERENCE_POSITION');
  for (const key of ['observationBefore','observationAfter']) if (Object.hasOwn(p,key)) jsonBytes(p[key]);
}
export function validateLink(link, s) {
  if (!exact(link,['schemaVersion','captureId','modelSha256','planSha256','flightRun','flightBoot','payloadId','sourceKind','actualImages']) ||
      link.schemaVersion!==1 || link.captureId!==s.captureId || link.sourceKind!=='SYNTHETIC' || link.actualImages!==0 ||
      !['modelSha256','planSha256','flightRun','flightBoot','payloadId'].every(k=>link[k]===s.context[k])) fail('LINK_CONTEXT');
}

/** Deterministic ustar archive: precisely three regular files, no directory/link entries. */
export function makeTar(files) {
  const out=[];
  for (const [name, bytes] of files) {
    if (!['original.jpg','sidecar.json','manifest.json'].includes(name)) fail('TAR_PATH');
    const header=Buffer.alloc(512);
    header.write(name,0,100,'ascii'); header.write('0000444\0',100,8,'ascii');
    header.write('0000000\0',108,8,'ascii'); header.write('0000000\0',116,8,'ascii');
    header.write(bytes.length.toString(8).padStart(11,'0')+'\0',124,12,'ascii');
    header.write('00000000000\0',136,12,'ascii'); header.fill(32,148,156); header[156]=48;
    header.write('ustar\0',257,6,'ascii'); header.write('00',263,2,'ascii');
    const sum=header.reduce((a,b)=>a+b,0); header.write(sum.toString(8).padStart(6,'0')+'\0 ',148,8,'ascii');
    out.push(header,bytes,Buffer.alloc((512-bytes.length%512)%512));
  }
  return Buffer.concat([...out,Buffer.alloc(1024)]);
}
