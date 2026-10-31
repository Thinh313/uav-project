#!/usr/bin/env python3
"""Read-only HERA02 provenance/derivative checks; not source semantics or HIL."""
import hashlib, json
from pathlib import Path
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/herahub-software-20261012'
records=json.loads((D/'sources.json').read_text());by_id={r['id']:r for r in records}
assert len(by_id)==len(records),'duplicate source id'
for r in records:
 if r['status']=='captured':
  assert hashlib.sha256((D/'snapshots'/r['snapshot']).read_bytes()).hexdigest()==r['sha256'],r['id']
 if 'derived_from' in r:
  raw=by_id[r['derived_from']['source']]
  assert raw['sha256']==r['derived_from']['sha256']
  assert raw['origin_id']==r['origin_id'] and raw['url']==r['url']
manifest=json.loads((D/'snapshots/ragas-release-manifest.json').read_text())
assert (D/'snapshots/ragas-release-notes.decoded.txt').read_text()==manifest['releaseNotes']+'\n'
reader=PdfReader(D/'snapshots/qualcomm-selector.pdf')
text='\n'.join(f'PAGE {i+1}\n{page.extract_text() or ""}' for i,page in enumerate(reader.pages))
assert (D/'snapshots/qualcomm-selector.pdf.txt').read_text()==text,'PDF derivative differs'
assert manifest['abi']=='arm64-v8a' and manifest['platform']=='android'
latest=max(json.loads((D/'snapshots/ragas-releases.json').read_text()),key=lambda r:r['published_at'])
assert latest['tag_name']=='v4.0.14-b111' and manifest['versionName']=='4.0.14' and manifest['buildNumber']==111
assert any(a['name']=='ragas-4.0.14+111-arm64-v8a.apk' for a in latest['assets'])
assert not list((D/'snapshots').glob('*.apk')) and not list((D/'snapshots').glob('*.deb'))
profile=json.loads((ROOT/'hardware/herahub2/profile.json').read_text())
assert profile['naming']['current']=='HeraHub'
assert profile['fields']['display_brightness_nits']['development_blocker'] is False
prior=ROOT/'evidence/hera01/source-manifest.json'
if not prior.exists():
 raise AssertionError('HERA01 source manifest missing; app preservation not checked')
old=json.loads(prior.read_text())['files'];app=[(k,v) for k,v in old.items() if k.startswith('app/')]
assert app,'No prior app fingerprints'
for rel,digest in app:
 assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,'App changed: '+rel
report={'capture_records':len(records),'captured':sum(r['status']=='captured' for r in records),'unavailable':sum(r['status']!='captured' for r in records),'origins':sorted({r['origin_id'] for r in records if r['status']=='captured'}),'derived_sources_checked':2,'pdf_pages':len(reader.pages),'publisher_apk_digest_only':True,'apk_not_downloaded':True,'app_files_unchanged':len(app),'brightness_nonblocking':True,'scope':'Provenance/derivation and existing app fingerprints; no device test, measured latency or semantic certification'}
print(json.dumps(report,ensure_ascii=False))
