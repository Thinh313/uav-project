/** Diagnostic-only complete AJZ block/row prefix reader. Never media acceptance. */
import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';import {createHash} from 'node:crypto';
const R=path.resolve(import.meta.dirname,'../../..'),E=path.join(R,'evidence/vidlife12/qa');
const H=b=>createHash('sha256').update(b).digest('hex');
const decoder=path.join(R,'planning/betasim-integrated01/product/semantic-journal.mjs'),original=fs.readFileSync(decoder,'utf8');
let source=original;
const replacements=[["import{inflateRawSync}from'node:zlib'","import{inflateRawSync,constants}from'node:zlib'"],["from'./broker-capture.mjs'","from'"+pathToFileURL(path.join(path.dirname(decoder),'broker-capture.mjs')).href+"'"],["from'./mission.mjs'","from'"+pathToFileURL(path.join(path.dirname(decoder),'mission.mjs')).href+"'"],["need(closed,'AJZ_MISSING_DURABLE_CLOSE');","/* Diagnostic prefix only: durable-close requirement NOT credited. */"],["maxOutputLength:8*2**20,info:true","maxOutputLength:8*2**20,info:true,finishFlush:constants.Z_SYNC_FLUSH"],["lossless:true,authorityRestorable:false","losslessRetainedRows:true,fullRecordingAccepted:false,authorityRestorable:false"]];
for(const[a,b]of replacements){if(source.split(a).length!==2)throw Error('EXACT_TRANSFORMATION_ONCE:'+a);source=source.replace(a,b);}
const prefix=(await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'))).decodeSemanticJournal;
const strict=(await import(pathToFileURL(decoder))).decodeSemanticJournal;
const root=path.join(R,'evidence/hostdiag11/s01/sessions/hostdiag11-short01/product'),files=[];
for(const folder of ['journal','media'])for(const n of fs.readdirSync(path.join(root,folder)))if(n.endsWith('.ajz01'))files.push(path.join(root,folder,n));
const journals=[];
for(const f of files){const bytes=fs.readFileSync(f);let strictError=null;try{strict([bytes]);}catch(e){strictError=e.message;}const q=prefix([bytes]);const kinds={};for(const row of q.rows)kinds[row.kind]=(kinds[row.kind]??0)+1;
 journals.push({path:path.relative(R,f),bytes:bytes.length,sha256:H(bytes),strictFullRecordingError:strictError,diagnosticRetainedPrefixOnly:true,fullRecordingAccepted:false,sourceClock:'NODE_HRTIME_NS_ONLY_NO_PYTHON_ORDER_ASSUMED',rows:q.rows.length,kinds,selected:q.rows.filter(row=>/FAIL|LOST|REVOK|STOP|CLOSE|CODEC|SOURCE_CONFIG|RECEIVER|CLOCK|HTTP|ERROR|ACTIV|HEART|SESSION|PILOT|ROOT_RX|PARAMETER/.test(row.kind)).map(row=>({n:row.n,hostNs:row.hostNs,kind:row.kind,data:row.data,sha256:row.sha256}))});
}
fs.mkdirSync(E,{recursive:true});const out=path.join(E,process.argv[2]??'COLD-PREFIX01.json');const report={format:'aeris-vidlife12-diagnostic-cold-prefix',status:'RETAINED_PREFIX_VERIFIED_NOT_RECORDING_OR_PRODUCT_ACCEPTANCE',originalDecoderSHA256:H(Buffer.from(original)),transformedDecoderSHA256:H(Buffer.from(source)),transformations:replacements.map(x=>x[0]),helperSHA256:H(fs.readFileSync(import.meta.filename)),journals,actorsStarted:false,sourceMutated:false};fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({out:path.relative(R,out),bytes:fs.statSync(out).size,journals:journals.map(x=>({path:x.path,rows:x.rows,kinds:x.kinds}))}));
