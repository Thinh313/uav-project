"""Streaming independent clock-chain/publication validation and frame-reference checks."""
from pathlib import Path
from importlib import import_module
from collections import OrderedDict
import hashlib,json,struct
from aeris_runtime.policy import clock_events,clock_policy
J=import_module('aeris_runtime.foundation.journal_base')


def verify_clock(out,run,epoch,boot,*,expected_anchor,source_amendment,maximum_seconds):
    root=Path(out)/'clock-journal';integrity=J.verify_journal(root,run,epoch,expected_commit=expected_anchor)
    if integrity['state']!='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH':raise ValueError('CLOCK_EXTERNAL_ANCHOR_REQUIRED')
    manifest=json.loads((root/'manifest.json').read_bytes())
    if manifest['policy']!=clock_policy(maximum_seconds).__dict__:raise ValueError('CLOCK_EXACT_CAPACITY_POLICY')
    from pilot.betaintegrated01.clock.correlation import Context,BoundedCorrelator
    from pilot.betaintegrated01.runtime.ap_stage import canonical
    context=Context(run,epoch,boot);emitted=[]
    correlator=BoundedCorrelator(context,('127.0.0.1',9014),emitted.append,max_pending=8,recent_limit=64)
    responses=OrderedDict();latest_response_sequence=None;publications={};events=registered=matched=0;binding=0;lastpub=None;origin=None;deferred=[]
    for p in sorted(root.glob('segment-*.jsonl')):
        with p.open('rb')as f:
            for line in f:
                row=json.loads(line);body=row['body']
                if body['kind']!='EVENT':continue
                events+=1
                if events>clock_events(maximum_seconds):raise ValueError('CLOCK_ALL_EVENTS_CAP')
                kind=body['payload']['eventKind'];d=body['payload']['data']
                if any(d.get(k)!=v for k,v in [('run',run),('epoch',epoch),('boot',boot)]):raise ValueError('CLOCK_CONTEXT')
                if kind=='CLOCK_OWNER_BINDING':
                    binding+=1;origin=d.get('originHostNs')
                    if binding!=1 or events!=1 or type(origin)is not int or origin<0 or d.get('sourceAmendmentSHA256')!=source_amendment or type(d.get('maximumEvents'))is not int or d['maximumEvents']!=clock_events(maximum_seconds)or type(d.get('maximumRecordBytes'))is not int or d['maximumRecordBytes']!=2048:raise ValueError('CLOCK_SOURCE_BINDING')
                elif kind=='CLOCK':
                    if binding!=1:raise ValueError('CLOCK_BINDING_REQUIRED')
                    event=d.get('kind')
                    # TIMEOUT is emitted by the next register/receive/tick operation;
                    # retain its exact row until that operation can reproduce it.
                    if event=='TIMEOUT':deferred.append(d);continue
                    emitted.clear()
                    if event=='REGISTERED':correlator.register(d['id'],d['hostSendNs'],context);registered+=1
                    elif event=='TICK':correlator.tick(d['hostNs'],context)
                    elif event in('RESPONSE','UNKNOWN_FUTURE_ID','RETIRED_OR_UNKNOWN'):
                        raw=bytes.fromhex(d['rawHex'])
                        if type(d.get('peer'))is not list:raise ValueError('CLOCK_PEER_SCHEMA')
                        correlator.receive(raw,tuple(d['peer']),d['hostNs'],context)
                    else:raise ValueError('CLOCK_FAILED_OR_UNKNOWN_EVENT_NOT_ACCEPTED')
                    expected=deferred+[d];deferred=[]
                    if canonical(emitted)!=canonical(expected):raise ValueError('CLOCK_CORRELATOR_REPLAY_MISMATCH')
                    if event=='RESPONSE'and d['freshCalibration']is True:
                        matched+=1;responses[body['seq']]={'data':d,'recordSHA256':row['sha256']};latest_response_sequence=body['seq']
                        while len(responses)>8:responses.popitem(last=False)
                elif kind=='CLOCK_PUBLICATION':
                    if deferred:raise ValueError('CLOCK_INCOMPLETE_OPERATION_BEFORE_PUBLICATION')
                    r=responses.get(d.get('responseSequence'))
                    if type(d.get('responseSequence'))is not int or d['responseSequence']!=latest_response_sequence or r is None or r['recordSHA256']!=d.get('responseSHA256'):raise ValueError('CLOCK_PUBLICATION_RESPONSE_HASH')
                    source=r['data']
                    if any(type(d.get(k))is not int or d[k]!=source[k]for k in('id','hostReceiveNs','offsetLowNs','offsetHighNs')):raise ValueError('CLOCK_PUBLICATION_BRACKET_MUTATION')
                    times=[d.get(k)for k in('responseDurableHostNs','publicationBeginHostNs')]
                    if any(type(t)is not int for t in times)or not source['hostReceiveNs']<=times[0]<=times[1]:raise ValueError('CLOCK_PUBLICATION_DURABLE_ORDER')
                    if lastpub is not None and d['id']<=lastpub:raise ValueError('CLOCK_PUBLICATION_REGRESSION')
                    lastpub=d['id'];publications[body['seq']]={'data':d,'recordSHA256':row['sha256']}
                else:raise ValueError('CLOCK_UNDECLARED_EVENT')
    if deferred or not binding or not publications:raise ValueError('CLOCK_INCOMPLETE_OR_NO_PUBLISHED_BRACKETS')
    return {'integrity':integrity,'publications':publications,'registered':registered,'matched':matched,'events':events,'sourceAmendmentSHA256':source_amendment,'originHostNs':origin,'semantics':'EXACT_FROZEN_BOUNDED_CORRELATOR_REPLAY_NOT_REMOTE_CLOCK_AUTHENTICATION'}


def verify_frame_reference(fields,origin,publications):
    if fields.get('clockAdmissionScopeVersion')!=9 or fields.get('clockAtOriginalReceiptStatus')!=0:raise ValueError('CLOCKPIPE09_STAGE_SEMANTICS_REQUIRED')
    for suffix,checkkey,agekey,idkey in [('Admission','clockCheckAtAdmissionSinceOriginNs','clockAgeAtAdmissionNs','clockIDAtAdmission'),('Send','clockCheckBeforeSendSinceOriginNs','clockAgeBeforeSendNs','clockIDBeforeSend')]:
        seq=fields.get('clockPublicationAt'+suffix);pub=publications.get(seq)
        if type(seq)is not int or pub is None:raise ValueError('FRAME_UNPUBLISHED_CLOCK_REFERENCE')
        d=pub['data'];complete=fields.get('clockPublicationCompleteAt'+suffix+'SinceOriginNs');checked=fields.get(checkkey)
        if type(complete)is not int or type(checked)is not int or complete<0 or not d['publicationBeginHostNs']<=origin+complete<=origin+checked:raise ValueError('FRAME_PUBLICATION_ORDER')
        if fields[idkey]!=d['id']or fields[agekey]!=origin+checked-d['hostReceiveNs']or not 0<=fields[agekey]<=250000000:raise ValueError('FRAME_CLOCK_FRESHNESS')
    sendpub=publications[fields['clockPublicationAtSend']]['data'];atomic=fields.get('clockAtomicPermitSinceOriginNs');atomicage=fields.get('clockAtomicPermitAgeNs')
    if type(atomic)is not int or type(atomicage)is not int or not fields['clockCheckBeforeSendSinceOriginNs']<=atomic<=fields['sendBeginSinceOriginNs']or atomicage!=origin+atomic-sendpub['hostReceiveNs']or not 0<=atomicage<=250000000:raise ValueError('ATOMIC_SEND_PERMIT_CLOCK_ORDER')
