"""Live pure original rehash of independently replayed Root-approved capsules.

No process, socket, native, model or command call is made here. Full crypto is
performed offline by Root after the original case has physically closed.
"""
import base64
from planning.betarc01.archive.common_rc01 import (
    approved_capsule, canonical, decode, need, original_ref, repository, sha, verify_inventory)


def closed_sources(approved_sources, node=None):
    need(type(approved_sources) is list and len(approved_sources) <= 8, 'APPROVED_SOURCE_COUNT8')
    results, seen = {}, set()
    for ref in approved_sources:
        request, options, capsule_raw, capsule = approved_capsule(ref)
        need(ref['sha256'] not in seen, 'DUPLICATE_APPROVED_SOURCE')
        seen.add(ref['sha256'])
        replay_raw = original_ref(capsule['replayRef'], 65536, within=repository() / 'evidence/betarc01')
        inventory_raw = original_ref(capsule['inventoryRef'], 1024 * 1024,
                                     within=repository() / 'evidence/betarc01')
        inventory = decode(inventory_raw)
        verify_inventory(inventory, request, capsule['requestRef']['sha256'])
        value = decode(replay_raw)
        need(value.get('format') == 'aeris-betarc01-offline-original-native-replay' and
             type(value.get('version')) is int and value['version'] == 2 and
             value.get('sourceRequestSHA256') == capsule['requestRef']['sha256'] and
             value.get('originalInventorySHA256') == sha(inventory_raw) and
             value.get('candidateSHA256') == request['candidateSHA256'] and
             value.get('sourceSHA256') == options['descriptor']['native']['sourceSHA256'] and
             value.get('APKSHA256') == options['descriptor']['native']['APK_SHA256'] and
             value.get('status') == 'ORIGINAL_SIGNATURES_STATUS_REGISTRATION_RC_CLOCK_REPLAYED_NOT_FLIGHT' and
             value.get('authorityRestorable') is False and value.get('flightAcceptance') is False and
             value.get('runtimeActorsStarted') is False and
             value.get('originalNativeObservationCount', 0) > 0 and
             type(value.get('generations')) is list and 1 <= len(value['generations']) <= 2,
             'ROOT_APPROVED_ORIGINAL_OFFLINE_REPLAY_JOIN')
        capture = value.get('offlineNodeCapture') or {}
        need(capture.get('format') == 'aeris-betarc01-offline-verifier-capture' and
             capture.get('captureComplete') is True and capture.get('stdoutEOF') is True and
             capture.get('stderrEOF') is True and capture.get('failure') is None and
             capture.get('exit') == 0 and capture.get('stderrBytes') == 0 and
             capture.get('stdinSHA256') == sha(canonical(options)), 'OFFLINE_COMPLETE_CRYPTO_CAPTURE')
        node_raw = base64.b64decode(value['originalNodeResultBase64'], validate=True)
        need(len(node_raw) == capture['stdoutBytes'] and sha(node_raw) == capture['stdoutSHA256'],
             'ORIGINAL_OFFLINE_NODE_RESULT_BYTES')
        node_value = decode(node_raw)
        need(all(node_value.get(k) == value.get(k) for k in
                 ('status', 'candidateSHA256', 'sourceSHA256', 'APKSHA256', 'context', 'generations',
                  'semantic', 'authorityRestorable', 'flightAcceptance')) and
             node_value.get('actorsStarted') is False, 'OFFLINE_NODE_RESULT_EXACT_GENERATIONS_SCOPE')
        for row in value['generations']:
            generation = row['generation']
            need(generation not in results, 'DUPLICATE_CLOSED_GENERATION_SOURCE')
            proof = {'format': 'aeris-betarc01-original-closed-generation-proof', 'version': 2,
                     **row, 'candidateSHA256': value['candidateSHA256'],
                     'APKSHA256': value['APKSHA256'], 'sourceSHA256': value['sourceSHA256'],
                     'context': value['context'], 'rootApprovedCapsuleRef': ref,
                     'sourceReplaySHA256': sha(replay_raw),
                     'authorityRestorable': False, 'flightAcceptance': False}
            results[generation] = {**proof, 'proofSHA256': sha(canonical(proof))}
    return results
