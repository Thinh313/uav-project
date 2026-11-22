"""LINUXPORT01 JSON physics forwarder for G2/G3 on Linux (team code, not the owner's; the user's decision "R: forwarder").

The owner's AP (in a container) sends its servo packets (UDP, 1200/s, lockstep) to the host. On the owner's Mac,
Docker Desktop passes them on to 127.0.0.1, where the backend listens (bind allowlist 127.0.0.1:9012) and sees one
127.0.0.1 sender. On Linux a container reaches the host only at the Docker bridge address, so this owned child
listens on 172.17.0.1:9012 (packets from docker0 only, first sender inside 172.17.0.0/16), sends every datagram
unchanged to 127.0.0.1:9012 from one fixed 127.0.0.1 socket and every reply unchanged back to the AP. The backend,
its allowlist and its peer lock stay as the owner wrote them.

hist_stats and forward are the functions of the tested team tool sitl_json_udp_forwarder.py (logs 2026-11-11/01-02),
unchanged except that forward takes the run context and prints it in its ready line (l18_patches.FORWARDER_PATCHES);
the tool's selftest and bench helpers are left out. forward fails closed: any stop but a signal ends forwarding for
good, so the backend's own SERVO_STALE_3S fails the run. Nothing is written to disk; the ready line and the summary
line go to stdout, which the harness captures (4 KiB bound). Exit 0 on SIGTERM/SIGINT, 3 peer rule, 4 backend
refused, 5 other.
"""
import argparse,hashlib,ipaddress,json,os,select,signal,socket,time
from pathlib import Path
now=time.perf_counter_ns
LISTEN_IP='172.17.0.1';LISTEN_PORT=9012;BACKEND_IP='127.0.0.1';BACKEND_PORT=9012;DEVICE='docker0';SUBNET='172.17.0.0/16'
def hist_stats(h,n,total,mx):
 if not n:return None
 def q(p):
  c=0
  for i,v in enumerate(h):
   c+=v
   if c>=p*n:return i
 return {'meanUs':round(total/n/1000,3),'p50Us':q(.5),'p99Us':q(.99),'maxUs':round(mx/1000,3),'histogramTopBucketIsOverflow':2001}
def forward(listen_ip,listen_port,backend_port,device,subnet,context):
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
 print(json.dumps({**context,'kind':'ready','tool':'aeris_runtime.json_forwarder','pid':os.getpid(),'listen':list(front.getsockname()),'port':front.getsockname()[1],
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
def ready_line(raw,config):
 """For launch.py: None until the first stdout line is complete; then it must be this run's ready line, or the launch is refused."""
 if len(raw.split(b'\n',1)[0])>1024:raise ValueError('L18_FORWARDER_READY_BOUND')
 if b'\n'not in raw:return None
 value=json.loads(raw.split(b'\n',1)[0])
 if type(value)is not dict or any(value.get(k)!=config[k]for k in('run','epoch','boot')):raise ValueError('L18_FORWARDER_READY_CONTEXT')
 if value.get('kind')!='ready'or value.get('tool')!='aeris_runtime.json_forwarder'or type(value.get('pid'))is not int or value.get('listen')!=[LISTEN_IP,LISTEN_PORT]or value.get('backend')!=[BACKEND_IP,BACKEND_PORT]or value.get('device')!=DEVICE or value.get('subnet')!=SUBNET:raise ValueError('L18_FORWARDER_READY_ENDPOINTS')
 return value
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
 config=json.loads(Path(args.config).read_bytes())
 if config.get('bind')!=[BACKEND_IP,BACKEND_PORT]:raise ValueError('L18_FORWARDER_BACKEND_BIND')
 raise SystemExit(forward(LISTEN_IP,LISTEN_PORT,BACKEND_PORT,DEVICE,SUBNET,{k:config[k]for k in('run','epoch','boot')}))
if __name__=='__main__':main()
