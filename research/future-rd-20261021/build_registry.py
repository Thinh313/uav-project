#!/usr/bin/env python3
"""Bounded, human-reviewed source claims. Never generates compatibility claims."""
import json, hashlib, sys, html, unicodedata
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, '/Users/os/.codex/skills/refinery')
import refinery

sources = {r['id']: r for r in json.loads((ROOT/'sources.json').read_text())['sources']}
for r in json.loads((ROOT/'fallback-sources.json').read_text())['sources']:
    sources[r['id']] = {**r, 'capturedAt': r['at'], 'status': 'CAPTURED_READER'}
power = ROOT/'snapshots/nvidia-power-reader.html'
sources['nvidia-power-reader'] = dict(id='nvidia-power-reader', origin='nvidia',
    url='https://docs.nvidia.com/jetson/archives/r39.2/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html',
    capturedAt='2026-10-21', snapshot=power.name, bytes=power.stat().st_size,
    sha256=hashlib.sha256(power.read_bytes()).hexdigest(),
    representation='EXACT_WEB_TOOL_READER_TEXT_NOT_ORIGIN_HTML')

# entity, field, normalized value (interpretation), short literal evidence, capture ID.
# All entries are official documentation claims, never local qualification.
facts = [
 ('sony-ilx-lr1-sdk','feature','ILX-LR1 is listed by Sony Camera Remote SDK','ILX-LR1','sony-sdk'),
 ('sony-ilx-lr1-sdk','software','Sony lists a 64-bit ARM Linux host; Android support is not established here','ARMv8','sony-sdk'),
 ('sony-remote-ptp','interface','Sony publishes a PTP command option, subject to per-model functions','PTP','sony-ptp'),
 ('gremsy-pixylr-standard','feature','Standard Pixy LR is designed for Sony ILX-LR1','Sony ILX-LR1','gremsy-pixylr'),
 ('gremsy-pixylr-standard','interface','Standard gimbal exposes USB 3.0 and UART SDK options; qualification still required','USB 3.0','gremsy-pixylr'),
 ('gremsy-pixylr-standard','mass','Published standard-gimbal mass: 495 g; not a complete payload mass','495g','gremsy-pixylr'),
 ('gremsy-pixylr-sportv2','mass','S-Port V2 column lists 462 g; do not substitute standard interface/mount','462g','gremsy-pixylr'),
 ('gremsy-pixylr-twoaxis','mass','Two-axis column lists 333 g; not the same axis/mount configuration','333g','gremsy-pixylr'),
 ('gremsy-pixylr-integration','feature','Official integration guide covers Airpixel ENTIRE with Cube/Pixhawk','AIRPIXEL','gremsy-integration'),
 ('gremsy-vio-f1','feature','Integrated EO/IR payload advertises MAVLink support','MAVLink Drone Support','gremsy-vio'),
 ('gremsy-vio-f1','interface','Published preview outputs include HDMI and Ethernet RTSP','HDMI/Ethernet RTSP','gremsy-vio'),
 ('gremsy-vio-f1','imaging','F1 lists radiometric Boson 640 and 14 mm EFL; not a 1280-native sensor','14 mm (EFL)','gremsy-vio'),
 ('gremsy-vio-g1','imaging','G1 uses a distinct radiometric 640 core / 19 mm EFL configuration','19mm (EFL)','gremsy-vio'),
 ('phaseone-p3-mavlink','interface','P3 MAVLink variants list MAVLink/Auterion protocol support; exact mount/API must be selected','MAVLink/Auterion','phaseone-p3'),
 ('phaseone-ixm-gs120','imaging','GS120 is marketed as a 120 MP global-shutter component; not every Phase One camera','Global Shutter','phaseone-gs120'),
 ('phaseone-ixm-gs120','feature','Maximum shutter speed specification is 1/16000 s; not a whole-system exposure guarantee','1/16000','phaseone-gs120'),
 ('phaseone-sdk3','software','Camera SDK documentation lists Linux ARM64 and x86_64','Linux (ARM64 & x86_64)','phaseone-sdk'),
 ('flir-hadron640rplus','imaging','640R+ radiometric variant measures temperature; select exact SKU','70640AS32-6PARXP','flir-hadron-reader'),
 ('flir-hadron640plus','imaging','640+ non-radiometric variant does not provide temperature measurement','70640AS32-6PAAXP','flir-hadron-reader'),
 ('nvidia-orin-nx16','feature','Orin NX has a 16 GB variant; compute suitability unmeasured','Jetson Orin NX 16GB','nvidia-orin'),
 ('nvidia-orin-nx16','power','Published normal 16 GB modes include 25 W; Super 40 W has flash/carrier conditions','25W','nvidia-power-reader'),
 ('nvidia-thor-family','feature','Thor is an available higher-power compute family, not an automatic airframe choice','Jetson T5000','nvidia-thor'),
 ('ark-v6x','feature','ARK documents an FMUv6X/PAB flight-controller module','FMUV6X','ark-v6x'),
 ('ark-v6x','software','ARK states that its shipped PX4 controller can be flashed with ArduPilot','can be flashed with ArduPilot','ark-v6x'),
 ('holybro-pixhawk6x','feature','Holybro identifies its 6X main MCU as STM32H753','STM32H753','holybro-v6x'),
 ('holybro-pixhawk6x','interface','The documented Ethernet port is 100 Mbps; not a gigabit mission-network switch','100Mbps','holybro-v6x'),
 ('doodlelabs-nano2','feature','Nano2 is a manufacturer radio candidate; range and throughput on Hera are unqualified','Nano²','doodle-products-reader'),
 ('dji-h30t-benchmark','imaging','DJI explicitly identifies 1280x1024 as native thermal sensor resolution','native sensor size','dji-h30'),
 ('mavlink-camera','interface','Camera service publishes capability/discovery messages; device implementation must be verified','CAMERA_INFORMATION','mavlink-camera'),
 ('mavlink-gimbal','interface','Gimbal v2 includes manager status and ownership semantics','GIMBAL_MANAGER_STATUS','mavlink-gimbal'),
 ('mavlink-timesync','interface','Time synchronization estimates component clock offset; not exposure-time certainty','TIMESYNC','mavlink-timesync'),
 ('gstreamer-webrtc','interface','GStreamer provides a WebRTC component; performance depends on actual pipeline','webrtcbin','gstreamer-webrtc'),
]

fields=['feature','interface','imaging','software','power','mass','installed_hera','price']
cfg=dict(domain='aeris_future_rd_20261021',entity_label='Selected reference components, not market coverage',
    schema=dict(type_field=None,fields=fields),rollup_field=None,
    universe=dict(estimate=None,basis='Purposeful shortlist only; no market denominator or coverage percentage'),
    refresh_days=dict(default=90),alias_map={},
    ambiguous_clusters=[['gremsy-pixylr-standard','gremsy-pixylr-sportv2','gremsy-pixylr-twoaxis'],
        ['gremsy-vio-f1','gremsy-vio-g1'],['flir-hadron640rplus','flir-hadron640plus']],
    domain_gates=dict(no_inferred_fields=fields))
claims=[]
for n,(entity,field,value,span,sid) in enumerate(facts,1):
    s=sources[sid]
    raw=(ROOT/'snapshots'/s['snapshot']).read_text()
    norm=lambda x: unicodedata.normalize('NFC',html.unescape(x))
    if norm(span) not in norm(raw):
        raise ValueError(f'Unmatched evidence {n}: {sid}: {span}')
    claims.append(dict(id=f'F{n:02}',entity=entity,field=field,value=value,evidence_span=span,
        extraction='normalized',tier='A',meaning='OFFICIAL_DOCUMENTATION_CLAIM_NOT_LOCAL_TEST',
        capture=dict(url=s['url'],fetched_at=s['capturedAt'],snapshot=s['snapshot'],source=s['origin'])))

(ROOT/'domain.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False))
(ROOT/'claims.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in claims))
cfg,claims,registry,agg,b = refinery.run_pipeline(ROOT)
(ROOT/'registry.json').write_bytes(b)
(ROOT/'registry-sources.json').write_text(json.dumps(list(sources.values()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(claims=len(claims),entities=len(registry),sha256=hashlib.sha256(b).hexdigest())))
