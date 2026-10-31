import fs from'node:fs';import path from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';import{createHash}from'node:crypto';
const R=fileURLToPath(new URL('../../',import.meta.url)),name='pilot/beta06g5/media/server.mjs',P=path.join(R,name),hash=s=>createHash('sha256').update(s).digest('hex');
export async function createBetaMedia(options){
 const pins=JSON.parse(fs.readFileSync(path.join(R,'evidence/beta06/generation17/flight-pins01.json')));const original=fs.readFileSync(P,'utf8');if(pins.files[name]!==hash(original))throw Error('FROZEN_MEDIA_SOURCE_DRIFT');
 let s="import{encodeBatch}from "+JSON.stringify(new URL('./batch.mjs',import.meta.url).href)+";\n"+original;const a="'evidence/beta06/generation05/'",b="'evidence/missionbeta01/'";if(s.split(a).length!==2)throw Error('MEDIA_SCOPE_EXACT_COUNT');s=s.replace(a,b);
 if(s.split('fileURLToPath(import.meta.url)').length!==3)throw Error('MEDIA_META_COUNT');s=s.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(P));
 s=s.replace(/from\s*(['"])(\.[^'"]+)\1/g,(_,q,p)=>'from '+JSON.stringify(new URL(p,pathToFileURL(P)).href));
 s=s.replace("'/viewer.mjs','/client.mjs'","'/viewer.mjs','/batch.mjs','/client.mjs'");
 s=s.replace("if (url.pathname === '/api/next') {","if (url.pathname === '/api/next' || url.pathname === '/api/next-batch') {");
 const single="const frameRef = hash(serverBoot + ':' + packet.meta.configId + ':' + packet.meta.frameId), frame = frames.get(frameRef); if (!frame) throw Error('FRAME_RETENTION');\n        return send(200,encodePacket({...packet.meta,frameRef,sourceHostBounds:frame.sourceHostBounds},packet.data),'application/octet-stream');";
 if(s.split(single).length!==2)throw Error('EXACT_BATCH_ROUTE_PROJECTION');
 s=s.replace(single,"const pack=p=>{const frameRef=hash(serverBoot+':'+p.meta.configId+':'+p.meta.frameId),frame=frames.get(frameRef);if(!frame)throw Error('FRAME_RETENTION');return encodePacket({...p.meta,frameRef,sourceHostBounds:frame.sourceHostBounds},p.data);};if(url.pathname==='/api/next-batch'){const packets=[pack(packet)];while(packets.length<4){const p=relay.take(viewerId);if(!p)break;packets.push(pack(p));}return send(200,encodeBatch(packets),'application/octet-stream');}return send(200,pack(packet),'application/octet-stream');");
 s=s.replace('reports: 8','reports: 48');
 s=s.replace('20n * 1024n ** 3n + 128n * 1024n ** 2n','10n * 1024n ** 3n + 256n * 1024n ** 2n').replace('lifetimeMs: 1800000','lifetimeMs: 2700000');
 s=s.replace("return send(200, await fs.readFile(file), filename.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/javascript');","return send(200, ['viewer.mjs','batch.mjs'].includes(filename) ? await fs.readFile(path.join(REPO,'pilot/missionbeta01',filename)) : await fs.readFile(file), filename.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/javascript');");
 const mod=await import('data:text/javascript;base64,'+Buffer.from(s).toString('base64'));const media=await mod.createMediaServer(options);
 return{...media,projection:{path:name,originalSha256:hash(original),effectiveSha256:hash(s),namespaceOnly:false,policyProjection:"USER_20_10_AND_MATCHED_45MIN_TEST_LIFETIME"}};
}
