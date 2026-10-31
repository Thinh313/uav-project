"""Bounded nonce correlation with raw records and a qualified Node bracket seam."""
import socket
import struct
import time
import json
import threading
import os
import select
import secrets
import sys


class Correlator:
    def __init__(self, peer, limit=1024):
        self.peer, self.limit = peer, limit
        self.requests = {}

    def register(self, rid, sent):
        if len(self.requests) >= self.limit or rid in self.requests:
            raise RuntimeError('Clock request bound/identity reuse')
        self.requests[rid] = {'sent': sent, 'received': False, 'timeout': False}

    def receive(self, data, addr, received):
        if addr != self.peer or len(data) != 56:
            raise RuntimeError('Foreign/malformed clock response')
        rid, g1, g2, usage, periods, throttles, throttled = struct.unpack('<7Q', data)
        if rid not in self.requests:
            raise RuntimeError('Unknown clock nonce')
        req = self.requests[rid]
        if g2 < g1 or received < req['sent']:
            raise RuntimeError('Clock timestamp regression')
        duplicate = req['received']
        req['received'] = True
        return {'id': rid, 'status': 'DUPLICATE_MATCHED' if duplicate else
                ('LATE_MATCHED' if req['timeout'] else 'MATCHED'),
                'hostSendNs': req['sent'], 'hostReceiveNs': received,
                'guestReceiveNs': g1, 'guestSendNs': g2,
                'offsetLowNs': req['sent']-g1, 'offsetHighNs': received-g2,
                'cgroupUsageUs': usage, 'cgroupPeriods': periods,
                'cgroupThrottles': throttles, 'cgroupThrottledUs': throttled,
                'freshCalibration': not duplicate and not req['timeout']}


class ClockObserver:
    def __init__(self, out, run, epoch, peer=('127.0.0.1',9004), cal_port=9005):
        self.out, self.run_id, self.epoch = out, run, epoch
        self.peer, self.cal_port = peer, cal_port
        self.stop = threading.Event()
        self.error = None
        self.rows = 0
        self.ready = threading.Event()
        self.domain = 'guest-python-monotonic' if sys.platform=='linux' else 'host-python-monotonic'
        self.thread = threading.Thread(target=self.work, daemon=True)
        self.thread.start()
        if not self.ready.wait(3) or self.error:
            raise RuntimeError('Clock observer startup: ' + str(self.error))

    def work(self):
        try:
            with (self.out/'clock-pairs.jsonl').open('x') as f, \
                 (self.out/'clock-raw.jsonl').open('x') as raw, \
                 (self.out/'node-calibration-server.jsonl').open('x') as cal, \
                 socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s, \
                 socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as n:
                n.bind(('0.0.0.0' if sys.platform=='linux' else '127.0.0.1',self.cal_port))
                s.setblocking(False);n.setblocking(False)
                correlator=Correlator(self.peer)
                seed=secrets.randbits(31)<<32
                seq=0;next_send=0
                self.ready.set()
                while not self.stop.is_set():
                    now=time.monotonic_ns()
                    if now>=next_send:
                        seq+=1;rid=seed+seq;correlator.register(rid,now)
                        s.sendto(struct.pack('<Q',rid),self.peer);next_send=now+333_333_333
                    for rid,r in correlator.requests.items():
                        if not r['received'] and not r['timeout'] and now-r['sent']>300_000_000:
                            r['timeout']=True
                            f.write(json.dumps({'id':rid,'hostSendNs':r['sent'],'status':'TIMEOUT',
                                                'hostClockDomain':self.domain})+'\n');self.rows+=1
                    ready,_,_=select.select([s,n],[],[],.05)
                    for source in ready:
                        data,addr=source.recvfrom(4096);received=time.monotonic_ns()
                        if source is s:
                            raw.write(json.dumps({'receiveNs':received,'peer':addr,'rawHex':data.hex(),
                                                  'clockDomain':self.domain})+'\n')
                            raw.flush()
                            row=correlator.receive(data,addr,received)
                            row.update(hostClockDomain=self.domain,guestClockDomain='guest-clock-monotonic')
                            if row['offsetLowNs']>row['offsetHighNs']:
                                raise RuntimeError('Inconsistent clock bracket')
                            f.write(json.dumps(row,separators=(',',':'))+'\n');self.rows+=1
                        else:
                            request=json.loads(data)
                            if request.get('run')!=self.run_id or request.get('epoch')!=self.epoch or \
                               not isinstance(request.get('nonce'),str) or len(request['nonce'])!=32:
                                cal.write(json.dumps({'status':'REJECTED_REQUEST','peer':addr,'rawHex':data.hex()})+'\n')
                                continue
                            reply={'run':self.run_id,'epoch':self.epoch,'nonce':request['nonce'],
                                   'backendReceiveNs':str(received),'backendSendNs':str(time.monotonic_ns()),
                                   'backendClockDomain':self.domain}
                            n.sendto(json.dumps(reply).encode(),addr)
                            cal.write(json.dumps(reply)+'\n')
                    f.flush();cal.flush()
                for stream in [f,raw,cal]:stream.flush();os.fsync(stream.fileno())
        except Exception as e:
            self.error=str(e);self.ready.set()
            with (self.out/'clock-error.json').open('x') as f:
                json.dump({'error':self.error,'clockDomain':self.domain,'atMonotonicNs':time.monotonic_ns()},f)

    def seal(self):
        self.stop.set();self.thread.join(3)
        if self.thread.is_alive() or self.error:
            raise RuntimeError('Clock observer failed '+str(self.error))
