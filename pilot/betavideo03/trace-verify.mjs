import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {gunzipSync,gzipSync} from 'node:zlib';
const hash=b=>createHash('sha256').update(b).digest('hex');
function reader(rootOrFiles){if(typeof rootOrFiles==='string')return n=>{if(!/^[a-z0-9.-]+$/.test(n))throw Error('TRACE_PATH');const p=path.join(rootOrFiles,n),s=fs.lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>64*2**20)throw Error('TRACE_FILE');return fs.readFileSync(p);};return n=>{const v=rootOrFiles[n];if(v===undefined)throw Error('TRACE_FILE_MISSING');const b=Buffer.isBuffer(v)?v:v instanceof Uint8Array?Buffer.from(v):v.base64?Buffer.from(v.base64,'base64'):null;if(!b||b.length>64*2**20)throw Error('TRACE_FILE');return b;};}
function chainRows(raw,{seq,head},onRow){if(!raw.length||raw.at(-1)!==10)throw Error('TRACE_TORN');for(const line of raw.toString().trimEnd().split('\n')){const q=JSON.parse(line),{sha256,...row}=q;if(Object.keys(row).join(',')!=='seq,hostMonoMs,kind,data,previous'||row.seq!==seq+1||row.previous!==head||!Number.isFinite(row.hostMonoMs)||!/^[A-Z][A-Z0-9_]{0,63}$/.test(row.kind)||sha256!==hash(JSON.stringify(row)))throw Error('TRACE_CHAIN');if(onRow)onRow(q);seq++;head=sha256;}return{seq,head};}
/** Validates all rows from sequence1 to an explicit durable checkpoint. */
export function verifyTrace(rootOrFiles,{receipt='trace-closure.json',onRow=null}={}){
 const read=reader(rootOrFiles),receiptBytes=read(receipt),r=JSON.parse(receiptBytes);if(r.format!=='aeris-betavideo03-full-trace'||r.version!==1||r.complete!==true||r.fatal!==null||!Array.isArray(r.blocks)||r.blocks.length>16384)throw Error('TRACE_RECEIPT_INCOMPLETE');
 let seq=0,head='0'.repeat(64),totalBytes=0,lastMs=-Infinity;
 for(const[index,b]of r.blocks.entries()){if(b.file!=='trace-block-'+String(index+1).padStart(6,'0')+'.jsonl.gz'||b.seqStart!==seq+1||b.previous!==head)throw Error('TRACE_BLOCK_ORDER');const bytes=read(b.file);totalBytes+=bytes.length;if(bytes.length!==b.bytes||hash(bytes)!==b.sha256||b.rawBytes>4*2**20||totalBytes>64*2**20)throw Error('TRACE_BLOCK_SHA_OR_QUOTA');const raw=gunzipSync(bytes,{maxOutputLength:4*2**20});if(raw.length!==b.rawBytes||hash(raw)!==b.rawSha256)throw Error('TRACE_BLOCK_RAW_SHA');const result=chainRows(raw,{seq,head},row=>{if(row.hostMonoMs<lastMs)throw Error('TRACE_HOST_CLOCK_REGRESSION');lastMs=row.hostMonoMs;onRow?.(row);});seq=result.seq;head=result.head;if(seq!==b.seqEnd||head!==b.head)throw Error('TRACE_BLOCK_HEAD');}
 if(seq!==r.events||head!==r.head)throw Error('TRACE_RECEIPT_HEAD');return{status:'PASS',events:seq,head,blocks:r.blocks.length,compressedBytes:totalBytes,receipt,receiptSha256:hash(receiptBytes),final:r.final===true,scope:r.scope};
}
/** Retains every original event in an explicit contiguous sequence range. The
 * original prefix is only a declared anchor, never falsely reverified here. */
export function serializeTraceRange(rootOrFiles,startSeq,endSeq,{receipt='trace-closure.json'}={}){
 if(!Number.isSafeInteger(startSeq)||startSeq<1||!Number.isSafeInteger(endSeq)||endSeq<startSeq)throw Error('TRACE_RANGE');
 const read=reader(rootOrFiles),receiptBytes=read(receipt),r=JSON.parse(receiptBytes);
 if(r.format!=='aeris-betavideo03-full-trace'||r.version!==1||r.complete!==true||r.fatal!==null||!Array.isArray(r.blocks)||r.blocks.length>16384)throw Error('TRACE_RECEIPT_INCOMPLETE');
 // Cheap complete metadata continuity; bytes before the requested range are
 // deliberately NOT re-read here. Full-host closure verification remains separate.
 let metadataSeq=0,metadataHead='0'.repeat(64),declaredBytes=0;
 for(const[index,b]of r.blocks.entries()){
  if(b.file!=='trace-block-'+String(index+1).padStart(6,'0')+'.jsonl.gz'||b.seqStart!==metadataSeq+1||b.previous!==metadataHead||!Number.isSafeInteger(b.seqEnd)||b.seqEnd<b.seqStart||b.seqEnd-b.seqStart>=1024||!/^[a-f0-9]{64}$/.test(b.head??'')||!/^[a-f0-9]{64}$/.test(b.sha256??'')||!/^[a-f0-9]{64}$/.test(b.rawSha256??'')||!Number.isSafeInteger(b.bytes)||b.bytes<1||!Number.isSafeInteger(b.rawBytes)||b.rawBytes<1||b.rawBytes>4*2**20)throw Error('TRACE_BLOCK_ORDER_OR_METADATA');
  metadataSeq=b.seqEnd;metadataHead=b.head;declaredBytes+=b.bytes;if(declaredBytes>64*2**20)throw Error('TRACE_BLOCK_SHA_OR_QUOTA');
 }
 if(metadataSeq!==r.events||metadataHead!==r.head)throw Error('TRACE_RECEIPT_HEAD');if(endSeq>r.events)throw Error('TRACE_RANGE_COVERAGE');
 const selected=r.blocks.filter(b=>b.seqEnd>=startSeq&&b.seqStart<=endSeq);if(!selected.length)throw Error('TRACE_RANGE_COVERAGE');
 const rows=[];let originalPrevious,selectedBytes=0,lastHostMs=-Infinity;
 for(const b of selected){const bytes=read(b.file);selectedBytes+=bytes.length;if(bytes.length!==b.bytes||hash(bytes)!==b.sha256)throw Error('TRACE_BLOCK_SHA_OR_QUOTA');const raw=gunzipSync(bytes,{maxOutputLength:4*2**20});if(raw.length!==b.rawBytes||hash(raw)!==b.rawSha256)throw Error('TRACE_BLOCK_RAW_SHA');let firstHostMs,lastRow;
  const result=chainRows(raw,{seq:b.seqStart-1,head:b.previous},row=>{if(row.hostMonoMs<lastHostMs)throw Error('TRACE_HOST_CLOCK_REGRESSION');firstHostMs??=row.hostMonoMs;lastHostMs=row.hostMonoMs;lastRow=row;if(row.seq>=startSeq&&row.seq<=endSeq){if(row.seq===startSeq)originalPrevious=row.previous;rows.push(row);}});
  if(result.seq!==b.seqEnd||result.head!==b.head||firstHostMs!==b.firstHostMs||lastRow.hostMonoMs!==b.lastHostMs)throw Error('TRACE_BLOCK_HEAD');
 }
 if(rows.length!==endSeq-startSeq+1)throw Error('TRACE_RANGE_COVERAGE');
 const source={status:'SELECTED_BLOCKS_VERIFIED_NOT_FULL_HOST',events:r.events,head:r.head,blocks:r.blocks.length,selectedBlocks:selected.length,compressedBytes:selectedBytes,receipt,receiptSha256:hash(receiptBytes),final:r.final===true,scope:'SOURCE_RECEIPT_METADATA_PLUS_SELECTED_BLOCK_VERIFICATION',originalPrefixVerified:false};
 const value={format:'aeris-betavideo03-trace-range',version:1,rangeScope:'CONTIGUOUS_SOURCE_SEQUENCE_SEGMENT_NOT_COMPLETE_HOST',sourceReceipt:source,anchor:{firstSeq:startSeq,previous:originalPrevious},lastSeq:endSeq,head:rows.at(-1).sha256,events:rows.length,rows};const bytes=gzipSync(Buffer.from(JSON.stringify(value)+'\n'),{level:1});return{bytes,sha256:hash(bytes),events:rows.length,firstSeq:startSeq,lastSeq:endSeq,head:value.head,sourceReceiptSha256:source.receiptSha256};
}
export function verifyTraceRange(bytes,{onRow=null}={}){if(bytes.length>32*2**20)throw Error('TRACE_RANGE_BYTES');const q=JSON.parse(gunzipSync(bytes,{maxOutputLength:128*2**20}));if(q.format!=='aeris-betavideo03-trace-range'||q.version!==1||q.rangeScope!=='CONTIGUOUS_SOURCE_SEQUENCE_SEGMENT_NOT_COMPLETE_HOST'||!Array.isArray(q.rows)||!q.rows.length||q.rows.length>500000||q.events!==q.rows.length)throw Error('TRACE_RANGE_SCHEMA');const raw=Buffer.from(q.rows.map(r=>JSON.stringify(r)).join('\n')+'\n');const end=chainRows(raw,{seq:q.anchor.firstSeq-1,head:q.anchor.previous},onRow);if(end.seq!==q.lastSeq||end.head!==q.head||q.events!==q.lastSeq-q.anchor.firstSeq+1)throw Error('TRACE_RANGE_HEAD');return{status:'PASS',events:q.events,firstSeq:q.anchor.firstSeq,lastSeq:q.lastSeq,head:q.head,sourceReceiptSha256:q.sourceReceipt.receiptSha256,scope:q.rangeScope,originalPrefixVerified:false};}
