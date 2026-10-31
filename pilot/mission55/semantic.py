"""Independent bounded QGC reader/comparator. No flight transport or app imports."""
import hashlib, json, math, struct

class ContractError(ValueError):pass
def require(ok, reason):
    if not ok:raise ContractError(reason)
def number(x):return type(x) in (int,float) and math.isfinite(x)
def integer(x):return type(x) is int
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        require(k not in d,'DUPLICATE_KEY:'+k);d[k]=v
    return d
def reject_constant(s):raise ContractError('NON_FINITE_JSON:'+s)
def read_json(raw):
    require(isinstance(raw,str) and len(raw.encode())<=262144,'INPUT_LIMIT_256K')
    try:
        result=json.loads(raw.lstrip('\ufeff'),object_pairs_hook=unique_pairs,parse_constant=reject_constant)
        pending=[(result,0)]
        while pending:
            value,depth=pending.pop();require(depth<=32,'JSON_DEPTH_LIMIT')
            if isinstance(value,dict):pending.extend((v,depth+1) for v in value.values())
            elif isinstance(value,list):pending.extend((v,depth+1) for v in value)
        return result
    except (json.JSONDecodeError,RecursionError) as e:raise ContractError('JSON_INVALID') from e
def coord(v,n=3):
    require(isinstance(v,list) and len(v)==n and all(number(x) for x in v),'COORD_TYPE')
    require(-90<=v[0]<=90 and -180<=v[1]<=180,'COORD_RANGE_OR_AXIS')

NAV={16,21,22}
CAMERA={206,2000,2001,2500,2501}
SUPPORTED=NAV|CAMERA|{20,178}
SIMPLE_KEYS={'type','params','coordinate','command','frame','autoContinue','doJumpId','Altitude','AltitudeMode','AMSLAltAboveTerrain'}
ROOT_KEYS={'fileType','version','groundStation','mission','geoFence','rallyPoints'}
MISSION_KEYS={'version','firmwareType','vehicleType','cruiseSpeed','hoverSpeed','globalPlanAltitudeMode','plannedHomePosition','items'}
SURVEY_KEYS={'type','version','complexItemType','TransectStyleComplexItem','angle','entryLocation','flyAlternateTransects','polygon','splitConcavePolygons','doJumpId'}
TRANSECT_KEYS={'version','CameraCalc','CameraShots','CameraTriggerInTurnAround','HoverAndCapture','Items','Refly90Degrees','TurnAroundDistance','VisualTransectPoints','FollowTerrain','TerrainAdjustTolerance','TerrainAdjustMaxClimbRate','TerrainAdjustMaxDescentRate'}
CAMERA_KEYS={'version','CameraName','DistanceMode','DistanceToSurface','DistanceToSurfaceRelative','AdjustedFootprintFrontal','AdjustedFootprintSide','CameraOrientationLandscape','FixedOrientation','FocalLength','ImageDensity','ImageHeight','ImageWidth','MinTriggerInterval','SensorHeight','SensorWidth','ValueSetIsDistance'}

def load_plan(raw):
    p=read_json(raw)
    require(isinstance(p,dict) and p.get('fileType')=='Plan' and p.get('version')==1,'PLAN_SCHEMA')
    m=p.get('mission');require(isinstance(m,dict) and m.get('version')==2,'MISSION_SCHEMA')
    coord(m.get('plannedHomePosition'))
    require(all(integer(m.get(k)) for k in ['firmwareType','vehicleType']),'MISSION_IDENTITY')
    if 'globalPlanAltitudeMode' in m:require(integer(m['globalPlanAltitudeMode']) and m['globalPlanAltitudeMode'] in range(6),'GLOBAL_ALTITUDE_MODE')
    for k in ['cruiseSpeed','hoverSpeed']:require(number(m.get(k)) and 0<=m[k]<=100,'SPEED_TYPE_RANGE')
    require(isinstance(m.get('items'),list) and 1<=len(m['items'])<=2000,'ITEM_LIMIT')
    unsupported=[];executable=[];design=[];labels=[]
    def extras(obj,allowed,path):
        require(isinstance(obj,dict),'OBJECT:'+path)
        unsupported.extend(path+'.'+k for k in obj.keys()-allowed)
    extras(p,ROOT_KEYS,'plan');extras(m,MISSION_KEYS,'mission')
    for key,allowed in [('geoFence',{'version','circles','polygons','polygon','breachReturn'}),('rallyPoints',{'version','points'})]:
        value=p.get(key)
        require(isinstance(value,dict) and value.get('version') in [1,2],'NAMESPACE_SCHEMA:'+key)
        extras(value,allowed,key)
        if any(value.get(k) for k in allowed-{'version'}):unsupported.append(key+'.NONEMPTY_CONTENT_NOT_INTERPRETED')
    def simple(i,path):
        extras(i,SIMPLE_KEYS,path)
        require(i.get('type')=='SimpleItem' and integer(i.get('command')) and 0<=i['command']<=65535,'COMMAND')
        require(integer(i.get('frame')) and 0<=i['frame']<=255 and type(i.get('autoContinue')) is bool,'FRAME_FLAGS')
        require(integer(i.get('doJumpId')) and i['doJumpId']>=1,'LABEL_ID')
        params=i.get('params')
        require(isinstance(params,list),'PARAMS')
        if len(params)==4 and 'coordinate' in i:
            coord(i['coordinate']);params=params+i['coordinate']
        else:require(len(params)==7 and 'coordinate' not in i,'PARAM_COUNT_OR_AMBIGUOUS_COORD')
        require(all(x is None or number(x) for x in params),'PARAM_TYPE')
        cmd=i['command']
        if cmd in CAMERA:require(i['frame'] in [0,2],'CAMERA_FRAME_UNSUPPORTED')
        def ident(index):require(number(params[index]) and params[index]==int(params[index]) and 0<=params[index]<=255,'CAMERA_ID_OR_STREAM_TYPE')
        if cmd==206:
            require(number(params[0]) and params[0]>=0 and number(params[1]) and params[1]>=-1,'TRIGGER_DISTANCE_OR_SHUTTER')
            require(params[2] in [0,1] and type(params[2]) is not bool,'TRIGGER_IMMEDIATE');ident(3)
        elif cmd==2000:
            ident(0)
            require(number(params[1]) and params[1]>=0 and number(params[2]) and params[2]>=0 and params[2]==int(params[2]),'CAPTURE_INTERVAL_COUNT')
            require(number(params[3]) and params[3]==int(params[3]) and (params[3]>=1 if params[2]==1 else params[3]==0),'CAPTURE_SEQUENCE')
        elif cmd==2001:ident(0)
        elif cmd==2500:
            ident(0);ident(2);require(number(params[1]) and params[1]>=0,'VIDEO_STATUS_RATE')
        elif cmd==2501:ident(0);ident(1)
        if i['command'] not in SUPPORTED:unsupported.append(path+'.command:'+str(i['command']))
        if i['command'] in NAV:
            coord(params[4:7])
            require(i['frame'] in [0,3,5,6,10,11],'NAV_FRAME_UNSUPPORTED')
            mode=i.get('AltitudeMode')
            if mode is not None:
                require(integer(mode) and mode in [1,2,3,4],'ALTITUDE_MODE')
                require(i['frame'] in {1:[3,6],2:[0,5],3:[0,5],4:[10,11]}[mode],'ALTITUDE_MODE_FRAME_CONFLICT')
                require(number(i.get('Altitude')),'ALTITUDE_VALUE')
                if mode==3:
                    require(number(i.get('AMSLAltAboveTerrain')) and abs(i['AMSLAltAboveTerrain']-params[6])<1e-7,'TERRAIN_BAKED_ALTITUDE_MISSING')
                else:require(abs(i['Altitude']-params[6])<1e-7,'ALTITUDE_DISPLAY_WIRE_CONFLICT')
        # Nulls are legal reserved/unspecified values. No blanket null→zero coercion.
        normalized={k:v for k,v in i.items() if k not in ['params','coordinate']};normalized['params']=params
        executable.append(normalized);labels.append(i['doJumpId'])
    for index,i in enumerate(m['items']):
        path=f'mission.items[{index}]'
        require(isinstance(i,dict),'ITEM_OBJECT')
        if i.get('type')=='SimpleItem':simple(i,path);design.append({'type':'SimpleItem','slot':len(executable)-1})
        elif i.get('type')=='ComplexItem' and i.get('complexItemType')=='survey' and i.get('version') in [4,5]:
            extras(i,SURVEY_KEYS,path)
            require(isinstance(i.get('polygon'),list) and 3<=len(i['polygon'])<=256,'POLYGON')
            for point in i['polygon']:coord(point,2)
            t=i.get('TransectStyleComplexItem');extras(t,TRANSECT_KEYS,path+'.TransectStyleComplexItem')
            require(t.get('version') in [1,2] and isinstance(t.get('Items'),list) and len(t['Items'])>0,'CACHED_ITEMS_REQUIRED_NOT_REGENERATION')
            extras(t.get('CameraCalc'),CAMERA_KEYS,path+'.CameraCalc')
            d={k:v for k,v in i.items() if k!='TransectStyleComplexItem'}
            d['TransectStyleComplexItem']={k:v for k,v in t.items() if k!='Items'}
            design.append(d)
            for n,item in enumerate(t['Items']):simple(item,path+f'.cache[{n}]')
        else:raise ContractError('COMPLEX_TYPE_OR_VERSION_UNSUPPORTED')
        require(len(executable)<=2000,'EXPANDED_ITEM_LIMIT')
    if len(set(labels))!=len(labels):unsupported.append('duplicate-doJumpId-labels')
    if any(i['command']==177 for i in executable):unsupported.append('DO_JUMP_NEEDS_CONTROL_FLOW_ORACLE')
    header={k:v for k,v in p.items() if k not in ['groundStation','mission']}
    header['mission']={k:v for k,v in m.items() if k!='items'}
    return {'rawSha256':hashlib.sha256(raw.encode()).hexdigest(),'plan':p,'header':header,'design':design,
            'executable':executable,'uninterpreted':sorted(set(unsupported)),
            'cacheRegeneration':'NOT_CHECKED' if any(i.get('type')=='ComplexItem' for i in m['items']) else 'NOT_APPLICABLE'}

MISSING=object()
def diff(a,b,path='',out=None):
    if out is None:out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(a.keys()|b.keys()):diff(a.get(k,MISSING),b.get(k,MISSING),path+'.'+k,out)
    elif isinstance(a,list) and isinstance(b,list):
        for n in range(max(len(a),len(b))):diff(a[n] if n<len(a) else MISSING,b[n] if n<len(b) else MISSING,path+f'[{n}]',out)
    elif a is MISSING or b is MISSING or type(a) is bool or type(b) is bool or not (number(a) and number(b)):
        if type(a) is not type(b) or a!=b:out.append({'path':path,'before':{'missing':True} if a is MISSING else a,'after':{'missing':True} if b is MISSING else b})
    elif a!=b:out.append({'path':path,'before':a,'after':b})
    return out

def compare_plans(before_raw,after_raw):
    a=load_plan(before_raw);b=load_plan(after_raw)
    differences={k:diff(a[k],b[k],k) for k in ['header','design','executable']}
    n=sum(len(x) for x in differences.values())
    return {'format':'mission55-semantic-diff','version':1,'verdict':'DIFFERENT' if n else 'REVIEW_REQUIRED' if a['uninterpreted'] or b['uninterpreted'] else 'EQUAL_DECLARED_SCOPE',
            'differenceCount':n,'differences':differences,'beforeSha256':a['rawSha256'],'afterSha256':b['rawSha256'],
            'uninterpreted':{'before':a['uninterpreted'],'after':b['uninterpreted']},'cacheRegeneration':a['cacheRegeneration'],
            'ignoredCosmeticFields':['groundStation','JSON key order/whitespace'],'flightReady':False,
            'scope':'Stored Plan semantics only; no Survey regeneration, flight approval or RAGAS runtime proof'}

def f32(x):
    require(number(x),'FLOAT_VALUE')
    try:return struct.unpack('<f',struct.pack('<f',x))[0]
    except (OverflowError,struct.error) as e:raise ContractError('FLOAT32_OVERFLOW') from e
def int_coord(x):return math.floor(x*1e7+0.5)

def compare_readback(raw,items,context):
    """Retained AP4.7.1 snapshot inventory only; direction-aware recipient checks."""
    p=load_plan(raw)
    require(not p['uninterpreted'],'UNINTERPRETED_PLAN')
    require(context.get('profile')=='copter4.7.1-qgc03-retained-v1','PROFILE_NOT_PINNED')
    require(context.get('source')==[1,1] and context.get('receiver')==[255,190],'ENVELOPE_ROUTE')
    require(context.get('session')==context.get('expectedSession') and context.get('boot')==context.get('expectedBoot'),'SESSION_BOOT')
    require(context.get('maxAgeMs',10000)==10000,'UNPINNED_FRESHNESS_POLICY')
    require(number(context.get('ageMs')) and 0<=context['ageMs']<=10000,'STALE_CONTEXT')
    require(isinstance(items,list) and len(items)==len(p['executable'])+1,'READBACK_COUNT')
    fields={'seq','command','frame','current','autocontinue','mission_type','target_system','target_component','param1','param2','param3','param4','x','y','z'}
    require(all(isinstance(i,dict) and set(i)==fields for i in items),'READBACK_FIELD_SCHEMA')
    observed_home=context.get('observedHome');coord(observed_home)
    errors=[];normalizations=[]
    def exact(path,a,b):
        if type(a) is not type(b) and not(number(a) and number(b)) or a!=b:errors.append({'path':path,'expected':a,'observed':b})
    def numeric(path,expected,observed):
        if not number(observed) or abs(observed-f32(expected))>max(1e-6,abs(f32(expected))*1e-7):
            errors.append({'path':path,'expectedFloat32':f32(expected),'observed':observed if number(observed) else str(observed)})
    # Home slot is compared against declared observed AP Home; planned Home remains separately visible.
    expected_home={'seq':0,'command':16,'frame':0,'mission_type':0,'current':0,'autocontinue':1,'target_system':255,'target_component':190,
                   'x':int_coord(observed_home[0]),'y':int_coord(observed_home[1])}
    for k,v in expected_home.items():exact('home.'+k,v,items[0].get(k))
    numeric('home.z',observed_home[2],items[0].get('z'))
    for k in ['param1','param2','param3','param4']:numeric('home.'+k,0,items[0].get(k))
    for n,(i,r) in enumerate(zip(p['executable'],items[1:]),1):
        require(i['command'] in {16,20,22,178,206,2001},'UNPROVEN_READBACK_COMMAND')
        params=list(i['params']);frame=i['frame']
        if i['command'] in {20,178,206,2001} and frame==2:
            frame=0;normalizations.append({'seq':n,'rule':'AP4.7.1-retained-DO-frame2-to0','field':'frame'})
        for k,v in {'seq':n,'command':i['command'],'frame':frame,'current':0,'autocontinue':int(i['autoContinue']),
                    'mission_type':0,'target_system':255,'target_component':190}.items():exact(f'{n}.'+k,v,r.get(k))
        for j,value in enumerate(params):
            if value is None:
                if i['command'] in NAV and j==3 or i['command']==2001 and j>=1:
                    params[j]=0;normalizations.append({'seq':n,'field':f'params[{j}]','rule':'AP4.7.1-retained-reserved-null-to0'})
                else:raise ContractError('NULL_NO_CANONICALIZATION_RULE')
        for j,k in enumerate(['param1','param2','param3','param4']):numeric(f'{n}.'+k,params[j],r.get(k))
        if i['command'] in NAV:
            for j,k in [(4,'x'),(5,'y')]:exact(f'{n}.'+k,int_coord(params[j]),r.get(k))
        else:
            for j,k in [(4,'x'),(5,'y')]:exact(f'{n}.'+k,params[j],r.get(k))
        numeric(f'{n}.z',params[6],r.get('z'))
    home_diff=diff(p['header']['mission']['plannedHomePosition'],observed_home,'planned-vs-observed-home')
    return {'verdict':'DIFFERENT' if errors else 'MATCH_RETAINED_READBACK_SCOPE','errors':errors,'normalizations':normalizations,
            'plannedVsObservedHome':home_diff,'sourcePlanSha256':p['rawSha256'],'flightReady':False,
            'scope':'Replay inventory, not a new upload/flight/camera execution; wire target is receiver GCS, not camera ID'}

def capture_evidence(events,identity):
    """Offline evidence reducer: ACK cannot create reported captures or verified files."""
    require(isinstance(events,list) and len(events)<=10000,'EVENT_LIMIT')
    require(all(isinstance(identity.get(k),str) and identity[k] for k in ['aircraft','session','clockId'])
            and integer(identity.get('boot')) and integer(identity.get('camera')) and 0<=identity['camera']<=255
            and number(identity.get('maxAgeMs')) and 0<identity['maxAgeMs']<=10000,'EVIDENCE_IDENTITY_OR_CLOCK')
    reported=set();files=set();ignored=[];acked=0
    for event in events:
        require(isinstance(event,dict),'EVENT_OBJECT')
        if any(event.get(k)!=identity[k] for k in ['aircraft','camera','session','boot']):ignored.append('FOREIGN_IDENTITY');continue
        if event.get('clockId')!=identity.get('clockId') or not number(event.get('ageMs')) or not 0<=event['ageMs']<=identity.get('maxAgeMs',10000):
            ignored.append('STALE_OR_UNKNOWN_CLOCK');continue
        if event.get('kind')=='ACK':acked+=1
        elif event.get('kind')=='CAPTURE_REPORTED':
            require(integer(event.get('index')) and event['index']>=0,'CAPTURE_INDEX')
            reported.add((event['camera'],event['index']))
        elif event.get('kind')=='FILE_VERIFIED':
            # Mock fixture declarations never become verified media. No media verifier supplied here.
            ignored.append('NO_PHYSICAL_FILE_VERIFIER')
        else:ignored.append('UNSUPPORTED_EVENT')
    return {'acknowledged':acked,'reportedUnique':len(reported),'verifiedPhysicalFiles':len(files),'ignored':ignored,
            'scope':'MOCK_REPLAY_ONLY','flightReady':False}
