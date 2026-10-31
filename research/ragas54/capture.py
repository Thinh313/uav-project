#!/usr/bin/env python3
"""Capture public release metadata only; never download release executables."""
import datetime, hashlib, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SNAP = ROOT / 'snapshots'
SNAP.mkdir(exist_ok=True)
sources = []

def capture(key, url, suffix='json', origin='rtr-ragas-publisher'):
    target = SNAP / f'{key}.{suffix}'
    if target.exists():
        raise SystemExit(f'Refusing to overwrite capture: {target}')
    req = urllib.request.Request(url, headers={'User-Agent': 'AERIS-RAGAS54-readonly-research', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=35) as response:
        body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise SystemExit('Capture exceeded metadata budget')
        fetched = datetime.datetime.now(datetime.timezone.utc).isoformat()
        target.write_bytes(body)
        sources.append({'id': key, 'url': url, 'final_url': response.url, 'fetched_at': fetched,
                        'http_status': response.status, 'snapshot': target.name, 'bytes': len(body),
                        'sha256': hashlib.sha256(body).hexdigest(), 'origin_id': origin, 'tier': 'A',
                        'tier_basis': 'Official publisher/specification; not a runtime test',
                        'etag': response.headers.get('ETag'), 'last_modified': response.headers.get('Last-Modified')})
    (ROOT / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n')
    return json.loads(body) if suffix == 'json' else body

releases = capture('releases', 'https://api.github.com/repos/Real-Time-Robotics/ragas-release/releases?per_page=100')
for release in releases[:]:
    if release['tag_name'] in {'v4.0.14-b111', 'v4.0.10-b111', 'v4.0.8-b110', 'v4.0.5-b109', 'v4.0.4-b108', 'v4.0.4-b107', 'v4.0.3-b106', 'test-linux-u20'}:
        # Derived notes retain the raw API parent hash and same origin, not independent corroboration.
        name = release['tag_name'] + '.md'
        body = release.get('body', '').encode()
        (SNAP / name).write_bytes(body)
        sources.append({'id': release['tag_name'], 'url': release['html_url'], 'fetched_at': sources[0]['fetched_at'],
                        'snapshot': name, 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(),
                        'origin_id': 'rtr-ragas-publisher', 'tier': 'A', 'derived_from': 'releases.json',
                        'parent_sha256': sources[0]['sha256'], 'tier_basis': 'Maintainer claims, not runtime evidence'})
        (ROOT / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n')
capture('tag-4014', 'https://api.github.com/repos/Real-Time-Robotics/ragas-release/git/ref/tags/v4.0.14-b111')
capture('tag-4010', 'https://api.github.com/repos/Real-Time-Robotics/ragas-release/git/ref/tags/v4.0.10-b111')
main = capture('main-head', 'https://api.github.com/repos/Real-Time-Robotics/ragas-release/commits/main')
capture('readme-main', f"https://raw.githubusercontent.com/Real-Time-Robotics/ragas-release/{main['sha']}/README.md", 'md')
capture('qgc-plan', 'https://docs.qgroundcontrol.com/master/en/qgc-dev-guide/file_formats/plan.html', 'html', 'qgc-project')
capture('mavlink-mission', 'https://mavlink.io/en/services/mission.html', 'html', 'mavlink-project')
capture('mavlink-camera', 'https://mavlink.io/en/services/camera.html', 'html', 'mavlink-project')
print(json.dumps({'captured': len(sources), 'bytes': sum(x['bytes'] for x in sources), 'release_count': len(releases), 'binary_downloads': 0}))
