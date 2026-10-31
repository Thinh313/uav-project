"""Validate persisted small JSON-string chunks, no synthesized rows or numeric transport."""
from pathlib import Path
import json,hashlib,sys

def join(root):
 m=json.loads((root/'manifest.json').read_text());rows=[];expected=0;seen=set()
 if m['overflow']or m['active']:raise ValueError('UI_NOT_CLOSED_OR_OVERFLOW')
 for p in m['parts']:
  if p['name']in seen or p['start']!=expected:raise ValueError('UI_CHUNK_DUPLICATE_OR_GAP')
  seen.add(p['name']);raw=(root/p['name']).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=p['sha256']:raise ValueError('UI_CHUNK_SHA')
  chunk=json.loads(raw)
  if len(chunk)!=p['rows']or not 0<len(chunk)<=500:raise ValueError('UI_CHUNK_SIZE')
  if not all(isinstance(r,list)and len(r)==4 for r in chunk):raise ValueError('UI_ROW_SHAPE')
  rows.extend(chunk);expected+=len(chunk)
 if expected!=m['count']or m['timing']['frames']!=expected:raise ValueError('UI_INCOMPLETE_TAIL')
 if any(a[0]>=b[0]for a,b in zip(rows,rows[1:])):raise ValueError('UI_TIME_ORDER')
 mean=(len(rows)-1)*1000/(rows[-1][0]-rows[0][0])
 if abs(mean-m['timing']['measuredHz'])>1e-8:raise ValueError('UI_MEAN_MISMATCH')
 return {'status':'PASS_COMPLETE_UI_STRING_CHUNKS','run':m['run'],'rows':len(rows),'chunks':len(m['parts']),'measuredHz':mean,'firstLastMs':[rows[0][0],rows[-1][0]],'precision':'OPAQUE_JSON_STRINGS_NO_TOOL_NUMERIC_RESERIALIZATION','scope':'UI draws, not1200Hz physics frames'},rows
if __name__=='__main__':
 root=Path(sys.argv[1]);result,_=join(root)
 with(root/'verification.json').open('x')as f:json.dump(result,f,indent=2)
 print(json.dumps(result))
