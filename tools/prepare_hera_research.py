#!/usr/bin/env python3
"""Serialize manually reviewed HERA02 claims; not a web/LLM extractor."""
import hashlib, html, json, unicodedata
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/herahub-software-20261012'
records=json.loads((D/'sources.json').read_text())
by_id={r['id']:r for r in records}
for raw_id,new_id,filename,method in [
 ('qualcomm-selector','qualcomm-selector-text','qualcomm-selector.pdf.txt','pypdf page text; QCS8550 table checked visually on PDF page 2'),
 ('ragas-release-manifest','ragas-release-notes','ragas-release-notes.decoded.txt','JSON releaseNotes string decoding')]:
 raw=by_id[raw_id];path=D/'snapshots'/filename
 derivative={**raw,'id':new_id,'snapshot':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'content_type':'text/plain; charset=utf-8','capture_format':method,'derived_from':{'source':raw_id,'snapshot':raw['snapshot'],'sha256':raw['sha256']}}
 by_id[new_id]=derivative
records=list(by_id.values());(D/'sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
claims=[]
def add(entity,field,value,source,span,scope=None):
 r=by_id[source];s=(D/'snapshots'/r['snapshot']).read_text()
 norm=lambda x:unicodedata.normalize('NFC',html.unescape(x))
 assert norm(span) in norm(s),(source,span)
 cap={k:r[k] for k in ['url','fetched_at','snapshot','origin_id','sha256']};cap['source']=source
 if 'derived_from' in r:cap['derived_from']=r['derived_from']
 claims.append(dict(entity=entity,field=field,value=value,evidence_span=span,extraction='normalized',tier=r['tier'],capture=cap,scope=scope or r['scope']))
old='RtR HeraHub (Intel public platform)';new='RtR HeraHub v2 (Android public platform)';manual='RAGAS (manual scoped to 4.0.0 build 4)';release='RAGAS (release 4.0.14 build 111)'
add(old,'soc','Intel Core i7-1255U','rtr-herahub','i7-1255U')
add(old,'video-count',8,'rtr-herahub','8 simultaneous')
add(old,'power','Dual hot-swappable batteries','rtr-herahub','hot-swappable')
add(new,'soc','Qualcomm QCS8550','rtr-herahub-v2','QCS8550')
add(new,'os','Android 13','rtr-herahub-v2','Android 13')
add(new,'gpu','Adreno 740','rtr-herahub-v2','Adreno 740')
add(new,'joystick-count',4,'rtr-herahub-v2','4 joysticks')
add(new,'video-count',6,'rtr-herahub-v2','6 simultaneous')
add(new,'storage-claim','256GB onboard; optional 1TB SSD','rtr-herahub-v2','256GB')
add('RAGAS (public API marketing)','api-family','REST and WebSocket advertised; endpoints/schema not supplied here','rtr-ragas','REST + WebSocket')
add('RtR HeraLink (historical naming)','historical-name','HeraLink appears in older HeraSight setup instructions','manual-legacy-payload-setup','Preparing the HeraLink')
add('RAGAS (historical controller example)','connection-example','TCP 192.168.0.210:20002 in legacy instructions; not a v2 default','manual-legacy-app-settings','192.168.0.210:20002')
add('RAGAS (historical payload controls)','legacy-control-example','First wheel EO zoom; second wheel IR zoom; not current channel IDs','manual-payloads-herasight-2-remote-controller-operation','1st Scroll Wheel')
add(manual,'manual-version','4.0.0 build 4','manual-ragas','RAGAS 4.0.0 (build 4)')
add(manual,'flight-authority','Autopilot owns avoidance, failsafe actions and fence enforcement','manual-ragas',"the behaviour is the autopilot's")
add(manual,'platform','Android field controller; Linux/macOS planning and review','manual-getting-started-supported-platforms','Android')
add(manual,'package-update','Application updates arrive as APK','manual-getting-started-installation','updates arrive as an APK')
add(manual,'permission-checks','Overlay permission and battery-optimisation exemption checked at start','manual-getting-started-installation','Battery-optimisation exemption')
add(manual,'rc-functions','Twelve assignable functions, not a count of physical buttons','manual-user-guide-settings-rc-settings','Twelve functions')
add(manual,'calibration','Guided sticks, triggers, wheels and switches; stick mode selection','manual-user-guide-settings-rc-settings','Guided calibration')
add(manual,'channel-feedback','Live channels and reversed throttle handling documented','manual-user-guide-settings-rc-settings','Channels are shown live')
add(manual,'signing','MAVLink 2 signing with key management','manual-user-guide-settings-transmission-settings','MAVLink 2 signing')
add(manual,'forwarding','Companion tool forwarding at host/port','manual-user-guide-settings-transmission-settings','Forwarding')
add(manual,'link-statistics','Sent, received, lost and current data rate','manual-user-guide-settings-transmission-settings','Messages sent, received and lost')
add(manual,'rtk-client','NTRIP profiles and automatic reconnection','manual-user-guide-settings-rtk-settings','NTRIP profiles')
add(manual,'vio','Manual/automatic VIO mode and origin coordinates','manual-user-guide-settings-rtk-settings','origin coordinates')
add(manual,'storage','Map and terrain caches, telemetry logs and media categories','manual-user-guide-settings-storage','Terrain cache')
add(manual,'payload-ota','Payload firmware update with rollback/cancel; not Android/BSP OTA','manual-user-guide-settings-ota-update','Installing payload firmware')
add(manual,'payload-ota-guards','Disarmed aircraft and controller battery at least 50%','manual-user-guide-settings-ota-update','50%')
add(manual,'aircraft-battery','Top bar battery indicator refers to the aircraft','manual-user-guide-flight-top-bar-status','aircraft battery')
add(manual,'per-link-status','Per-link signal and noise detail documented','manual-user-guide-flight-top-bar-status','per-link breakdown')
add(manual,'save-upload','Local save and aircraft upload are separate operations','manual-user-guide-mission','Saving is local to the controller')
add(manual,'mission-ownership','Uploading replaces the onboard mission','manual-user-guide-mission','Uploading replaces')
add(manual,'mission-patterns','Survey, corridor, structure and orbit patterns','manual-user-guide-mission-waypoints-and-patterns','Corridor')
add(manual,'offline-map','Download selected square/circle region; capacity/progress and recovery controls','manual-user-guide-map-offline-map','square')
add(manual,'terrain','Elevation data cached for later offline use','manual-user-guide-mission-mission-terrain','cached')
add(manual,'capability-ui','Controls depend on actual payload capabilities','manual-reference-capability-matrix','EIS')
add(release,'abi','Android arm64-v8a','ragas-release-manifest','"abi": "arm64-v8a"')
add(release,'version','4.0.14 build 111','ragas-release-manifest','"buildNumber": 111')
add(release,'survey-grid','Publisher reports QGC .plan grid alignment fixes','ragas-release-notes','same spacing phase')
add(release,'survey-figures','Publisher reports area/time/whole-mission photo count corrections','ragas-release-notes','100×')
add(release,'camera-upload','Publisher reports camera commands now forwarded to ArduPilot','ragas-release-notes','empty placeholders')
add(release,'terrain-export','Publisher reports blocking export when required terrain is missing','ragas-release-notes','wrong altitude')
add(release,'resume','Publisher reports resume at last reached waypoint','ragas-release-notes','last reached')
add(release,'capture-observation','Publisher reports actual/planned photo display','ragas-release-notes','37/120')
add('QCS8550 (silicon vendor scope)','cpu-topology','Octa-core','qualcomm-selector-text','Octa-Core')
add('QCS8550 (silicon vendor scope)','gpu','Adreno 740','qualcomm-selector-text','Adreno™ 740')
add('Android standard input (conditional)','input-events','Binary KeyEvent and analog MotionEvent for compatible controllers','android-input','KeyEvent')
add('Android codec capabilities','decoder-limit','getMaxSupportedInstances is an upper-bound hint, not a concurrency guarantee','android-codec-capabilities','upper bound')
add('Android codec capabilities','low-latency','Low latency decoding is a queryable decoder feature','android-codec-capabilities','FEATURE_LowLatency')
add('Android Media3 RTSP','video-codec','H264 listed; SDP requires SPS/PPS; H265 not listed in this captured support table','android-rtsp','H264')
add('Android Media3 RTSP','transport','UDP unicast and interleaved TCP; multicast unsupported','android-rtsp','multicast is not supported')
add('Android foreground service','background-start','Background FGS starts restricted for apps targeting Android 12 or higher, with exceptions','android-background','while the app is running in the background')
add('MAVLink redundancy guidance','packet-dedup','Per-channel packet sequence counters cannot deduplicate messages across links','mavlink-redundancy','each channel has its own sequence counter')
add('MAVLink manual control','manual-axis','Vehicle-frame axes normalised to -1000 through 1000; not proof of Hera RC transport','mavlink-manual','-1000 to 1000')
add('MAVLink common messages','rtcm-carrier','GPS_RTCM_DATA carries RTCM correction data to GPS','mavlink-common','GPS_RTCM_DATA')
add('MAVLink signing guidance','signing','MAVLink 2 signature validation and unsigned acceptance policies','mavlink-signing','signature is valid')
add('GStreamer candidate','rtsp-source','rtspsrc supports RTSP UDP/TCP unicast/multicast','gstreamer-rtsp','unicast or multicast mode')
add('GStreamer candidate','h265-depayload','rtph265depay extracts H265 from RTP; does not itself decode video','gstreamer-h265','Extracts H265')
unknowns=['device-sdk-url','current-channel-map','installed-radio','installed-codec-limits','measured-latency','controller-battery-api','controller-bsp-update','production-signer','installed-build','live-video-codec','api-endpoints']
fields=sorted({c['field'] for c in claims}|set(unknowns))
cfg={'domain':'herahub-software-20261012','entity_label':'Version-scoped software integration evidence','schema':{'type_field':None,'fields':fields},'rollup_field':None,'universe':{'estimate':None,'basis':'45 selected public capture requests, not exhaustive product/SDK coverage'},'alias_map':{},'ambiguous_clusters':[[old,new],['RtR HeraLink (historical naming)','CubePilot HereLink']],'domain_gates':{'no_inferred_fields':['soc','os','abi',*unknowns]}}
(D/'domain.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False))
(D/'claims.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in claims))
print(json.dumps({'claims':len(claims),'entities':len({c['entity'] for c in claims}),'captured':sum(r['status']=='captured' for r in records),'unavailable':sum(r['status']!='captured' for r in records),'spans_checked':True}))
