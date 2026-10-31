"""Explicit primary-source claim extraction; proposed AERIS features remain separate."""
from pathlib import Path
import json,datetime,hashlib,yaml,html,re
D=Path(__file__).resolve().parent
captures=json.loads((D/'captures.json').read_text())['sources']+json.loads((D/'captures-followup.json').read_text())['sources']
sources={x['id']:x for x in captures if x['status']=='CAPTURED_PRIMARY_HTML'}
# Short verbatim anchors, <=25 words combined per source; values are paraphrases.
items=[
 ('DJI M4 / Detection','dji-m4','built-in model can detect','Manufacturer advertises onboard object detection; hardware/model dependent.'),
 ('DJI M4 / Tracking','dji-m4','Smart Track','Manufacturer advertises subject tracking, zoom adjustment and reacquisition.'),
 ('DJI M4 / Guided navigation','dji-m4','FlyTo','Manufacturer advertises assisted destination navigation.'),
 ('DJI M4 / Orbit','dji-m4','POI','Manufacturer advertises point-of-interest observation.'),
 ('DJI M4 / 3D capture','dji-m4','Smart 3D Explore','Matrice4E plus Manifold3 is the stated combination for this modeling feature; not controller-only capability.'),
 ('DJI M4 / Obstacle sensing','dji-m4','fisheye vision sensors','Manufacturer associates avoidance with onboard vision sensors, not a GUI switch.'),
 ('DJI FlightHub2 / Planning','dji-fh2','Flight Route Planning','Manufacturer advertises route planning for multiple terrain and mission needs.'),
 ('DJI FlightHub2 / Collaboration','dji-fh2','Live Annotations','Manufacturer advertises collaborative operational annotations.'),
 ('DJI FlightHub2 / Deployment','dji-fh2','On-Premises','Manufacturer advertises private deployment; edition/API support must be checked.'),
 ('DJI FlightHub2 / AI workflow','dji-fh2','AI agent','Manufacturer advertises an agent for AEC operations; this is not proof of generic LLM flight authority.'),
 ('DJI FlightHub2 / Review','dji-fh2','detailed logs','Manufacturer advertises logs and post-flight operational review.'),
 ('DJI GEO / Rollout2025','dji-geo-new','reclassified as Enhanced Warning Zones','Dated announcement describes transition of remaining NFZs to warning zones, with phased firmware rollout; not universal runtime verification.'),
 ('DJI GEO / Advisory provenance','dji-geo-new','does not replace the official airspace data','Manufacturer states its airspace advisory does not replace authority data.'),
 ('DJI GEO / Legacy scope','dji-geo-legacy','M200','Legacy page identifies product generations; do not project its blocking behavior onto every current DJI configuration.'),
 ('AP / AUTO','ap-auto','stored in the autopilot','AUTO executes a mission on the flight controller; this alone is not learned visual autonomy.'),
 ('AP / Pilot takeover','ap-auto','pilot can retake control','Documentation describes pilot takeover through flight-mode change, subject to configuration.'),
 ('AP / Fence','ap-fence','Inclusion and Exclusion Fences','Autopilot documents configurable inclusion/exclusion fences and breach behavior.'),
 ('AP / GCS loss','ap-gcs-failsafe','will <strong>not</strong> automatically return','Configured autopilot failsafe does not automatically restore the previous mode after link returns.'),
 ('AP / Avoidance','ap-avoidance','AUTO, GUIDED, and RTL','BendyRuler avoidance is mode/configuration dependent, with sensor data and an obstacle database.'),
 ('AP / Terrain','ap-terrain','terrain data','Terrain following requires terrain information; not a complete obstacle model.'),
 ('QGC5.1 / Mission planning','qgc-plan','Survey, Corridor Scan, Structure Scan','Documentation lists mission pattern families, with firmware/vehicle dependencies.'),
 ('QGC5.1 / Containment','qgc-plan','Rally Points','Documentation supports planning containment and recovery points when firmware supports them.'),
 ('QGC5.1 / Flight cockpit','qgc-fly','Camera Tools','Fly view combines flight telemetry, actions, maps and payload tools.'),
 ('QGC5.1 / Video layout','qgc-fly','video or map','Documentation describes switching primary map/video layout.'),
 ('QGC5.1 / Resume distinction','qgc-fly','Continue and','Documentation distinguishes paused-mission continuation from resume after an intermediate landing.'),
 ('Skydio X10 / Integrated autonomy','skydio-x10','embedded AI-driven Autonomy','Manufacturer describes an integrated aircraft/autonomy/application stack, not interchangeable GCS-only AI.'),
 ('Skydio X10 / Survey accuracy','skydio-x10','Accuracy depends on mission planning','Manufacturer conditions survey accuracy on setup, mission planning and reference points.'),
 ('Skydio ecosystem / Navigation','skydio-autonomy','Skydio Pathfinder','Manufacturer advertises automatic path planning; compatible platform and configuration must be established.'),
 ('Skydio ecosystem / Acquisition','skydio-autonomy','3D Scan','Manufacturer advertises automated data acquisition; specific model/package support not inferred for all drones.'),
 ('Android / Touch targets','android-touch','48dpx48dp','Android recommends minimum touch area; glove performance and native geometry still require operator/device checks.'),
 ('NASA / Automation visibility','nasa-interface','Automation System Status Provision','Reference principle: expose automation state and operator authority. Human-spaceflight guidance used by analogy.'),
 ('NASA / Decision explanations','nasa-interface','Decision Aid Clarity','Reference principle: explain suggested actions and their consequences; not UAV certification.'),
 ('NASA / Automation recovery','nasa-interface','Automation Failure Recovery','Reference principle: enable safe operator recovery from automation failure; not a prescriptive Hera control binding.'),
 ('Vietnam / Official airspace entry','vn-airspace','cambay.mod.gov.vn','Government publication identifies the Ministry of Defence airspace map entry point; usable live dataset/API/update integration remains unverified.'),
 ('RAGAS public / Shared video','rtr-ragas','Air-to-Ground Streaming','RtR advertises sharing airborne video to ground devices.'),
 ('RAGAS public / Ground feeds','rtr-ragas','Ground-to-Air Streaming','RtR advertises feeding ground video into the GCS.'),
 ('RAGAS public / Geographic picture','rtr-ragas','Unified Map View','RtR advertises map-based aircraft, camera and ground participant context.'),
 ('HeraHub Intel / Operator roles','rtr-herahub','Dual-Operator Mode','Manufacturer advertises separate flight and payload operator roles on this Intel controller page.'),
 ('HeraHub Intel / Streams','rtr-herahub','up to 8 simultaneous 1080p','Intel-generation manufacturer stream-capacity claim; not a measured Android v2 decoder limit.'),
]
rows=[];wordCounts={}
for entity,source,span,value in items:
 raw=(D/'snapshots'/(source+'.html')).read_text()
 if html.unescape(span) not in html.unescape(raw):raise RuntimeError('Evidence anchor missing: '+source+' '+span)
 cap=sources[source];domain=__import__('urllib.parse',fromlist=['urlparse']).urlparse(cap['url']).hostname
 origin='dji.com' if domain.endswith('dji.com') else 'rtrobotics.com' if domain.endswith('rtrobotics.com') else domain
 wordCounts[source]=wordCounts.get(source,0)+len(span.split())
 rows.append({'entity':entity,'field':'documented_capability','value':value,'evidence_span':span,'extraction':'normalized','tier':'A','capture':{'url':cap['url'],'fetched_at':cap['fetchedAt'],'snapshot':source+'.html','source':origin},'sourceNature':'First-party assertion/documentation; no independent performance verification'})
assert max(wordCounts.values())<=25,wordCounts
cfg={'domain':'uav_gcs_capabilities_20261014','entity_label':'Selected documented capability assertions','schema':{'type_field':'deployment_scope','fields':['documented_capability','deployment_scope','independent_performance']},'rollup_field':'deployment_scope','universe':{'estimate':len(items),'basis':'Closed set of selected capability entities in this research, not the universe of products/features or market coverage'},'refresh_days':{'default':30},'alias_map':{},'ambiguous_clusters':[['DJI M4 / Tracking','Skydio ecosystem / Navigation']],'domain_gates':{'no_inferred_fields':['documented_capability']}}
(D/'domain.yaml').write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False))
(D/'claims.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n')
(D/'extraction-summary.json').write_text(json.dumps({'claims':len(rows),'selectedEntities':len(items),'quotedAnchorWordsBySource':wordCounts,'independentPerformance':'HONEST_NULL','notes':'Registry facts concern what documentation asserts; no competitor test or AERIS feature promotion.'},indent=2)+'\n')
print(json.dumps({'claims':len(rows),'sourcesUsed':len(wordCounts)}))
