#!/usr/bin/env python3
"""Freeze explicitly listed public URLs; record errors rather than invent captures."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib, json, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
ROOT=Path(__file__).resolve().parents[1]
domain=Path(sys.argv[1]).resolve()
requests=json.loads((domain/'capture-requests.json').read_text())
existing={r['id']:r for r in json.loads((domain/'sources.json').read_text())} if (domain/'sources.json').exists() else {}
snapshots=domain/'snapshots';snapshots.mkdir(parents=True,exist_ok=True)
def capture(item):
    if item['id'] in existing and existing[item['id']]['status']=='captured':
        return existing[item['id']]
    rec={**item,'fetched_at':datetime.now(timezone.utc).isoformat()}
    assert item['url'].startswith('https://'),'Only explicit public HTTPS source capture'
    assert Path(item['snapshot']).name==item['snapshot'],'Snapshot must be a basename'
    try:
        req=Request(item['url'],headers={'User-Agent':'Mozilla/5.0 public-technical-research'})
        with urlopen(req,timeout=30) as res:
            data=res.read(12*1024*1024+1)
            if len(data)>12*1024*1024:raise ValueError('Capture exceeds 12 MiB limit')
            rec.update(http_status=res.status,final_url=res.url,content_type=res.headers.get('Content-Type'))
        (snapshots/item['snapshot']).write_bytes(data)
        rec.update(status='captured',sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),capture_format='Raw HTTP response bytes')
    except (URLError,ValueError,TimeoutError) as exc:
        rec.update(status='unavailable',error=str(exc))
    return rec
with ThreadPoolExecutor(max_workers=4) as pool:
    records=list(pool.map(capture,requests))
(domain/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'id':r['id'],'status':r['status'],**({k:r[k] for k in ['bytes','error'] if k in r})} for r in records],ensure_ascii=False))
