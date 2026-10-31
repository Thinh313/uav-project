#!/usr/bin/env python3
"""Build/run deterministic offline corpus; retains each attempt's receipts."""
import argparse,copy,datetime,hashlib,json,math,os,random,subprocess,sys,time,statistics,resource,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];EVIDENCE=ROOT/'evidence/mission55'
sys.path.insert(0,str(HERE/'vendor'))
from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea
from semantic import canonical,digest,load_plan,compare_plans,compare_readback,capture_evidence,ContractError
from wire import decode_item,inventory_cycles,x25
from geometry import compare_geometry,metrics,compare_measurement

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def disk_gate():
    fs=os.statvfs(ROOT)
    if fs.f_bavail*fs.f_frsize<20*1024**3+10*1024**2:raise SystemExit('DISK_FLOOR')
def json_write(path,value):
    disk_gate();path.parent.mkdir(exist_ok=True,parents=True)
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    if path.exists():
        if path.read_text()!=text:raise RuntimeError('No overwrite: '+str(path))
    else:path.write_text(text)
ap=argparse.ArgumentParser();ap.add_argument('--attempt',default='run1');args=ap.parse_args()
if not args.attempt.isalnum():raise SystemExit('Attempt name must be alphanumeric')
out=EVIDENCE/args.attempt
if out.exists():raise SystemExit('Attempt already exists')
disk_gate();out.mkdir()
checks=[];corpus=[];fixtures=HERE/'fixtures'/args.attempt;fixtures.mkdir(exist_ok=True,parents=True)
json_write(out/'source-at-start.json',{'files':{str(p.relative_to(ROOT)):sha(p) for p in HERE.glob('*') if p.suffix in ['.py','.mjs']}})
def check(name,fn,scope='OFFLINE_CONTRACT'):
    try:
        value=fn();ok=bool(value);checks.append({'name':name,'pass':ok,'scope':scope,'detail':value})
    except Exception as e:checks.append({'name':name,'pass':False,'scope':scope,'error':type(e).__name__+': '+str(e)})
def rejects(fn,reason):
    try:fn()
    except ContractError as e:return reason in str(e)
    return False
def add_plan(name,data,origin='SYNTHETIC',parent=None):
    p=fixtures/(name+'.plan');json_write(p,data)
    row={'id':name,'path':str(p.relative_to(ROOT)),'sha256':sha(p),'provenance':origin,'parent':parent,'producer':'MISSION55 fixture builder; NOT QGC application'}
    corpus.append(row);return p.read_text()
def mutate(data,path,value):
    target=copy.deepcopy(data);ptr=target
    for k in path[:-1]:ptr=ptr[k]
    ptr[path[-1]]=value;return target
def item(cmd,params,frame=2,mode=None):
    i={'type':'SimpleItem','command':cmd,'params':params,'frame':frame,'autoContinue':True,'doJumpId':1}
    if mode is not None:i.update({'AltitudeMode':mode,'Altitude':50,'AMSLAltAboveTerrain':None})
    return i
def numbered(plan):
    n=1
    for i in plan['mission']['items']:
        for c in i['TransectStyleComplexItem']['Items'] if i['type']=='ComplexItem' else [i]:c['doJumpId']=n;n+=1
    return plan

base={'fileType':'Plan','version':1,'groundStation':'MISSION55-SYNTHETIC','geoFence':{'version':2,'circles':[],'polygons':[]},
 'rallyPoints':{'version':2,'points':[]},'mission':{'version':2,'firmwareType':3,'vehicleType':2,'cruiseSpeed':6,'hoverSpeed':2,
 'globalPlanAltitudeMode':0,'plannedHomePosition':[10.854,106.807,100],'items':[
 item(22,[0,0,0,None,10.854,106.807,50],3,1),item(206,[8,0,1,0,0,0,0]),
 item(16,[0,0,0,None,10.855,106.807,50],3,1),item(206,[0,0,0,0,0,0,0]),
 item(2000,[1,2,5,0,None,None,None]),item(2001,[0,None,None,None,None,None,None]),
 item(2500,[1,0,0,0,None,None,None]),item(2501,[1,0,None,None,None,None,None]),
 item(16,[0,0,0,None,10.855,106.808,50],0,2),item(20,[0,0,0,0,0,0,0])
 ]}}
numbered(base);base_raw=add_plan('camera-mixed-altitude',base)
check('baseline-synthetic-self-equal',lambda:compare_plans(base_raw,base_raw)['verdict']=='EQUAL_DECLARED_SCOPE')
camera_mutations=[
 ('placeholder',['mission','items',1,'command'],0,'command'),
 ('distance',['mission','items',1,'params',0],9,'params[0]'),
 ('immediate',['mission','items',1,'params',2],0,'params[2]'),
 ('camera-id',['mission','items',4,'params',0],2,'params[0]'),
 ('image-period',['mission','items',4,'params',1],3,'params[1]'),
 ('image-count',['mission','items',4,'params',2],6,'params[2]'),
 ('reserved-null-zero',['mission','items',5,'params',1],0,'params[1]'),
 ('video-stop-id',['mission','items',7,'params',0],2,'params[0]'),
 ('distance-camera-id',['mission','items',1,'params',3],100,'params[3]'),
 ('video-start-camera-id',['mission','items',6,'params',2],100,'params[2]'),
 ('video-stop-camera-id',['mission','items',7,'params',1],100,'params[1]'),
 ('home-height',['mission','plannedHomePosition',2],97,'plannedHomePosition[2]'),
 ('home-position',['mission','plannedHomePosition',0],10.85403,'plannedHomePosition[0]'),
 ('cruise-not-hover',['mission','cruiseSpeed'],12,'cruiseSpeed'),
 ('label-change',['mission','items',2,'doJumpId'],90,'doJumpId'),
 ('nav-null-yaw-zero',['mission','items',2,'params',3],0,'params[3]'),
 ('fence-change',['geoFence','circles'],[{'inclusion':True,'radius':100,'circle':[10.854,106.807]}],'geoFence'),
 ('rally-change',['rallyPoints','points'],[[10.854,106.807,20]],'rallyPoints'),
]
for name,path,value,needle in camera_mutations:
    changed=add_plan(name,mutate(base,path,value),'SYNTHETIC_DERIVATIVE','camera-mixed-altitude')
    def probe(changed=changed,needle=needle):
        result=compare_plans(base_raw,changed)
        return result['verdict']=='DIFFERENT' and any(needle in d['path'] for ds in result['differences'].values() for d in ds)
    check('detect:'+name,probe,'MUTATION')
for name,transform in [('drop-camera',lambda x:x['mission']['items'].pop(1)),('reorder-camera',lambda x:x['mission']['items'].reverse())]:
    d=copy.deepcopy(base);transform(d);raw=add_plan(name,d,'SYNTHETIC_DERIVATIVE','camera-mixed-altitude')
    check('detect:'+name,lambda raw=raw:compare_plans(base_raw,raw)['verdict']=='DIFFERENT','MUTATION')

survey_path=ROOT/'app/fixtures/qgc/desktop/qgc-survey-angle35.plan'
survey=json.loads(survey_path.read_text());parent={'path':str(survey_path.relative_to(ROOT)),'sha256':sha(survey_path)}
survey_raw=add_plan('survey35-retained-derived',copy.deepcopy(survey),'SYNTHETIC_DERIVATIVE_OF_QGC51',parent)
for name,path,value in [
 ('survey-angle',['mission','items',2,'angle'],90),('survey-entry',['mission','items',2,'entryLocation'],3),
 ('survey-alternate',['mission','items',2,'flyAlternateTransects'],True),
 ('survey-concave',['mission','items',2,'splitConcavePolygons'],False),
 ('survey-refly',['mission','items',2,'TransectStyleComplexItem','Refly90Degrees'],True),
 ('survey-shot-count',['mission','items',2,'TransectStyleComplexItem','CameraShots'],99),
 ('survey-overlap-footprint',['mission','items',2,'TransectStyleComplexItem','CameraCalc','AdjustedFootprintFrontal'],8),
 ('survey-cache-placeholder',['mission','items',2,'TransectStyleComplexItem','Items',1,'command'],0),
 ('survey-vertex',['mission','items',2,'polygon',0,0],10.8539),
]:
    changed=add_plan(name,mutate(survey,path,value),'SYNTHETIC_DERIVATIVE_NOT_REGENERATED',parent)
    check('detect:'+name,lambda changed=changed:compare_plans(survey_raw,changed)['verdict']=='DIFFERENT','MUTATION')
changed=mutate(survey,['mission','items',2,'angle'],90)
check('design-change-cannot-hide-behind-equal-cache',lambda:(lambda d:bool(d['differences']['design']) and not d['differences']['executable'])(compare_plans(survey_raw,json.dumps(changed))))
flat=copy.deepcopy(survey);flat['mission']['items']=[]
for i in survey['mission']['items']:flat['mission']['items'].extend(i['TransectStyleComplexItem']['Items'] if i['type']=='ComplexItem' else [i])
flatraw=add_plan('survey-flattened-snapshot',flat,'SYNTHETIC_DERIVATIVE_LOST_EDITABLE_DESIGN',parent)
check('flatten-not-editable-equivalence',lambda:(lambda d:d['verdict']=='DIFFERENT' and bool(d['differences']['design']) and not d['differences']['executable'])(compare_plans(survey_raw,flatraw)))
two=copy.deepcopy(survey);two['mission']['items'].insert(3,copy.deepcopy(two['mission']['items'][2]));numbered(two)
add_plan('two-survey-patterns-synthetic',two,'SYNTHETIC_DUPLICATE_GEOMETRY_NOT_REGENERATED',parent)
for angle in [0,35,90,179]:add_plan('angle-recipe-'+str(angle),mutate(survey,['mission','items',2,'angle'],angle),'SYNTHETIC_DESIGN_ONLY_NOT_REGENERATED',parent)

for name,d,expected in [
 ('extension-retained',base|{'vendorExtension':{'mode':'unknown'}},'REVIEW_REQUIRED'),
 ('jump-unsupported',numbered(mutate(base,['mission','items',1,'command'],177)),'REVIEW_REQUIRED'),
]:
    raw=add_plan(name,d,'SYNTHETIC_UNSUPPORTED_REVIEW_ONLY')
    check('unsupported:'+name,lambda raw=raw,expected=expected:compare_plans(raw,raw)['verdict']==expected)
unknown=base|{'vendorExtension':{'mode':'unknown'}}
check('extension-drop-visible',lambda:compare_plans(json.dumps(unknown),base_raw)['verdict']=='DIFFERENT','MUTATION')
for name,d,reason in [
 ('bool-param',mutate(base,['mission','items',1,'params',0],True),'PARAM_TYPE'),
 ('axis-swap',mutate(base,['mission','plannedHomePosition'],[106.807,10.854,100]),'COORD_RANGE'),
 ('unknown-version',base|{'version':2},'PLAN_SCHEMA'),
 ('frame-conflict',mutate(base,['mission','items',0,'frame'],0),'ALTITUDE_MODE_FRAME'),
 ('display-alt-conflict',mutate(base,['mission','items',0,'Altitude'],60),'ALTITUDE_DISPLAY'),
 ('terrain-no-data',mutate(base,['mission','items',0,'AltitudeMode'],3),'ALTITUDE_MODE_FRAME'),
 ('missing-cache',mutate(survey,['mission','items',2,'TransectStyleComplexItem','Items'],[]),'CACHED_ITEMS'),
 ('negative-interval',mutate(base,['mission','items',4,'params',1],-1),'CAPTURE_INTERVAL_COUNT'),
 ('fractional-camera-id',mutate(base,['mission','items',4,'params',0],1.5),'CAMERA_ID'),
 ('bad-single-capture-sequence',mutate(base,['mission','items',4,'params',2],1),'CAPTURE_SEQUENCE'),
 ('bad-video-camera-id',mutate(base,['mission','items',7,'params',1],256),'CAMERA_ID'),
]:
    raw=add_plan(name,d,'SYNTHETIC_INVALID_NEGATIVE')
    check('reject:'+name,lambda raw=raw,reason=reason:rejects(lambda:load_plan(raw),reason),'INVALID_INPUT')
check('reject:duplicate-json-key',lambda:rejects(lambda:load_plan('{"version":1,"version":2}'),'DUPLICATE_KEY'),'INVALID_INPUT')
check('reject:NaN',lambda:rejects(lambda:load_plan(base_raw.replace('"cruiseSpeed": 6','"cruiseSpeed": NaN')),'NON_FINITE'),'INVALID_INPUT')
check('reject:oversize',lambda:rejects(lambda:load_plan(' '*262145),'INPUT_LIMIT'),'INVALID_INPUT')
check('reject:JSON-depth',lambda:rejects(lambda:load_plan('['*40+'0'+']'*40),'JSON_DEPTH_LIMIT'),'INVALID_INPUT')
for d in [mutate(base,['mission','items',8,'frame'],10),mutate(base,['mission','items',8,'AltitudeMode'],4)]:
    check('reject:ambiguous-altitude-'+str(len(checks)),lambda d=d:rejects(lambda:load_plan(json.dumps(d)),'ALTITUDE_MODE_FRAME'),'INVALID_INPUT')

# Genuine QGC files are referenced and hash-bound; no new QGC production claim.
retained=json.loads((ROOT/'research/ragas54/reuse.json').read_text())['fixtures']
for f in retained:
    p=ROOT/f['path'];check('retained-fixture-sha:'+p.stem,lambda p=p,f=f:sha(p)==f['expected'],'RETAINED_PROVENANCE')
    check('retained-fixture-self:'+p.stem,lambda p=p:compare_plans(p.read_text(),p.read_text())['verdict'] in ['EQUAL_DECLARED_SCOPE','REVIEW_REQUIRED'],'RETAINED_REPLAY')
before=(ROOT/'app/fixtures/qgc/roundtrip03/simple-relative-input.plan').read_text()
after=(ROOT/'app/fixtures/qgc/roundtrip03/simple-relative-qgc-saved.plan').read_text()
home_diff=compare_plans(before,after);json_write(out/'qgc-home10-to7-diff.json',home_diff)
check('retained-QGC-Home10-to7-still-DIFFERENT',lambda:home_diff['verdict']=='DIFFERENT' and any('plannedHomePosition[2]' in d['path'] for d in home_diff['differences']['header']),'RETAINED_REPLAY')
geographic_diff=compare_geometry(before,after);json_write(out/'qgc-home-height-geometry.json',geographic_diff)
check('Home10-to7-implied-altitude-minus3m',lambda:all(x['impliedAmslDeltaM']==-3 and x['horizontalDeltaM']<1e-6 for x in geographic_diff['alignedNavByOrdinal']),'INDEPENDENT_NUMERICAL_COMPARISON')
geo_survey=metrics(survey_raw);json_write(out/'qgc-survey-geodesic-reference.json',geo_survey)
check('survey-geodesic-reference-positive',lambda:geo_survey['surveys'][0]['geodesicAreaM2']>0,'ORACLE_SERVICE')
check('area-ha-unit-explicit-conversion',lambda:compare_measurement({'value':10000,'unit':'m2','metric':'LOCAL_PLANAR'},{'value':1,'unit':'ha','metric':'LOCAL_PLANAR'},1e-6)['pass'])
check('detect-area-100x-underreport',lambda:compare_measurement({'value':10000,'unit':'m2','metric':'LOCAL_PLANAR'},{'value':100,'unit':'m2','metric':'LOCAL_PLANAR'},1e-6)['verdict']=='DIFFERENT','MUTATION')
check('reject-planar-vs-geodesic-metric',lambda:rejects(lambda:compare_measurement({'value':10000,'unit':'m2','metric':'LOCAL_PLANAR'},{'value':10000,'unit':'m2','metric':'ELLIPSOID_WGS84'},1),'METRIC_MISMATCH'))
check('unknown-photo-count-not-zero',lambda:compare_measurement({'value':None,'unit':'count','metric':'REPORTED'},{'value':0,'unit':'count','metric':'REPORTED'},0)['verdict']=='NOT_CHECKED')
check('integer-photo-count-exact',lambda:rejects(lambda:compare_measurement({'value':5,'unit':'count','metric':'PLANNED'},{'value':5.1,'unit':'count','metric':'PLANNED'},0),'COUNT_EXACT'))
check('feet-to-meter-explicit',lambda:compare_measurement({'value':0.3048,'unit':'m','metric':'ALTITUDE_MODEL'},{'value':1,'unit':'ft','metric':'ALTITUDE_MODEL'},1e-12)['pass'])
for n in range(3):
    reordered=json.dumps(json.loads(base_raw),sort_keys=bool(n%2),indent=None if n%2 else 4)
    check('three-serialization-cycles-'+str(n),lambda reordered=reordered:compare_plans(base_raw,reordered)['verdict']=='EQUAL_DECLARED_SCOPE','METAMORPHIC')

# Raw upload byte decoder and historical decoded readback comparison are separate.
replay=[]
for label in ['simple-relative','survey-absolute']:
    p=ROOT/f'evidence/qgc03/sitl/{label}-journal.json';j=json.loads(p.read_text())
    inventory=inventory_cycles(j)
    accepted=(ROOT/f'evidence/qgc03/sitl/{label}-accepted.plan').read_text()
    results=[]
    for n,cycle in enumerate(inventory['cycles']):
        context={'profile':'copter4.7.1-qgc03-retained-v1','source':[1,1],'receiver':[255,190],
          'session':j['sessionId'],'expectedSession':j['sessionId'],'boot':'NOT_RECORDED','expectedBoot':'NOT_RECORDED',
          'ageMs':0,'maxAgeMs':10000,'ageBasis':'synthetic replay context, not live freshness',
          'observedHome':[cycle[0]['x']/1e7,cycle[0]['y']/1e7,cycle[0]['z']]}
        result=compare_readback(accepted,cycle,context);results.append(result)
        check(f'{label}-readback-cycle{n}-classified',lambda result=result:result['verdict'] in ['MATCH_RETAINED_READBACK_SCOPE','DIFFERENT'],'RETAINED_REPLAY')
    check(label+'-at-least-one-matched-readback',lambda results=results:any(r['verdict']=='MATCH_RETAINED_READBACK_SCOPE' for r in results),'RETAINED_REPLAY')
    check(label+'-raw-upload-19-items',lambda inventory=inventory:len(inventory['outboundCycles'])==1 and len(inventory['outboundCycles'][0])==19,'RAW_RETAINED_REPLAY')
    raw_entry=next(f for f in j['frames'] if f.get('direction')=='out' and f.get('id')==73 and f.get('sessionId')==j['sessionId'])
    raw=bytearray.fromhex(raw_entry['hex']);raw[12]^=1
    check(label+'-CRC-flip-rejected',lambda raw=raw:rejects(lambda:decode_item(raw.hex()),'FRAME_CRC'),'FAULT_INJECTION')
    cycle=inventory['cycles'][0];context['observedHome']=[cycle[0]['x']/1e7,cycle[0]['y']/1e7,cycle[0]['z']]
    for name,key,value,reason in [('wrong-source','source',[2,1],'ENVELOPE_ROUTE'),('wrong-receiver','receiver',[1,1],'ENVELOPE_ROUTE'),
                               ('wrong-session','session','foreign','SESSION_BOOT'),('reboot','boot',2,'SESSION_BOOT'),('stale','ageMs',10001,'STALE')]:
        bad=context|{key:value}
        check(label+'-reject-'+name,lambda bad=bad:rejects(lambda:compare_readback(accepted,cycle,bad),reason),'FAULT_INJECTION')
    for field,value in [('command',0),('param1',999),('target_component',100),('frame',10),('mission_type',1)]:
        bad=copy.deepcopy(cycle);bad[4][field]=value
        check(label+'-reject-readback-'+field,lambda bad=bad:compare_readback(accepted,bad,context)['verdict']=='DIFFERENT','MUTATION')
    check(label+'-unbounded-freshness-policy-rejected',lambda:rejects(lambda:compare_readback(accepted,cycle,context|{'maxAgeMs':1e9}),'UNPINNED_FRESHNESS_POLICY'),'FAULT_INJECTION')
    replay.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'inventory':inventory,'comparisons':results,
                   'bootEvidence':'NOT_RECORDED','inboundRawCRC':'NOT_CHECKED','newSITLFlight':False})
json_write(out/'retained-replay.json',replay)

# CRC-extra re-derived from pinned official common.xml for message73.
xml=ET.parse(EVIDENCE/'sources/mavlink-common.xml').getroot();msg=next(x for x in xml.findall('.//message') if x.get('id')=='73')
fields=[]
for field in msg:
    if field.tag=='extensions':break
    if field.tag=='field':fields.append(field)
sizes={'float':4,'int32_t':4,'uint16_t':2,'uint8_t':1}
fields.sort(key=lambda f:-sizes[f.get('type')])
crc=x25(b'MISSION_ITEM_INT ')
for f in fields:crc=x25((f.get('type')+' '+f.get('name')+' ').encode(),crc)
check('CRC-extra-derived-from-official-schema',lambda:((crc&255)^(crc>>8))==38,'SCHEMA_ORACLE')

identity={'aircraft':'HERA-SYNTHETIC','camera':1,'session':'mock1','boot':1,'clockId':'mock-clock1','maxAgeMs':10000}
ack=identity|{'kind':'ACK','ageMs':100};reported=identity|{'kind':'CAPTURE_REPORTED','index':7,'ageMs':100};file=identity|{'kind':'FILE_VERIFIED','sha256':'0'*64,'ageMs':100}
check('ACK-not-image',lambda:capture_evidence([ack],identity)['reportedUnique']==0)
check('reported-not-file',lambda:capture_evidence([ack,reported,file],identity)['verifiedPhysicalFiles']==0)
check('duplicate-capture-deduplicated',lambda:capture_evidence([reported,reported],identity)['reportedUnique']==1)
check('foreign-camera-does-not-count',lambda:capture_evidence([reported|{'camera':2}],identity)['reportedUnique']==0)
check('foreign-session-does-not-count',lambda:capture_evidence([reported|{'session':'old'}],identity)['reportedUnique']==0)
check('stale-capture-does-not-count',lambda:capture_evidence([reported|{'ageMs':10001}],identity)['reportedUnique']==0)
check('foreign-clock-does-not-count',lambda:capture_evidence([reported|{'clockId':'old-clock'}],identity)['reportedUnique']==0)
check('unknown-clock-identity-rejected',lambda:rejects(lambda:capture_evidence([reported],identity|{'clockId':None}),'EVIDENCE_IDENTITY_OR_CLOCK'))
check('negative-capture-age-does-not-count',lambda:capture_evidence([reported|{'ageMs':-1}],identity)['reportedUnique']==0)

# Independent numerical oracle: Python GeographicLib/Decimal-derived analytic values vs JS.
numeric=[]
def numeric_case(name,op,inputs,expected=None,error=None,tolerance=1e-6):
    numeric.append({'id':name,'op':op,'args':inputs,'expected':expected,'expectedError':error,'absoluteTolerance':tolerance})
numeric_case('area-square','area',{'points':[[0,0],[100,0],[100,100],[0,100]],'frame':'LOCAL_PLANAR_METERS'},{'areaM2':10000,'hectares':1})
numeric_case('area-triangle','area',{'points':[[0,0],[100,0],[0,100]],'frame':'LOCAL_PLANAR_METERS'},{'areaM2':5000})
numeric_case('area-concave','area',{'points':[[0,0],[100,0],[100,50],[50,50],[50,100],[0,100]],'frame':'LOCAL_PLANAR_METERS'},{'areaM2':7500})
numeric_case('area-reversed-offset','area',{'points':[[1e8,1e8],[1e8,1e8+100],[1e8+100,1e8+100],[1e8+100,1e8]],'frame':'LOCAL_PLANAR_METERS'},{'areaM2':10000})
numeric_case('area-bowtie','area',{'points':[[0,0],[100,100],[0,100],[100,0]],'frame':'LOCAL_PLANAR_METERS'},error='SELF_INTERSECTION')
numeric_case('area-not-declared','area',{'points':[[0,0],[100,0],[0,100]],'frame':'WGS84'},error='METRIC_NOT_DECLARED')
numeric_case('ETA-1000m-6mps','time',{'legs':[{'distanceM':1000,'speedMps':6,'delayS':0}]},{'seconds':1000/6})
numeric_case('ETA-two-speeds-hover','time',{'legs':[{'distanceM':120,'speedMps':6,'delayS':60},{'distanceM':60,'speedMps':3,'delayS':1}]},{'seconds':101})
numeric_case('ETA-zero-speed','time',{'legs':[{'distanceM':100,'speedMps':0,'delayS':0}]},error='LEG_INVALID')
cam={'heightM':100,'sensorWidthMm':36,'focalLengthMm':50,'imageWidthPx':6000,'footprintAlongM':40,'frontOverlap':0.8,'velocityMps':10,'minPeriodS':1}
numeric_case('camera-80-overlap-too-fast','camera',cam,{'spacingM':8,'periodS':0.8,'gsdM':0.012,'cadence':'MODEL_TOO_FAST'})
numeric_case('camera-boundary-1second','camera',cam|{'velocityMps':8},{'cadence':'MODEL_FEASIBLE'})
numeric_case('camera-cycle-unknown','camera',cam|{'minPeriodS':None},{'cadence':'NOT_CHECKED'})
numeric_case('camera-overlap-100-invalid','camera',cam|{'frontOverlap':1},error='OVERLAP')
policy={'name':'EXPLICIT_ENDPOINT_GRID_V1','includeEntry':True,'includeExit':True}
numeric_case('photos-per-transect-not-whole-rounding','photos',{'lengths':[32,33],'spacingM':8,'policy':policy},{'counts':[5,6],'total':11})
numeric_case('photos-unknown-endpoint-policy','photos',{'lengths':[32],'spacingM':8,'policy':None},error='POLICY_REQUIRED')
numeric_case('photos-zero-distance','photos',{'lengths':[32],'spacingM':0,'policy':policy},error='POLICY_REQUIRED')
ctx={'session':'s1','boot':1,'datum':'EGM2008','maxAgeMs':10000}
source={'session':'s1','boot':1,'datum':'EGM2008','ageMs':100,'lat':10.854,'lon':106.807}
ctx|={'home':source|{'amslM':100},'terrain':source|{'amslM':120,'sha256':'a'*64,'noData':False},
      'geoid':source|{'separationM':30,'model':'SYNTHETIC-EGM2008','sha256':'b'*64}}
alt={'coordinate':[10.854,106.807],'valueM':50,'mode':'relative'}
for mode,expected in [('relative',{'amslM':150,'frame':3,'z':50}),('amsl',{'amslM':50,'frame':0,'z':50}),
                      ('terrain_calc',{'amslM':170,'frame':0,'z':170}),('terrain_native',{'amslM':170,'frame':10,'z':50}),
                      ('ellipsoid',{'amslM':20,'frame':0,'z':20})]:
    numeric_case('alt-'+mode,'altitude',{'input':alt|{'mode':mode,'datum':'EGM2008'},'context':ctx},expected)
for name,key,changed,error,mode in [
 ('home-stale','home',{'ageMs':10001},'STALE','relative'),('reboot','home',{'boot':2},'SESSION_BOOT','relative'),
 ('home-datum-unknown','home',{'datum':'UNKNOWN'},'DATUM','relative'),('terrain-missing','terrain',None,'SESSION_BOOT','terrain_calc'),
 ('terrain-no-data','terrain',{'noData':True},'NODATA','terrain_calc'),('terrain-hash-bad','terrain',{'sha256':'bad'},'HASH','terrain_calc'),
 ('terrain-wrong-position','terrain',{'lon':106.808},'COORDINATE','terrain_calc'),('terrain-datum','terrain',{'datum':'EGM96'},'DATUM','terrain_calc'),
 ('geoid-wrong-sign-case','geoid',{'separationM':-30},None,'ellipsoid')]:
    c=copy.deepcopy(ctx);c[key]=None if changed is None else c[key]|changed
    numeric_case('alt-fault-'+name,'altitude',{'input':alt|{'mode':mode},'context':c},expected={'amslM':80} if error is None else None,error=error)
numeric_case('ridge-midleg-conflict','ridge',{'ground':[120,180,120],'plannedM':150},{'clearanceM':[30,-30,30],'minimumM':-30,'modelConflict':True})
numeric_case('ridge-no-data','ridge',{'ground':[120,None,120],'plannedM':150},error='NO_DATA')

vectors=json.loads((HERE/'geodesic-vectors.json').read_text())
for n,v in enumerate(vectors['vectors']):
    a=[v[0],(v[1]+180)%360-180];b=[v[3],(v[4]+180)%360-180]
    ref=Geodesic.WGS84.Inverse(*a,*b)['s12']
    check('geographiclib-upstream-vector-'+str(n),lambda ref=ref,v=v:abs(ref-v[6])<1e-7,'PRIMARY_NUMERICAL_ORACLE')
    numeric_case('inverse-upstream-'+str(n),'inverse',{'a':a,'b':b},{'distanceM':ref},tolerance=0.001)
for n,(a,b) in enumerate([([10.854,106.807],[10.855,106.808]),([0,179.999],[0,-179.999]),([89.9,0],[89.9,90]),([-30,-70],[-30.1,-70.1]),([10,10],[10,10])]):
    numeric_case('inverse-edge-'+str(n),'inverse',{'a':a,'b':b},{'distanceM':Geodesic.WGS84.Inverse(*a,*b)['s12']},tolerance=0.001)
numeric_case('inverse-antipodal-rejects-no-fallback','inverse',{'a':[0,0],'b':[0,180]},error='GEODESIC_NONCONVERGENT_NO_SPHERE_FALLBACK')
numeric_case('inverse-invalid-axis','inverse',{'a':[106,10],'b':[10,11]},error='RANGE')
random.seed(55)
for n in range(20):
    a=[random.uniform(-80,80),random.uniform(-170,170)];b=[a[0]+random.uniform(-.01,.01),a[1]+random.uniform(-.01,.01)]
    numeric_case('inverse-local-seed55-'+str(n),'inverse',{'a':a,'b':b},{'distanceM':Geodesic.WGS84.Inverse(*a,*b)['s12']},tolerance=0.001)
json_write(out/'numeric-corpus.json',numeric)
run=subprocess.run(['node',str(HERE/'geo_cli.mjs')],input=json.dumps(numeric),text=True,capture_output=True,timeout=20)
if run.returncode:raise RuntimeError(run.stderr)
observed=json.loads(run.stdout);by_id={v['id']:v for v in observed}
def close_fields(expected,actual,tol):
    if isinstance(expected,dict):return all(k in actual and close_fields(v,actual[k],tol) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(actual,list) and len(expected)==len(actual) and all(close_fields(a,b,tol) for a,b in zip(expected,actual))
    if type(expected) in (float,int):return type(actual) in (float,int) and math.isfinite(actual) and abs(expected-actual)<=tol
    return type(expected) is type(actual) and expected==actual
for case in numeric:
    ob=by_id[case['id']]
    check('numeric:'+case['id'],lambda case=case,ob=ob:(not ob['ok'] and case['expectedError'] in ob['error']) if case['expectedError'] else ob['ok'] and close_fields(case['expected'],ob['result'],case['absoluteTolerance']),'INDEPENDENT_NUMERICAL_COMPARISON')
json_write(out/'numeric-observed.json',observed)

# Ellipsoidal polygon area is an oracle service, not replaced by planar shoelace.
poly=PolygonArea(Geodesic.WGS84,False)
for lat,lon in [[89,0],[89,90],[89,180],[89,270]]:poly.AddPoint(lat,lon)
geodesic_area=poly.Compute(False,True)[2]
check('ellipsoid-area-vs-published-polar-square',lambda:abs(geodesic_area-24952305678.0)<1,'PRIMARY_NUMERICAL_ORACLE')
json_write(out/'ellipsoid-area-oracle.json',{'coordinatesLatLon':[[89,0],[89,90],[89,180],[89,-90]],'areaM2':geodesic_area,
 'method':'GeographicLib2.1 PolygonArea WGS84','candidateAerisGeodesicArea':'NOT_CHECKED',
 'scope':'Oracle-only ellipsoidal area; local planar area must not be compared as same metric'})

# Bounded large-input comparison, and a measured microbenchmark, not UI/AP latency.
large=copy.deepcopy(base);large['mission']['items']=[copy.deepcopy(base['mission']['items'][2]) for n in range(1000)]
numbered(large);large_raw=canonical(large)
large_changed=copy.deepcopy(large);large_changed['mission']['items'][-1]['params'][5]+=1e-7
large_changed_raw=canonical(large_changed)
check('1000-item-final-coordinate-mutation-visible',lambda:compare_plans(large_raw,large_changed_raw)['verdict']=='DIFFERENT','RESOURCE_BOUNDARY')
durations=[]
for n in range(20):
    start=time.perf_counter_ns();compare_plans(large_raw,large_changed_raw);durations.append((time.perf_counter_ns()-start)/1e6)
perf={'case':'1000-item pair strict diff','samples':len(durations),'inputBytes':[len(large_raw.encode()),len(large_changed_raw.encode())],
      'medianMs':statistics.median(durations),'p95Ms':sorted(durations)[math.ceil(.95*len(durations))-1],
      'maxMs':max(durations),'processMaxRssBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      'engineeringBudgetMs':500,'scope':'Local standalone comparator microbenchmark only; not RAGAS/Fly/HeraHub/UI/AP/SITL latency'}
check('1000-item-comparison-p95-under500ms',lambda:perf['p95Ms']<500,'HOST_MICROBENCHMARK')
json_write(out/'performance.json',perf)

json_write(out/'corpus.json',{'schema':1,'generated':corpus,'retained':retained,
 'newQgcExports':0,'newRagasRuns':0,'generatedGridRegeneration':'NOT_CHECKED','scope':'Synthetic/derived fixtures plus hash-pinned retained files'})
report={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':args.attempt,'passed':sum(c['pass'] for c in checks),
 'failed':sum(not c['pass'] for c in checks),'checks':checks,'generatedPlans':len(corpus),'retainedFixtures':len(retained),
 'numericCases':len(numeric),'rawOutboundFramesDecoded':sum(x['inventory']['decodedRawFrames'] for x in replay),
 'readbackCycles':sum(len(x['inventory']['cycles']) for x in replay),'newSITLFlights':0,'RAGASRuntime':'NOT_CHECKED',
 'QgcRegeneration':'NOT_CHECKED','physicalImages':'NOT_CHECKED','flightReady':False,
 'scope':'Offline semantic/math/corpus acceptance only; no product, hardware, binary or field acceptance'}
json_write(out/'verification.json',report)
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
if report['failed']:print(json.dumps([c for c in checks if not c['pass']],ensure_ascii=False,indent=2))
sys.exit(bool(report['failed']))
