#!/usr/bin/env python3
"""Supplement existing capture with small manifests/checksum files; no executables."""
import datetime, hashlib, json, urllib.request
from pathlib import Path
root = Path(__file__).resolve().parent
sources = json.loads((root/'sources.json').read_text())
releases = json.loads((root/'snapshots/releases.json').read_text())
for tag in ['v4.0.14-b111', 'v4.0.10-b111']:
    release = next(x for x in releases if x['tag_name'] == tag)
    for asset in release['assets']:
        name = asset['name']
        if not name.endswith(('.json', '.sha256')):
            continue
        key = tag + '--' + name
        dest = root/'snapshots'/key
        if dest.exists():
            raise SystemExit('Capture exists: ' + key)
        req = urllib.request.Request(asset['browser_download_url'], headers={'User-Agent':'AERIS-RAGAS54-readonly-research'})
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read(100_001)
            if len(data)>100_000: raise SystemExit('Small-metadata budget exceeded')
            digest = hashlib.sha256(data).hexdigest()
            if asset.get('digest') != 'sha256:'+digest: raise SystemExit('Asset metadata digest mismatch: '+key)
            dest.write_bytes(data)
            sources.append({'id':key,'url':asset['browser_download_url'],'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            'http_status':response.status,'snapshot':key,'sha256':digest,'bytes':len(data),
                            'origin_id':'rtr-ragas-publisher','tier':'A','tier_basis':'Publisher asset manifest/checksum, not downloaded binary verification'})
            (root/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'sources':len(sources),'binary_downloads':0}))
