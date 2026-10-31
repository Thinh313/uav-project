from pathlib import Path
import re,os,json,hashlib
R=Path(__file__).resolve().parents[2];A=R/'native/native95/assets';V=A/'direct95/vendor';roots=['services/sitl.mjs','pilot/auto63/link-v5.mjs','pilot/auto63/flight-guard.mjs','native/native94/link83.mjs','native/native94/takeoff83.mjs','native/native94/display-link84.mjs','native/native94/telemetry84.mjs'];seen={}
def visit(name):
 name=os.path.normpath(name)
 if name in seen:return
 s=(R/name).read_text();seen[name]=s
 for imp in re.findall(r'(?:from\s*|import\s*)[\'\"]([^\'\"]+)[\'\"]',s):
  if imp.startswith('.'):visit(str(Path(name).parent/imp))
for name in roots:visit(name)
for name,s in seen.items():
 p=V/name;p.parent.mkdir(parents=True,exist_ok=True)
 # Original compiler is replaced with the already verified portable offline94 compiler.
 if name=='pilot/auto63/compiler.mjs':
  rel=os.path.relpath(A/'offline94/auto.mjs',p.parent);s='export * from '+repr(rel)+';\n'
 elif name=='pilot/aeris57/domain.mjs':
  rel=os.path.relpath(A/'offline94/domain.mjs',p.parent);s='export * from '+repr(rel)+';\n'
 elif name=='services/mavlink.mjs':
  rel=os.path.relpath(V/'pilot/apstream40/wire.mjs',p.parent)
  s="""import{DEFINITIONS}from'./mavlink-definitions.mjs';import{FullFramer,encodeFull}from'REL';export{DEFINITIONS};
export const encode=(id,fields={},m={})=>encodeFull(id,fields,{system:255,component:190,...m,seq:(m.seq??0)&255});
export class Decoder{constructor(){this.framer=new FullFramer();this.started=false;this.prefix=[];this.stats={accepted:0,unknown:0,corrupt:0,unsupported:0};}push(chunk){let b=chunk;if(!this.started){let k=b.findIndex(x=>x===253||x===254),p=k<0?b:b.slice(0,k);this.prefix.push(...p);if(this.prefix.length>1024||p.some(x=>![9,10,13].includes(x)&&(x<32||x>126)))throw Error('PREFIX_BOUND');if(k<0)return[];if(this.prefix.length&&!new TextDecoder().decode(Uint8Array.from(this.prefix)).includes('Init ArduCopter V4.7.1 (dbe79216)'))throw Error('WRONG_BANNER');this.started=true;b=b.slice(k);}if(!b.length)return[];return this.framer.push(b,Math.floor(globalThis.nativeNow95?.()??performance.now())).filter(f=>{if(f.signed)throw Error('SIGNED_UNVERIFIED');if(!f.known){this.stats.unknown++;return false;}this.stats.accepted++;return true;}).map(f=>({...f,fields:Object.fromEntries(Object.entries(f.fields).map(([k,v])=>[k,typeof v==='string'&&['uint64_t','int64_t'].some(t=>DEFINITIONS[f.id].fields.some(x=>x.name===k&&x.type===t))?Number(v):v]))}));}}
""".replace('REL',rel)
 else:
  if "from 'node:net'"in s:s=s.replace("from 'node:net'","from '"+os.path.relpath(A/'direct95/socket.mjs',p.parent)+"'")
  if "from 'node:events'"in s:s=s.replace("from 'node:events'","from '"+os.path.relpath(A/'direct95/events.mjs',p.parent)+"'")
  s=re.sub(r"import\s*fs\s*from\s*'node:fs';?",'',s)
  s=re.sub(r"import\s*\{randomUUID\}\s*from\s*'node:crypto';?","const randomUUID=()=>crypto.randomUUID();",s)
  if "import{createHash}from'node:crypto';"in s or "import {createHash} from 'node:crypto';"in s:
   rel=os.path.relpath(A/'workflow/preflight/sha256.mjs',p.parent);s=s.replace("import{createHash}from'node:crypto';",f"import{{sha256Text}}from'{rel}';").replace("import {createHash} from 'node:crypto';",f"import{{sha256Text}}from'{rel}';")
   s=s.replace("createHash('sha256').update(stable(x)).digest('hex')","sha256Text(stable(x))").replace("createHash('sha256').update(typeof x==='string'?x:stable(x)).digest('hex')","sha256Text(typeof x==='string'?x:stable(x))")
  s=s.replace("Buffer.from(s,'hex')","Uint8Array.from((s.match(/../g)??[]).map(x=>parseInt(x,16)))")
  s=s.replace("Buffer.from(intent.rawHex,'hex')","unhex(intent.rawHex)")
  if name=='pilot/auto63/link-v5.mjs':
   rel=os.path.relpath(V/'pilot/apstream40/wire.mjs',p.parent);s=f"import{{hex,unhex}}from'{rel}';"+s
   s=s.replace("b.toString('hex')","hex(b)").replace('now(){return Math.floor(performance.now())}','now(){return Math.floor(this.clock())}').replace('const at=this.now();this.record(\'RX_RAW\'',"const at=this.socket.receivedAt95??this.now();this.record('RX_RAW'")
  if name=='services/sitl.mjs':
   rel=os.path.relpath(V/'pilot/apstream40/wire.mjs',p.parent);s=f"import{{hex}}from'{rel}';"+s
   s=s.replace("b.toString('hex')","hex(b)").replace('this.heartbeatTimer.unref();','').replace('this.receive(m);','this.receive({...m,receivedAt95:s.receivedAt95});',1).replace('const at=this.clock();this.frames.push','const at=m.receivedAt95??this.clock();this.frames.push')
  if name=='native/native94/telemetry84.mjs':s=s.replace('HOST_MONOTONIC','ANDROID_MONOTONIC')
 p.write_text(s)
(A/'direct95/lineage.json').write_text(json.dumps({'sources':{n:hashlib.sha256(s.encode()).hexdigest()for n,s in seen.items()},'adaptations':'platform import adapters; Buffer→Uint8Array; native monotonic timestamp; full-framer decoder; portable offline compiler; no host control IO'},indent=2))
print('PORT_MODULES',len(seen))
