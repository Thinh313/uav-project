import dgram from 'node:dgram';
import {randomBytes} from 'node:crypto';
export class ClockClient{
 constructor(run,epoch,domain,record){
  this.run=run;this.epoch=epoch;this.domain=domain;this.record=record;
  this.requests=new Map();this.matches=0;this.error=null;this.lastMatchAt=null;this.closed=false;
  this.socket=dgram.createSocket('udp4');
  this.socket.on('error',e=>{this.error=e.message;});
  this.socket.on('message',(bytes,peer)=>{
   const received=process.hrtime.bigint();
   try{
    this.record('CLOCK_NODE_RAW',{receiveNodeNs:String(received),peer,rawHex:bytes.toString('hex'),clockDomain:'host-node-hrtime'});
    const r=JSON.parse(bytes.toString()),q=this.requests.get(r.nonce);
    if(peer.address!=='127.0.0.1'||peer.port!==9005||!q||r.run!==this.run||r.epoch!==this.epoch||r.backendClockDomain!==this.domain)throw Error('Foreign clock calibration identity');
    const a=BigInt(r.backendReceiveNs),b=BigInt(r.backendSendNs);
    if(b<a||received<q.sent)throw Error('Calibration clock regression');
    const low=q.sent-a,high=received-b;if(low>high)throw Error('Inconsistent Node/backend bracket');
    const status=q.matched?'DUPLICATE_MATCHED':q.timedout?'LATE_MATCHED':'MATCHED';q.matched=true;clearTimeout(q.timer);
    this.record('CLOCK_NODE_BACKEND_BRACKET',{...r,status,nodeSendNs:String(q.sent),nodeReceiveNs:String(received),nodeMinusBackendLowNs:String(low),nodeMinusBackendHighNs:String(high),nodeClockDomain:'host-node-hrtime',uncertaintyRetained:true});
    if(status==='MATCHED'){this.matches++;this.lastMatchAt=Date.now();}
    q.resolve?.(r);q.resolve=null;
   }catch(e){this.error=e.message;try{this.record('CLOCK_NODE_REJECTED',{error:e.message,rawHex:bytes.toString('hex')});}catch(capture){this.error='Clock evidence failure: '+capture.message;}}
  });
  this.socket.bind(0,'127.0.0.1');
 }
 sample(){
  if(this.closed||this.error)return Promise.reject(Error(this.error??'Clock client closed'));
  if(this.requests.size>=1024)return Promise.reject(Error('Clock calibration request bound'));
  const nonce=randomBytes(16).toString('hex'),sent=process.hrtime.bigint();
  return new Promise((resolve,reject)=>{
   const q={sent,resolve,reject,matched:false,timedout:false};this.requests.set(nonce,q);
   q.timer=setTimeout(()=>{q.timedout=true;try{this.record('CLOCK_NODE_TIMEOUT',{nonce,nodeSendNs:String(sent),clockDomain:'host-node-hrtime'});}catch(e){this.error='Clock evidence failure: '+e.message;}q.reject?.(Error('Clock calibration timeout'));q.resolve=null;q.reject=null;},1000);
   this.socket.send(Buffer.from(JSON.stringify({run:this.run,epoch:this.epoch,nonce})),9005,'127.0.0.1');
  });
 }
 start(){this.timer=setInterval(()=>this.sample().catch(()=>{}),5000);}
 close(){if(this.closed)return;this.closed=true;clearInterval(this.timer);for(const q of this.requests.values())clearTimeout(q.timer);this.socket.close();}
}
