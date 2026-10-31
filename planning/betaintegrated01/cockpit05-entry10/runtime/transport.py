"""Transparent native transport fault seam + strictly receive-only AP observer.

This module does not create MAVLink messages. TCP forwarding retains native
bytes unchanged; the passive channel never transmits application bytes.
"""
from pathlib import Path
from dataclasses import dataclass
import hashlib
import json
import os
import selectors
import socket
import threading
import time
from .journal import SegmentedJournal,Policy
from pilot.betaintegrated01.runtime.ap_stage import canonical,exclusive
from pilot.betaintegrated01.control01.mavlink import Framer,observe
from pilot.betaintegrated01.control05.bootstrap import StartupEnvelope
from pilot.betaintegrated01.cockpit04.capacity import transport_policy


@dataclass(frozen=True)
class Context:
    run:str
    epoch:str
    boot:str


class FaultState:
    def __init__(self,context):
        self.context=context;self.cut_latched=False;self.accepted_nonce=None

    def cut(self,request,now_ns):
        if self.cut_latched:raise ValueError('CUT_ALREADY_LATCHED_NO_RESTORE')
        if type(request)is not dict or set(request)!={'run','epoch','boot','action','nonce','hostNs'}:
            raise ValueError('CUT_SCHEMA')
        if any(request[k]!=getattr(self.context,k) for k in ('run','epoch','boot')):
            raise ValueError('FOREIGN_CUT_CONTEXT')
        if request['action']!='CUT_NATIVE_LINK':raise ValueError('CUT_ACTION')
        if type(request['nonce'])is not str or not 1<=len(request['nonce'])<=64:
            raise ValueError('CUT_NONCE')
        if type(request['hostNs'])is not int or type(now_ns)is not int or not 0<=now_ns-request['hostNs']<=2_000_000_000:
            raise ValueError('STALE_OR_FUTURE_CUT')
        self.cut_latched=True;self.accepted_nonce=request['nonce']
        return {'action':'CUT_NATIVE_LINK','nativeReconnectAllowed':False,'restoredAuthority':False}


class PassiveObservation:
    """No socket sender or encoder is part of this API."""
    def __init__(self,record):
        self.framer=Framer();self.envelope=StartupEnvelope();self.record=record;self.latest={};self.received_bytes=0
        self.frames=0;self.foreign=0;self.application_tx_bytes=0
        self.last_sequence=None;self.duplicate_frames=0;self.older_frames=0;self.sequence_gaps=0
        self.boot_by_id={};self.boot_regression=None

    def receive(self,raw,now_ns):
        self.record('PASSIVE_RX',{'hostNs':now_ns,'rawHex':raw.hex(),'applicationTXBytes':0})
        self.received_bytes+=len(raw)
        mav_bytes,prefix=self.envelope.feed(raw,now_ns)
        for classified in prefix:self.record('PASSIVE_BOOTSTRAP_PREFIX',classified)
        for frame in self.framer.feed(mav_bytes,now_ns):
            item=observe(frame);self.frames+=1;classification='FOREIGN_SOURCE'
            accepted=False
            if item['expectedAPSource']:
                seq=item['wireSequence']
                delta=None if self.last_sequence is None else(seq-self.last_sequence)&255
                if delta==0:
                    self.duplicate_frames+=1;classification='DUPLICATE_NO_FRESHNESS_REFRESH'
                elif delta is not None and delta>=128:
                    self.older_frames+=1;classification='OLDER_OR_HALF_RANGE_AMBIGUOUS_NO_REFRESH'
                else:
                    classification='FIRST'if delta is None else'NEW'if delta==1 else'NEW_WITH_SEQUENCE_GAP'
                    if delta is not None and delta>1:self.sequence_gaps+=delta-1
                    self.last_sequence=seq;accepted=True
                    fields=item['fields']
                    if fields is not None and 'bootMs'in fields:
                        previous=self.boot_by_id.get(item['id'])
                        if previous is not None and fields['bootMs']<previous:
                            self.boot_regression={'id':item['id'],'previousBootMs':previous,'observedBootMs':fields['bootMs']}
                            classification='AP_BOOT_REGRESSION_NEW_EPOCH_REQUIRED';accepted=False
                        else:self.boot_by_id[item['id']]=fields['bootMs']
            item['observationClass']=classification
            item['newSequenceObservation']=accepted
            self.record('PASSIVE_FRAME',item)
            if self.boot_regression is not None:raise RuntimeError('PASSIVE_AP_BOOT_REGRESSION_NEW_EPOCH_REQUIRED')
            if accepted and item['fields']is not None:
                fields={**item['fields'],'observedHostNs':now_ns,'wireSequence':item['wireSequence']}
                self.latest[fields['kind']]=fields
            elif not item['expectedAPSource']:
                self.foreign+=1

    def snapshot(self):
        return {'startupPairs':self.envelope.pairs,'startupPending':self.envelope.pending_ns is not None,'mavStarted':self.envelope.mav_started,'receivedBytes':self.received_bytes,'frames':self.frames,'foreignSources':self.foreign,
                'applicationTXBytes':0,'latest':dict(self.latest),'framer':self.framer.snapshot(),
                'duplicateFrames':self.duplicate_frames,'olderOrAmbiguousFrames':self.older_frames,
                'sequenceGaps':self.sequence_gaps,'bootRegression':self.boot_regression,
                'latestQualifiedForFlightAuthority':False,'authorityGranted':False}



class PassiveStartup:
    """Retry only the pre-byte TCP-proxy startup state, never an AP stream."""
    maximum_wait_ns=20_000_000_000
    maximum_attempts=200
    def __init__(self):self.started_ns=None;self.bytes_seen=0;self.eofs=0;self.mav_seen=False
    def begin(self,now_ns):self.started_ns=now_ns
    def check(self,now_ns):
        if self.mav_seen:return
        if self.started_ns is None or not 0<=now_ns-self.started_ns<=self.maximum_wait_ns:
            raise RuntimeError('PASSIVE_INITIAL_OBSERVATION_TIMEOUT_20S')
    def receive(self,raw):
        # Latch on ANY byte before parse, including foreign/partial/invalid data.
        self.bytes_seen+=len(raw)
    def eof(self,now_ns):
        if self.bytes_seen:raise RuntimeError('PASSIVE_AP_EOF_NEW_EPOCH_REQUIRED')
        self.check(now_ns);self.eofs+=1
        return {'initialEOFNumber':self.eofs,'beforeAnyAPByte':True,'applicationTXBytes':0,
                'elapsedStartupNs':now_ns-self.started_ns,'retryPolicy':'BOUNDED_INITIAL_TCP_PROXY_ONLY'}

class TransportHub:
    """One owned thread/epoch, independently primed real guard and bounded logs."""
    def __init__(self,out,run,epoch,boot,maximum_seconds):
        self.out=Path(out);self.context=Context(run,epoch,boot);self.maximum_seconds=maximum_seconds
        self.stop_event=threading.Event();self.ready=threading.Event();self.done=threading.Event()
        self.thread=threading.Thread(target=self._run,name='m1-control-transport',daemon=True)
        self.error=None;self.result=None;self.journal=None;self.passive=None
        self.state=FaultState(self.context);self.pending_to_AP=b'';self.pending_to_native=b''
        self.native_forwarded=self.AP_forwarded=0;self.native_chunks=0;self.passive_connect_attempts=0
        self.passive_connected=False;self.native_connected=False;self._last_publish=0
        self.passive_startup=PassiveStartup()
        self._state_lock=threading.Lock();self._snapshot={'ready':False,'applicationPassiveTXBytes':0}
        if (self.out/'cut-request.json').exists():raise ValueError('PREEXISTING_CUT_REQUEST')

    def start(self):self.thread.start()

    def snapshot(self):
        with self._state_lock:return json.loads(json.dumps(self._snapshot))

    def _record(self,kind,data):self.journal.append_event(kind,{**data,'_boot':self.context.boot,'_observedHostNs':time.monotonic_ns()})

    def _retain_pending(self,reason):
        summary={}
        for direction,body in (('toAP',self.pending_to_AP),('toNative',self.pending_to_native)):
            summary[direction+'Bytes']=len(body);summary[direction+'SHA256']=hashlib.sha256(body).hexdigest()
            for offset in range(0,len(body),4096):
                self._record('PENDING_FORWARD_BYTES',{'direction':direction,'offset':offset,
                             'rawHex':body[offset:offset+4096].hex(),'reason':reason,'neverReplayed':True})
        return summary

    def _publish(self,force=False):
        now=time.monotonic()
        if not force and now-self._last_publish<.5:return
        state={'run':self.context.run,'epoch':self.context.epoch,'boot':self.context.boot,
               'ready':self.ready.is_set(),'error':self.error,'nativeConnected':self.native_connected,
               'passiveConnected':self.passive_connected,'cutLatched':self.state.cut_latched,
               'nativeBytesForwardedUnmodified':self.native_forwarded,'APBytesForwardedUnmodified':self.AP_forwarded,
               'passiveConnectAttempts':self.passive_connect_attempts,'applicationPassiveTXBytes':0,
               'initialPassiveEOFs':self.passive_startup.eofs,'passiveBytesEverObserved':self.passive_startup.bytes_seen,
               'passive':self.passive.snapshot()if self.passive else None,'observedHostNs':time.monotonic_ns(),
               'source':'MUTABLE_PROJECTION_RAW_JOURNAL_IS_AUTHORITY'}
        with self._state_lock:self._snapshot=state
        body=canonical(state)+b'\n';self.journal.guard.check(len(body))
        temp=self.out/'transport-state.tmp';fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        try:
            view=memoryview(body)
            while view:
                n=os.write(fd,view)
                if n<=0:raise OSError('PROJECTION_SHORT_WRITE')
                view=view[n:]
            os.fsync(fd)
        finally:os.close(fd)
        os.replace(temp,self.out/'transport-state.json');self._last_publish=now

    def _run(self):
        selector=selectors.DefaultSelector();listener=native=upstream=passive_socket=None
        started=time.monotonic();next_passive_connect=0;cut_seen=False
        try:
            self.journal=SegmentedJournal(self.out/'transport-journal',self.context.run,self.context.epoch,
                         transport_policy(self.maximum_seconds))
            self.passive=PassiveObservation(self._record)
            listener=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(('127.0.0.1',5961));listener.listen(2);listener.setblocking(False)
            selector.register(listener,selectors.EVENT_READ,'listener')
            self._record('HUB_READY',{'nativeListen':['127.0.0.1',5961],'APUpstream':['127.0.0.1',5963],
                                     'passiveEndpoint':['127.0.0.1',5962],'passiveApplicationTXBytes':0,
                                     'guardPriming':self.journal.guard.prime_receipt})
            self.ready.set();self._publish(force=True);started=time.monotonic()
            self.passive_startup.begin(time.monotonic_ns())

            def close_connection(sock):
                if sock is None:return
                try:selector.unregister(sock)
                except KeyError:pass
                try:sock.shutdown(socket.SHUT_RDWR)
                except OSError:pass
                sock.close()

            while not self.stop_event.is_set():
                self.journal.guard.check()
                now=time.monotonic()
                if now-started>self.maximum_seconds+20:raise RuntimeError('TRANSPORT_MAXIMUM_LIFETIME')
                self.passive.framer.tick(time.monotonic_ns())
                self.passive.envelope.tick(time.monotonic_ns())
                self.passive_startup.check(time.monotonic_ns())
                request_path=self.out/'cut-request.json'
                if request_path.exists() and not cut_seen:
                    raw=request_path.read_bytes()
                    if len(raw)>2048:raise ValueError('CUT_FILE_BOUND')
                    try:request=json.loads(raw)
                    except json.JSONDecodeError:request=None
                    if request is not None:
                        self._record('CUT_REQUEST',request)
                        outcome=self.state.cut(request,time.monotonic_ns())
                        pending=self._retain_pending('ROOT_INTENTIONAL_NATIVE_LINK_CUT')
                        self._record('CUT_ACCEPTED',{**outcome,'pending':pending,'pendingOutcome':'NOT_RETRIED_UNKNOWN_IF_PARTIAL'})
                        closing_ns=time.monotonic_ns()
                        close_connection(native);close_connection(upstream);native=upstream=None
                        self.pending_to_AP=self.pending_to_native=b''
                        self.native_connected=False;cut_seen=True
                        self._record('CUT_CONNECTIONS_CLOSED',{'closeStartedHostNs':closing_ns,
                                     'closedHostNs':time.monotonic_ns(),'applicationPassiveTXBytes':0,
                                     'nativeReconnectAllowed':False,'FDMClockUntouched':True})
                if passive_socket is None and now>=next_passive_connect:
                    self.passive_connect_attempts+=1
                    if self.passive_connect_attempts>self.passive_startup.maximum_attempts:raise RuntimeError('PASSIVE_CONNECT_ATTEMPT_BOUND')
                    candidate=socket.socket(socket.AF_INET,socket.SOCK_STREAM);candidate.settimeout(.15)
                    try:candidate.connect(('127.0.0.1',5962))
                    except OSError as exc:
                        candidate.close();self._record('PASSIVE_CONNECT_WAIT',{'attempt':self.passive_connect_attempts,
                                                'errorType':type(exc).__name__,'applicationTXBytes':0})
                        next_passive_connect=now+.1
                    else:
                        passive_socket=candidate;passive_socket.setblocking(False);self.passive_connected=True
                        selector.register(passive_socket,selectors.EVENT_READ,'passive')
                        self._record('PASSIVE_CONNECTED',{'applicationTXBytes':0,'noRequestsOrHeartbeat':True})
                for channel,role,source_buffer,destination_buffer in (
                    (native,'native',self.pending_to_AP,self.pending_to_native),
                    (upstream,'upstream',self.pending_to_native,self.pending_to_AP)):
                    if channel is None:continue
                    events=(selectors.EVENT_READ if len(source_buffer)<16384 else 0)|(selectors.EVENT_WRITE if destination_buffer else 0)
                    try:selector.get_key(channel)
                    except KeyError:
                        if events:selector.register(channel,events,role)
                    else:
                        if events:selector.modify(channel,events,role)
                        else:selector.unregister(channel)
                for key,mask in selector.select(.02):
                    sock=key.fileobj;role=key.data
                    if role=='listener':
                        client,address=listener.accept()
                        if self.state.cut_latched or native is not None or address[0]!='127.0.0.1':
                            client.close();self._record('NATIVE_CONNECTION_REFUSED',{'cutLatched':self.state.cut_latched,'peer':repr(address)});continue
                        server=socket.socket(socket.AF_INET,socket.SOCK_STREAM);server.settimeout(.15)
                        try:server.connect(('127.0.0.1',5963))
                        except OSError:
                            client.close();server.close();raise RuntimeError('NATIVE_CONNECT_BEFORE_AP_UPSTREAM_READY')
                        native,upstream=client,server;native.setblocking(False);upstream.setblocking(False)
                        self.native_connected=True
                        selector.register(native,selectors.EVENT_READ,'native');selector.register(upstream,selectors.EVENT_READ,'upstream')
                        self._record('NATIVE_CONNECTED',{'peer':repr(address),'upstream':['127.0.0.1',5963],'authorityGranted':False});continue
                    if role=='passive':
                        try:raw=passive_socket.recv(4096)
                        except BlockingIOError:continue
                        if not raw:
                            self._record('PASSIVE_EOF',{'pendingBytes':len(self.passive.framer.pending),'applicationTXBytes':0})
                            close_connection(passive_socket);passive_socket=None;self.passive_connected=False
                            retry=self.passive_startup.eof(time.monotonic_ns())
                            self._record('PASSIVE_INITIAL_EOF_RETRY',retry)
                            next_passive_connect=time.monotonic()+.1
                            continue
                        self.passive_startup.receive(raw)
                        self.passive.receive(raw,time.monotonic_ns());self.passive_startup.mav_seen=self.passive.envelope.mav_started;continue
                    if sock not in (native,upstream):continue
                    if mask&selectors.EVENT_READ:
                        buffer=self.pending_to_AP if role=='native' else self.pending_to_native
                        if len(buffer)<16384:
                            try:raw=sock.recv(min(4096,16384-len(buffer)))
                            except BlockingIOError:raw=None
                            if raw==b'':
                                pending=self._retain_pending('NATIVE_PATH_EOF')
                                self._record('NATIVE_PATH_EOF',{'side':role,'pending':pending,'noRetry':True})
                                close_connection(native);close_connection(upstream);native=upstream=None
                                self.pending_to_AP=self.pending_to_native=b''
                                self.native_connected=False
                                continue
                            if raw:
                                self._record('NATIVE_RX'if role=='native'else'AP_RELAY_RX',{'rawHex':raw.hex(),'hostNs':time.monotonic_ns()})
                                if role=='native':self.pending_to_AP+=raw;self.native_chunks+=1
                                else:self.pending_to_native+=raw
                    for destination,direction in ((upstream,'toAP'),(native,'toNative')):
                        if destination is None:continue
                        data=self.pending_to_AP if direction=='toAP'else self.pending_to_native
                        if not data:continue
                        part=data[:4096]
                        self._record('FORWARD_INTENT',{'direction':direction,'rawHex':part.hex(),'generatedMAVLink':False})
                        try:sent=destination.send(part)
                        except BlockingIOError:
                            self._record('FORWARD_NOT_READY',{'direction':direction,'sentBytes':0});continue
                        except Exception as exc:
                            self._record('FORWARD_UNKNOWN',{'direction':direction,'errorType':type(exc).__name__,'noRetry':True});raise
                        if sent<=0:raise RuntimeError('FORWARD_LOCAL_RETURN_UNKNOWN')
                        self._record('FORWARD_LOCAL_RETURN',{'direction':direction,'sentBytes':sent,'notAPExecutionEvidence':True})
                        if direction=='toAP':self.pending_to_AP=data[sent:];self.native_forwarded+=sent
                        else:self.pending_to_native=data[sent:];self.AP_forwarded+=sent
                self._publish()
            pending=self._retain_pending('HUB_OWNED_STOP')
            self._record('HUB_STOP',{'pending':pending,
                                    'applicationPassiveTXBytes':0,'authorityRestored':False})
            for sock in (native,upstream,passive_socket,listener):close_connection(sock)
            native=upstream=passive_socket=listener=None
            commit=self.journal.close()
            self.result={'status':'TRANSPORT_CLOSED_BYTES_NOT_FLIGHT_ACCEPTANCE','commitAnchor':commit['commitAnchor'],
                         'nativeBytesForwardedUnmodified':self.native_forwarded,'APBytesForwardedUnmodified':self.AP_forwarded,
                         'passive':self.passive.snapshot(),'cutLatched':self.state.cut_latched,'applicationPassiveTXBytes':0}
        except Exception as exc:
            self.error=type(exc).__name__+':'+str(exc)
            if self.journal is not None:
                try:self.journal.abort(self.error)
                except Exception:pass
            self.result={'status':'TRANSPORT_FAILED_RETAINED_PREFIX','error':self.error,'applicationPassiveTXBytes':0,
                         'guardDiagnostic':getattr(exc,'diagnostic',None)}
        finally:
            for sock in (native,upstream,passive_socket,listener):
                if sock is not None:
                    try:sock.close()
                    except OSError:pass
            selector.close();self.done.set()
            result={**(self.result or {}),'run':self.context.run,'epoch':self.context.epoch,'boot':self.context.boot}
            exclusive(self.out/'transport-result.json',canonical(result)+b'\n')

    def stop(self):
        self.stop_event.set();self.thread.join(4)
        if self.thread.is_alive():raise RuntimeError('TRANSPORT_THREAD_NOT_CLOSED')
        if self.error:raise RuntimeError(self.error)
        return self.result
