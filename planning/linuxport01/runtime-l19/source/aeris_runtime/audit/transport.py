"""Exact old transport integrity receiver plus declared startup-envelope classification."""
from pathlib import Path
from collections import deque
import hashlib,json
from aeris_runtime.foundation.journal_base import verify_journal
from pilot.betaintegrated01.control01.mavlink import Framer
from aeris_runtime.audit.control import events,critical_fields,native_fields
from pilot.betaintegrated01.control05.bootstrap import StartupEnvelope

def audit_transport(out,run,epoch,boot,*,expected_anchor):
    root=Path(out)/'transport-journal'
    integrity=verify_journal(root,run,epoch,expected_commit=expected_anchor)
    if integrity['state']!='COMPLETE_RECORDING_EXTERNAL_ANCHOR_MATCH':raise ValueError('EXTERNAL_TRANSPORT_ANCHOR_REQUIRED')
    passive=Framer();envelope=StartupEnvelope();expected_prefix=deque();native=Framer();pending_passive=deque();pending_to_AP=b'';pending_to_native=b''
    active_intent=None;forwarded_AP=forwarded_native=0;closed_cut=None;cut_requested=False;failure_closed=None;eof=None;eof_pending=None;cut_request_seen=False
    timeline=[];native_timeline=[];seq=None;boot_by_id={};duplicates=older=0
    for kind,data in events(root):
        if data.get('_boot')!=boot or type(data.get('_observedHostNs'))is not int:raise ValueError('TRANSPORT_BOOT_OR_CLOCK_BINDING')
        now=data['_observedHostNs']
        cut_kind=kind in('CUT_REQUEST','CUT_ACCEPTED','CUT_CONNECTIONS_CLOSED')
        if eof is not None and cut_kind or cut_request_seen and kind in('NATIVE_PATH_EOF','NATIVE_FAILURE_CONNECTIONS_CLOSED')or(closed_cut is not None or failure_closed is not None)and cut_kind:raise ValueError('MUTUALLY_EXCLUSIVE_TERMINAL_FENCE_ROUTES')
        if eof is not None and kind in('NATIVE_CONNECTED','NATIVE_RX','AP_RELAY_RX','FORWARD_INTENT','FORWARD_LOCAL_RETURN','FORWARD_NOT_READY','FORWARD_UNKNOWN','NATIVE_PATH_EOF'):raise ValueError('NATIVE_OR_FORWARD_EVENT_AFTER_TERMINAL_EOF')
        if (closed_cut is not None or failure_closed is not None)and kind in('NATIVE_CONNECTED','NATIVE_RX','AP_RELAY_RX','FORWARD_INTENT','FORWARD_LOCAL_RETURN','FORWARD_NOT_READY','FORWARD_UNKNOWN','NATIVE_PATH_EOF','NATIVE_FAILURE_CONNECTIONS_CLOSED'):raise ValueError('POST_FENCE_RECONNECT_RX_OR_FORWARD')
        if kind=='PASSIVE_RX':
            if data.get('applicationTXBytes')!=0:raise ValueError('PASSIVE_TX_DECLARED')
            raw=bytes.fromhex(data['rawHex'])
            if len(raw)>4096:raise ValueError('PASSIVE_CHUNK_BOUND')
            mav,prefix=envelope.feed(raw,data['hostNs']);expected_prefix.extend(prefix)
            pending_passive.extend(passive.feed(mav,data['hostNs']))
            if len(pending_passive)>512:raise ValueError('PASSIVE_DECODE_QUEUE_BOUND')
        elif kind=='PASSIVE_BOOTSTRAP_PREFIX':
            if not expected_prefix:raise ValueError('BOOTSTRAP_CLASSIFICATION_WITHOUT_RAW')
            expected=expected_prefix.popleft()
            if any(data.get(k)!=v for k,v in expected.items()):raise ValueError('BOOTSTRAP_CLASSIFICATION_NOT_EXACT_RAW')
        elif kind=='PASSIVE_FRAME':
            if not pending_passive:raise ValueError('FRAME_WITHOUT_PASSIVE_RX')
            frame=pending_passive.popleft()
            if any(data.get(key)!=frame[key]for key in('id','system','component','wireSequence','wireHex','monotonicNs')):
                raise ValueError('STORED_FRAME_NOT_EQUAL_RAW')
            if frame['system']!=42 or frame['component']!=1:continue
            delta=None if seq is None else(frame['wireSequence']-seq)&255
            if delta==0:duplicates+=1;continue
            if delta is not None and delta>=128:older+=1;continue
            seq=frame['wireSequence'];fields=critical_fields(frame)
            if fields is not None:
                if 'bootMs'in fields:
                    if frame['id']in boot_by_id and fields['bootMs']<boot_by_id[frame['id']]:raise ValueError('AP_BOOT_REGRESSION_WITHIN_EPOCH')
                    boot_by_id[frame['id']]=fields['bootMs']
                timeline.append({'hostNs':frame['monotonicNs'],**fields})
                if len(timeline)>131072:raise ValueError('CONTROL_TIMELINE_BOUND_NO_SAMPLING')
        elif kind in('NATIVE_RX','AP_RELAY_RX'):
            raw=bytes.fromhex(data['rawHex'])
            if kind=='NATIVE_RX':
                if closed_cut is not None:raise ValueError('NATIVE_RX_AFTER_CUT')
                pending_to_AP+=raw
            else:pending_to_native+=raw
            if len(pending_to_AP)>16384 or len(pending_to_native)>16384:raise ValueError('FORWARD_BUFFER_BOUND')
        elif kind=='FORWARD_INTENT':
            if active_intent is not None:raise ValueError('UNRESOLVED_FORWARD_INTENT')
            direction=data['direction'];raw=bytes.fromhex(data['rawHex'])
            source=pending_to_AP if direction=='toAP'else pending_to_native
            if not raw or len(raw)>4096 or source[:len(raw)]!=raw:raise ValueError('FORWARD_BYTES_MUTATED_OR_GENERATED')
            if direction=='toAP'and closed_cut is not None:raise ValueError('SEND_AFTER_CUT')
            active_intent=(direction,raw)
        elif kind in('FORWARD_LOCAL_RETURN','FORWARD_NOT_READY'):
            if active_intent is None:raise ValueError('FORWARD_RETURN_WITHOUT_INTENT')
            direction,raw=active_intent
            if data['direction']!=direction:raise ValueError('FORWARD_DIRECTION')
            n=data['sentBytes']
            if type(n)is not int or not 0<=n<=len(raw)or(kind=='FORWARD_LOCAL_RETURN'and n==0):raise ValueError('FORWARD_COUNT')
            if direction=='toAP':
                pending_to_AP=pending_to_AP[n:];forwarded_AP+=n
                for frame in native.feed(raw[:n],now):
                    decoded=native_fields(frame)
                    if decoded:native_timeline.append({'hostNs':now,'wireSHA256':hashlib.sha256(bytes.fromhex(frame['wireHex'])).hexdigest(),**decoded})
                    if len(native_timeline)>131072:raise ValueError('NATIVE_TIMELINE_BOUND')
            else:pending_to_native=pending_to_native[n:];forwarded_native+=n
            active_intent=None
        elif kind=='FORWARD_UNKNOWN':raise ValueError('FORWARD_UNKNOWN_NOT_COMPLETE_ACCEPTANCE')
        elif kind=='CUT_REQUEST':
            if cut_request_seen:raise ValueError('MULTIPLE_CUT_REQUESTS')
            cut_request_seen=True
        elif kind=='CUT_ACCEPTED':
            if not cut_request_seen or cut_requested:raise ValueError('MULTIPLE_OR_UNREQUESTED_CUTS')
            cut_requested=True
        elif kind=='CUT_CONNECTIONS_CLOSED':
            if not cut_requested or closed_cut is not None:raise ValueError('CUT_CLOSE_ORDER')
            if not(type(data['closeStartedHostNs'])is int and type(data['closedHostNs'])is int and data['closeStartedHostNs']<=data['closedHostNs']<=now):
                raise ValueError('CUT_CLOSE_CLOCK')
            closed_cut=data['closedHostNs'];pending_to_AP=pending_to_native=b''
        elif kind=='NATIVE_PATH_EOF':
            if eof is not None or data.get('side')not in('native','upstream')or data.get('noRetry')is not True:raise ValueError('ORIGINAL_EOF_SCHEMA')
            pending=data.get('pending',{});original={'toAPBytes':len(pending_to_AP),'toAPSHA256':hashlib.sha256(pending_to_AP).hexdigest(),'toNativeBytes':len(pending_to_native),'toNativeSHA256':hashlib.sha256(pending_to_native).hexdigest()}
            if pending!=original:raise ValueError('EOF_PENDING_NOT_ORIGINAL_RAW')
            eof={'hostNs':now,'side':data['side']};eof_pending=original;pending_to_AP=pending_to_native=b''
        elif kind=='NATIVE_FAILURE_CONNECTIONS_CLOSED':
            start=data.get('closeStartedHostNs');closed=data.get('closedHostNs')
            if eof is None or active_intent is not None or eof_pending['toAPBytes']!=0 or any(type(v)is not int for v in(start,closed))or not eof['hostNs']<=start<=closed<=now:raise ValueError('FAILURE_FENCE_EOF_PENDING_OR_CLOCK')
            if data.get('sourceSide')!=eof['side']or data.get('pending')!=eof_pending or data.get('socketFDsClosed')is not True or data.get('nativeReconnectAllowed')is not False or data.get('FDMClockUntouched')is not True or type(data.get('applicationPassiveTXBytes'))is not int or data['applicationPassiveTXBytes']!=0 or data.get('restoredAuthority')is not False or data.get('pendingOutcome')!='NOT_RETRIED_UNKNOWN_IF_PARTIAL':raise ValueError('FAILURE_FENCE_CLOSE_SCHEMA')
            failure_closed=closed
        elif kind=='PASSIVE_TX':raise ValueError('PASSIVE_APPLICATION_TX_FORBIDDEN')
    if expected_prefix:raise ValueError('BOOTSTRAP_RAW_NOT_CLASSIFIED')
    if pending_passive:raise ValueError('UNCONSUMED_PASSIVE_FRAMES')
    if active_intent is not None:raise ValueError('UNRESOLVED_FINAL_FORWARD')
    return {'status':'RAW_TRANSPORT_INTEGRITY_AND_UNMODIFIED_FORWARDING_PASS','passiveApplicationTXBytes':0,
            'passiveTimeline':timeline,'nativeForwardedTimeline':native_timeline,'cutClosedHostNs':closed_cut,'failureClosedHostNs':failure_closed,
            'nativeBytesForwarded':forwarded_AP,'APBytesForwarded':forwarded_native,'duplicatesIgnored':duplicates,
            'olderOrAmbiguousIgnored':older,'partialPassiveBytesAtOwnedStop':len(passive.pending),
            'partialNativeBytesAtOwnedStop':len(native.pending),'authorityGranted':False,
            'startupResetPairsClassified':envelope.pairs,'startupRawBytesRetained':envelope.pairs*2,
            'sourceAuthenticity':'LOCAL_PINNED_ORCHESTRATION_NOT_REMOTE_AUTHENTICATION'}
