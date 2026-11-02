/** Original native cryptography + semantic/RC/clock replay for archival only.
 * No live devices, sockets, flight, restoration or synthetic acceptance.
 */
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {verifyNativeInputs} from '../../betasim-integrated01/product/native-cold.mjs';
import {decodeInputJournal} from '../../betasim-integrated01/product/input-journal.mjs';
import {scanNativeTar} from '../../betasim-integrated01/product/native-tar.mjs';
import {NativeProducer} from '../../betasim-integrated01/product/native-producer.mjs';
import {canonical, need, sha} from '../../betasim-integrated01/product/mission.mjs';

function file(p, root, maximum) {
  p = path.resolve(p); root = path.resolve(root);
  need(p.startsWith(root + path.sep) && fs.realpathSync(p) === p, 'RC01_CLOSED_ORIGINAL_PATH');
  const s = fs.lstatSync(p);
  need(s.isFile() && !s.isSymbolicLink() && s.nlink === 1 && s.size > 0 && s.size <= maximum,
    'RC01_CLOSED_ORIGINAL_BOUND');
  const fd = fs.openSync(p, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const before = fs.fstatSync(fd), raw = fs.readFileSync(fd), after = fs.fstatSync(fd);
    need(raw.length === s.size && ['dev', 'ino', 'size', 'mtimeMs', 'ctimeMs'].every(k =>
      before[k] === s[k] && after[k] === s[k]), 'RC01_ORIGINAL_CHANGED_DURING_READ');
    return raw;
  } finally { fs.closeSync(fd); }
}
function ref(root, r, maximum) {
  need(r && typeof r.path === 'string' && Number.isSafeInteger(r.offset) && r.offset >= 0 &&
    Number.isSafeInteger(r.bytes) && r.bytes > 0 && r.bytes <= maximum &&
    /^[a-f0-9]{64}$/.test(r.sha256), 'RC01_CLOSED_ORIGINAL_REF');
  const raw = file(path.resolve(root, r.path), root, 32 * 2 ** 20);
  need(r.offset + r.bytes <= raw.length, 'RC01_CLOSED_ORIGINAL_RANGE');
  const part = raw.subarray(r.offset, r.offset + r.bytes);
  need(sha(part) === r.sha256, 'RC01_CLOSED_ORIGINAL_SHA');
  return part;
}
export async function replayClosedUsed(options) {
  const {reference, descriptor, productRoot} = options;
  const caseRoot = path.dirname(path.dirname(path.dirname(productRoot)));
  const context = {...descriptor.context, profileId: descriptor.profileId};
  const progressRaw = file(path.join(productRoot, 'reports/companion-progress.jsonl'), caseRoot, 1024 * 1024);
  need(progressRaw.at(-1) === 10, 'RC01_ORIGINAL_COMPANION_PROGRESS_COMPLETE');
  const launchRaw = file(path.join(caseRoot, 'diagnostics/product-' + descriptor.context.run + '/launch.json'),
    caseRoot, 8192), launchRows = launchRaw.toString('utf8').trim().split('\n').map(JSON.parse);
  need(launchRows.length === 1 && Number.isSafeInteger(launchRows[0].pid) &&
    launchRows[0].format === 'aeris-diagnostic-child', 'RC01_ORIGINAL_COMPANION_LAUNCH');
  const seals = progressRaw.toString('utf8').trim().split('\n').map(JSON.parse)
    .filter(r => r.kind === 'COMMAND_COMPLETE' && r.data?.action === 'SEAL_PRODUCT');
  need(seals.length === 1 && seals[0].pid === launchRows[0].pid &&
    seals[0].run === descriptor.context.run &&
    canonical(seals[0].data.result.product) === canonical(options.sourceSeal),
    'RC01_ORIGINAL_PRODUCT_SEAL_NOT_SUPPLIED_SUMMARY');
  const storeRaw = file(path.join(productRoot, 'journal/workspace.jsonl'), productRoot, 8 * 2 ** 20);
  need(storeRaw.at(-1) === 10, 'RC01_ORIGINAL_WORKSPACE_COMPLETE');
  let storeHead = '0'.repeat(64), storeSequence = 0; const originalReviews = [];
  for (const line of storeRaw.toString('utf8').trim().split('\n')) {
    const row = JSON.parse(line), {hash, ...body} = row;
    need(canonical(row) === line && row.seq === ++storeSequence && row.previousHash === storeHead &&
      row.schemaVersion === 1 && sha(body) === hash && storeSequence <= 2048,
      'RC01_ORIGINAL_WORKSPACE_ROW_CHAIN');
    storeHead = hash;
    if (row.kind === 'BETA_FLIGHT_REVIEW') originalReviews.push(row.data);
  }
  const storeClose = options.sourceSeal.store;
  need(storeClose?.closed === true && storeClose.poisoned === false && storeClose.issue === null &&
    storeClose.head === storeHead && storeClose.records === storeSequence &&
    canonical(originalReviews) === canonical(options.reviews), 'RC01_REVIEWS_FROM_ORIGINAL_WORKSPACE');
  const closeBytes = file(path.join(productRoot, 'state/store-close-' + storeClose.ownerNonce + '.json'),
    productRoot, 16384), closedStore = JSON.parse(closeBytes);
  need(closedStore.nonce === storeClose.ownerNonce && closedStore.head === storeHead &&
    closedStore.records === storeSequence && closedStore.poisoned === false &&
    closedStore.issue === null && closedStore.authorityRestorable === false,
    'RC01_ORIGINAL_WORKSPACE_CLOSED_POINTER');
  const raw = file(reference.descriptorPath, caseRoot, 16384);
  need(raw.length === reference.descriptorBytes && sha(raw) === reference.descriptorSHA256,
    'RC01_CLOSED_DESCRIPTOR_SHA');
  const closed = JSON.parse(raw);
  need(closed.candidateSHA256 === descriptor.candidateSHA256 &&
    canonical(closed.context) === canonical(context) && closed.authorityRestorable === false &&
    Array.isArray(closed.generations) && closed.generations.length >= 1 && closed.generations.length <= 2,
    'RC01_CLOSED_GENERATIONS_CONTEXT');
  const selected = new Map(), keys = new Set(), epochs = new Set();
  for (const [ordinal, g] of closed.generations.entries()) {
    need(g.probeGeneration === ordinal + 1 && /^[a-f0-9]{32}$/.test(g.journalGeneration) &&
      !selected.has(g.journalGeneration) && !keys.has(g.keyId) && !epochs.has(g.processEpoch) &&
      g.sourceSHA256 === descriptor.native.sourceSHA256 &&
      g.APKSHA256 === descriptor.native.APK_SHA256, 'RC01_CLOSED_DISTINCT_SELECTED_IDENTITY');
    need(path.dirname(g.originalStoreRoot) === path.dirname(productRoot), 'RC01_CLOSED_STORE_SCOPE');
    const registration = JSON.parse(ref(caseRoot, g.registrationRootRef, 8192));
    need(registration.format === 'aeris-root-native-producer-registration' && registration.version === 1 &&
      registration.authorityGranted === false && registration.generation === ordinal + 1 &&
      canonical(registration.context) === canonical(context) && registration.pid === g.pid &&
      registration.processEpoch === g.processEpoch && registration.keyId === g.keyId &&
      registration.publicKeyX509Base64 === g.publicKeyX509Base64 &&
      registration.sourceSHA256 === g.sourceSHA256 && registration.APKSHA256 === g.APKSHA256 &&
      registration.originalStoreRoot === g.originalStoreRoot, 'RC01_CLOSED_ROOT_REGISTRATION');
    new NativeProducer({...g, scope: 'ROOT_PRIVILEGED_NATIVE_STATUS_VERIFIED',
      authorityRestorable: false, originalStatusRef: g.originalObservationRef});
    const observation = JSON.parse(ref(g.originalStoreRoot, g.originalObservationRef, 16384));
    const snapshotRaw = ref(g.originalStoreRoot, g.snapshotOriginalRef, 16384), s = JSON.parse(snapshotRaw);
    const ack = JSON.parse(ref(g.originalStoreRoot, observation.ACKRef, 2048));
    need(observation.format === 'aeris-product-native-observation' && observation.version === 1 &&
      observation.actualPID === g.pid && observation.sourceSHA256 === g.sourceSHA256 &&
      observation.APKSHA256 === g.APKSHA256 && observation.authorityGranted === false &&
      observation.readonly === true && canonical(observation.snapshotRef) === canonical(g.snapshotOriginalRef) &&
      observation.requestNonce === s.requestNonce && ack.requestNonce === s.requestNonce &&
      ack.pid === s.pid && ack.processEpoch === s.processEpoch && ack.bytes === snapshotRaw.length &&
      ack.sha256 === sha(snapshotRaw), 'RC01_CLOSED_PRIVILEGED_STATUS_ACK');
    const i = s.input, j = i?.journal;
    need(s.format === 'aeris-betasim-native-status' && s.version === 1 && s.pid === g.pid &&
      s.processEpoch === g.processEpoch && s.package === descriptor.native.package &&
      s.sourceSHA256 === g.sourceSHA256 && s.authorityRestorable === false &&
      i?.producerKeyId === g.keyId && i.producerPublicKeyX509Base64 === g.publicKeyX509Base64 &&
      i.closed === true && i.workerTerminated === true && i.configured === false &&
      i.pending === false && i.failed === false && i.authorityRestorable === false &&
      j?.generation === g.journalGeneration && j.closed === true && j.durablyDrained === true &&
      j.failed === false && j.pendingOutcome === false && canonical(j) === canonical(g.journalStatus),
      'RC01_CLOSED_ORIGINAL_QUIESCENT_EXACT_STATUS');
    selected.set(g.journalGeneration, g); keys.add(g.keyId); epochs.add(g.processEpoch);
  }
  const result = await verifyNativeInputs(options);
  need(result.unresolvedIntentGenerations.length === 0 && result.unclosedGenerationPrefixes.length === 0,
    'RC01_CLOSED_NO_UNRESOLVED_OR_UNCLOSED');
  const generations = [], tarHash = createHash('sha256'); let tarBytes = 0;
  async function* tarChunks() {
    for await (const block of fs.createReadStream(closed.tar.path)) {
      tarBytes += block.length; need(tarBytes <= closed.tar.bytes, 'RC01_TAR_REPLAY_GROWTH');
      tarHash.update(block); yield block;
    }
  }
  await scanNativeTar(tarChunks(), {
    select: p => selected.has(p.match(/^files\/product-input01\/([a-f0-9]{32})\.aj02$/)?.[1]),
    onJournal: ({path: member, raw, bytes, sha256}) => {
      const generation = member.slice(-37, -5), g = selected.get(generation), decoded = decodeInputJournal(raw);
      need(decoded.unresolvedIntentSequence === null && decoded.records === g.journalStatus.sequence &&
        decoded.bytes === g.journalStatus.bytes && decoded.head === g.journalStatus.head,
        'RC01_CLOSED_EXACT_ORIGINAL_AJ02');
      generations.push({generation, bytes, sha256, records: decoded.records, head: decoded.head,
        disposition: decoded.records === 0 ? 'UNUSED' : 'CLOSED_VERIFIED', sourceClosedStatusBound: true,
        pid: g.pid, processEpoch: g.processEpoch, keyId: g.keyId,
        originalObservationRef: g.originalObservationRef, snapshotOriginalRef: g.snapshotOriginalRef,
        registrationRootRef: g.registrationRootRef});
    }
  });
  need(generations.length === selected.size && tarBytes === closed.tar.bytes &&
    tarHash.digest('hex') === closed.tar.sha256, 'RC01_CLOSED_ALL_SELECTED_ORIGINAL_TAR_BYTES');
  return {format: 'aeris-betarc01-original-used-native-cold-replay', version: 1,
    status: 'ORIGINAL_SIGNATURES_STATUS_REGISTRATION_RC_CLOCK_REPLAYED_NOT_FLIGHT',
    candidateSHA256: descriptor.candidateSHA256, sourceSHA256: descriptor.native.sourceSHA256,
    APKSHA256: descriptor.native.APK_SHA256, context, generations, semantic: result,
    authorityRestorable: false, flightAcceptance: false, actorsStarted: false};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const raw = fs.readFileSync(0); need(raw.length <= 256 * 1024, 'RC01_OPTIONS_256K');
  const result = await replayClosedUsed(JSON.parse(raw));
  const output = Buffer.from(JSON.stringify(result) + '\n');
  need(output.length <= 32768, 'RC01_REPLAY_RESULT_32K'); process.stdout.write(output);
}
