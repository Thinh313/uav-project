"""Pass the AP's JSON physics packets between the Docker bridge and the owner's backend on 127.0.0.1 (LINUXPORT01, G2/G3 port; team tool;
not harness evidence; the user's decision "R: forwarder", not the owner's).

Why: the owner's AP (in a container) sends its servo packets (UDP, 1200/s, lockstep) to JSON:192.168.65.254 port 9012. On his Mac, Docker
Desktop passes that address on to the Mac's 127.0.0.1, where his backend listens (bind allowlist 127.0.0.1:9012) and sees the AP as
127.0.0.1:<port>. On Linux a container cannot reach the host's 127.0.0.1, only the bridge address (docker0, 172.17.0.1). This tool takes
the place of Docker Desktop's pass-through: it listens on LISTEN_IP:LISTEN_PORT, sends every datagram unchanged to 127.0.0.1:BACKEND_PORT
from one fixed 127.0.0.1 socket, and sends every reply unchanged back to the AP. The backend, its allowlist and its peer lock stay as the
owner wrote them. (The AP's argv must name LISTEN_IP instead of 192.168.65.254: a separate declared patch, not done here.)

Rules it keeps (fail closed; any stop but a signal ends forwarding for good, so the backend's own SERVO_STALE_3S fails the run):
 - the first sender becomes the AP peer; with --subnet it must be inside that network, else stop PEER_OUTSIDE_SUBNET;
 - a datagram from any other sender: stop FOREIGN_PEER (the backend's own rule is FOREIGN_SERVO_PEER); it is not passed on;
 - one datagram in, one out, whole (up to 65535 B, so the backend's own 1024 B truncation check still sees the real size); never
   repeated, never held back; a short send stops it (SHORT_SEND);
 - backend port closed (ICMP refused): stop BACKEND_REFUSED; a backend datagram before any AP peer: stop BACKEND_PACKET_WITHOUT_PEER;
 - with --device the listening socket takes packets only from that interface (SO_BINDTODEVICE, e.g. docker0);
 - nothing is written to disk; counters and a 1 us histogram of its own handling time (receive returned -> send returned) stay in
   memory and are printed at the end. Stops cleanly on SIGTERM/SIGINT (exit 0); exit 3 peer rule, 4 backend refused, 5 other.
Limit: the backend's receive time for each servo packet is taken after this extra hop (the owner's Mac also has a hop there).

Output: one 'ready' line (actual ports) when listening, one 'summary' line at the end (JSON).
Usage: sitl_json_udp_forwarder.py LISTEN_IP LISTEN_PORT BACKEND_PORT [--device DEV] [--subnet CIDR]
       sitl_json_udp_forwarder.py --selftest                  (loopback only, ephemeral ports: function and fail-closed rules)
       sitl_json_udp_forwarder.py --bench FRAMES RATE ROUNDS  (loopback only: round-trip time direct vs through the forwarder)
       sitl_json_udp_forwarder.py --echo                      (internal: fake backend for --selftest/--bench)
"""
import hashlib,ipaddress,json,os,platform,select,signal,socket,struct,subprocess,sys,time
SERVO=struct.Struct('<HHI16H');PAD=bytes(range(256))+bytes(36);now=time.perf_counter_ns
def hist_stats(h,n,total,mx):
 if not n:return None
 def q(p):
  c=0
  for i,v in enumerate(h):
   c+=v
   if c>=p*n:return i
 return {'meanUs':round(total/n/1000,3),'p50Us':q(.5),'p99Us':q(.99),'maxUs':round(mx/1000,3),'histogramTopBucketIsOverflow':2001}
def forward(listen_ip,listen_port,backend_port,device,subnet):
 net=ipaddress.ip_network(subnet) if subnet else None
 front=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);back=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
 if device:front.setsockopt(socket.SOL_SOCKET,socket.SO_BINDTODEVICE,device.encode()+b'\0')
 front.bind((listen_ip,listen_port));back.bind(('127.0.0.1',0));back.connect(('127.0.0.1',backend_port))
 stop={'why':None}
 def on_signal(number,frame):stop['why']=stop['why'] or 'SIGNAL'
 signal.signal(signal.SIGTERM,on_signal);signal.signal(signal.SIGINT,on_signal)
 ep=select.epoll();ff=front.fileno();ep.register(ff,select.EPOLLIN);ep.register(back.fileno(),select.EPOLLIN)
 H=[[0]*2002,[0]*2002];N=[0,0];B=[0,0];T=[0,0];MX=[0,0];peer=None;refused=None;started=time.monotonic()
 def refuse(data,addr):return {'peer':list(addr),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 print(json.dumps({'kind':'ready','tool':'sitl_json_udp_forwarder.py','pid':os.getpid(),'listen':list(front.getsockname()),'port':front.getsockname()[1],
  'backSocket':list(back.getsockname()),'backend':['127.0.0.1',backend_port],'device':device,'subnet':subnet}),flush=True)
 while stop['why'] is None:
  for fd,event in ep.poll(.2):
   if fd==ff:
    data,addr=front.recvfrom(65535);t=now()
    if peer is None:
     if net is not None and ipaddress.ip_address(addr[0]) not in net:refused=refuse(data,addr);stop['why']='PEER_OUTSIDE_SUBNET';break
     peer=addr
    elif addr!=peer:refused=refuse(data,addr);stop['why']='FOREIGN_PEER';break
    try:sent=back.send(data)
    except ConnectionRefusedError:stop['why']='BACKEND_REFUSED';break
    d=0
   else:
    try:data=back.recv(65535)
    except ConnectionRefusedError:stop['why']='BACKEND_REFUSED';break
    t=now()
    if peer is None:stop['why']='BACKEND_PACKET_WITHOUT_PEER';break
    sent=front.sendto(data,peer);d=1
   if sent!=len(data):stop['why']='SHORT_SEND';break
   e=now()-t;N[d]+=1;B[d]+=len(data);T[d]+=e;H[d][min(e//1000,2001)]+=1
   if e>MX[d]:MX[d]=e
 why=stop['why'];front.close();back.close()
 print(json.dumps({'kind':'summary','stopped':why,'peer':peer and list(peer),'refused':refused,'seconds':round(time.monotonic()-started,3),
  'toBackend':{'packets':N[0],'bytes':B[0],'handle':hist_stats(H[0],N[0],T[0],MX[0])},'toAP':{'packets':N[1],'bytes':B[1],'handle':hist_stats(H[1],N[1],T[1],MX[1])}}))
 return 0 if why=='SIGNAL' else 3 if why in('PEER_OUTSIDE_SUBNET','FOREIGN_PEER') else 4 if why=='BACKEND_REFUSED' else 5
def echo():
 """Fake backend: replies to each datagram with its first 8 bytes + 292 fixed bytes; remembers senders and frame order."""
 stop=[];signal.signal(signal.SIGTERM,lambda n,f:stop.append(1));signal.signal(signal.SIGINT,lambda n,f:stop.append(1))
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(.2);peers=[];n=0;last={};ordered=True
 print(json.dumps({'kind':'ready','port':s.getsockname()[1]}),flush=True)
 while not stop:
  try:data,addr=s.recvfrom(65535)
  except TimeoutError:continue
  if addr not in peers and len(peers)<8:peers.append(addr)
  if len(data)==SERVO.size:
   frame=SERVO.unpack(data)[2]
   if addr in last and frame!=last[addr]+1:ordered=False
   last[addr]=frame
  n+=1;s.sendto(data[:8]+PAD,addr)
 print(json.dumps({'kind':'echo','packets':n,'peers':[list(p) for p in peers],'framesInOrderPerPeer':ordered}));return 0
def spawn(*args):
 p=subprocess.Popen([sys.executable,'-I','-B',os.path.abspath(__file__),*map(str,args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 line=p.stdout.readline()
 if not line:raise RuntimeError('child did not start: '+p.communicate()[1][-400:])
 return p,json.loads(line)
def finish(p,sig=signal.SIGTERM):
 if sig is not None and p.poll() is None:p.send_signal(sig)
 out,err=p.communicate(timeout=10);return p.returncode,[json.loads(l) for l in out.splitlines() if l.startswith('{')][-1]
def packet(frame):return SERVO.pack(18458,1200,frame,*[1000+(frame*(i+1)*17%901) for i in range(16)])
def client(sock,target,first,frames,rate=0):
 """Fake AP: lockstep, one servo packet out, wait for its reply; returns round-trip times (ns), wrong replies, first timeout."""
 rt=[];bad=0;tick=time.perf_counter()
 for frame in range(first,first+frames):
  if rate:
   while (wait:=tick-time.perf_counter())>0:time.sleep(wait)
   tick+=1/rate
  raw=packet(frame);t=now();sock.sendto(raw,target)
  try:reply,addr=sock.recvfrom(65535)
  except TimeoutError:return rt,bad,frame
  rt.append(now()-t)
  if addr!=target or reply!=raw[:8]+PAD:bad+=1
 return rt,bad,None
def ap_socket():s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.bind(('127.0.0.1',0));s.settimeout(1);return s
def start_forwarder(port,subnet='127.0.0.0/8'):
 """Forwarder on loopback with --device lo when the kernel lets an unprivileged process do it; else without (reported)."""
 try:return (*spawn('127.0.0.1',0,port,'--subnet',subnet,'--device','lo'),True)
 except RuntimeError:return (*spawn('127.0.0.1',0,port,'--subnet',subnet),False)
def us(ns):
 if not ns:return None
 s=sorted(ns);q=lambda p:round(s[min(len(s)-1,int(p*len(s)))]/1000,3)
 return {'n':len(s),'meanUs':round(sum(s)/len(s)/1000,3),'p50Us':q(.5),'p99Us':q(.99),'p999Us':q(.999),'maxUs':round(s[-1]/1000,3)}
def selftest():
 checks=[]
 e,er=spawn('--echo');f,fr,dev=start_forwarder(er['port']);a=ap_socket();target=('127.0.0.1',fr['port'])
 rt,bad,timeout=client(a,target,0,300);assert len(rt)==300 and bad==0 and timeout is None,(len(rt),bad,timeout)
 checks.append('300 lockstep packets through the forwarder: every reply right, none lost')
 b=ap_socket();b.sendto(packet(300),target);code,s=finish(f,None)
 assert code==3 and s['stopped']=='FOREIGN_PEER' and s['refused']['peer']==list(b.getsockname()) and s['toBackend']['packets']==300 and s['toAP']['packets']==300,s
 assert s['peer']==list(a.getsockname()) and s['toBackend']['bytes']==300*SERVO.size and s['toAP']['bytes']==300*300,s
 code,es=finish(e);assert es['packets']==300 and es['peers']==[fr['backSocket']] and es['framesInOrderPerPeer'] and fr['backSocket'][1]!=a.getsockname()[1],es
 checks+=['second sender: stop FOREIGN_PEER, exit 3, its packet not passed on','backend saw exactly one sender, the forwarder\'s 127.0.0.1 socket, frames in order']
 e,er=spawn('--echo');f,fr,_=start_forwarder(er['port'],'10.0.0.0/8');a.sendto(packet(0),('127.0.0.1',fr['port']));code,s=finish(f,None);_,es=finish(e)
 assert code==3 and s['stopped']=='PEER_OUTSIDE_SUBNET' and s['toBackend']['packets']==0 and es['packets']==0,(s,es)
 checks.append('first sender outside --subnet: stop PEER_OUTSIDE_SUBNET, nothing passed on')
 closed=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);closed.bind(('127.0.0.1',0));port=closed.getsockname()[1];closed.close()
 f,fr,_=start_forwarder(port);a.sendto(packet(0),('127.0.0.1',fr['port']));code,s=finish(f,None)
 assert code==4 and s['stopped']=='BACKEND_REFUSED' and s['toAP']['packets']==0,s
 checks.append('backend port closed: stop BACKEND_REFUSED, exit 4')
 f,fr,_=start_forwarder(port);code,s=finish(f);assert code==0 and s['stopped']=='SIGNAL' and s['toBackend']['packets']==0,s
 checks.append('SIGTERM while idle: clean stop, exit 0')
 assert hist_stats([0,3,1],4,8000,4000)=={'meanUs':2.0,'p50Us':1,'p99Us':2,'maxUs':4.0,'histogramTopBucketIsOverflow':2001}
 print(json.dumps({'selftest':'PASS','deviceBindTested':dev,'checks':checks}));return 0
def bench(frames,rate,rounds,warm=200):
 e,er=spawn('--echo');f,fr,dev=start_forwarder(er['port']);direct=('127.0.0.1',er['port']);via=('127.0.0.1',fr['port']);sa=ap_socket();sb=ap_socket()
 cpu=next((l.split(':',1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')),None)
 print(json.dumps({'kind':'header','tool':'sitl_json_udp_forwarder.py --bench','started':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'python':sys.version.split()[0],
  'machine':platform.machine(),'cpu':cpu,'frames':frames,'rate':rate,'rounds':rounds,'warmFramesDiscardedPerBlock':warm,'servoBytes':SERVO.size,'replyBytes':8+len(PAD),
  'deviceBind':dev,'forwarder':fr}),flush=True)
 R={'direct':[],'via':[]};bad=0;timeouts=[];first={'direct':0,'via':0}
 for r in range(rounds):
  for name,sock,target in(('direct',sa,direct),('via',sb,via)):
   rt,b,t=client(sock,target,first[name],warm+frames,rate);first[name]+=warm+frames;bad+=b
   if t is not None:timeouts.append({'round':r,'path':name,'frame':t})
   R[name]+=rt[warm:];print(json.dumps({'kind':'block','round':r,'path':name,'roundTrip':us(rt[warm:]),'wrongReplies':b,'timeoutAtFrame':t}),flush=True)
 code,fs=finish(f);_,es=finish(e);d,v=us(R['direct']),us(R['via']);sent=rounds*(warm+frames)
 added={k:round(v[k]-d[k],3) for k in('meanUs','p50Us','p99Us','p999Us')} if d and v else None
 rule={'noWrongReplyOrTimeout':bad==0 and not timeouts,'forwarderPassedAll':fs['toBackend']['packets']==sent==fs['toAP']['packets'],'forwarderCleanStop':code==0 and fs['stopped']=='SIGNAL',
  'backendSawAll':es['packets']==2*sent and es['framesInOrderPerPeer'],'addedMeanUnder83us':bool(added) and added['meanUs']<83,'addedP99Under208us':bool(added) and added['p99Us']<208}
 print(json.dumps({'kind':'summary','direct':d,'via':v,'addedByForwarder':added,'wrongReplies':bad,'timeouts':timeouts,'forwarder':fs,'echo':es,
  'teamRule':rule,'teamVerdict':'PASS' if all(rule.values()) else 'FAIL','finished':time.strftime('%Y-%m-%dT%H:%M:%S%z')}));return 0
if __name__=='__main__':
 a=sys.argv[1:]
 if a==['--selftest']:raise SystemExit(selftest())
 if a==['--echo']:raise SystemExit(echo())
 if len(a)==4 and a[0]=='--bench':raise SystemExit(bench(int(a[1]),int(a[2]),int(a[3])))
 opt={'--device':None,'--subnet':None};pos=[];i=0
 while i<len(a):
  if a[i] in opt and i+1<len(a):opt[a[i]]=a[i+1];i+=2
  else:pos.append(a[i]);i+=1
 if len(pos)!=3 or any(p.startswith('--') for p in pos):raise SystemExit(__doc__)
 raise SystemExit(forward(pos[0],int(pos[1]),int(pos[2]),opt['--device'],opt['--subnet']))
