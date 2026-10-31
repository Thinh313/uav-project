"""QA-authored corpus generator. No production import, socket, build or runtime."""
from pathlib import Path
import sys,json,hashlib,math,random,copy
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'pilot/mission55/vendor'))
from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea
OUT=ROOT/'evidence/integration03-qa/heldout-corpus01.json'
R=random.Random(0xA3E120261020)
sha=lambda b:hashlib.sha256(b).hexdigest()
home={'lat':10.854,'lon':106.807,'amslM':10}
def point(x,y):
 p=Geodesic.WGS84.Direct(home['lat'],home['lon'],math.degrees(math.atan2(x,y)),math.hypot(x,y))
 return [p['lon2'],p['lat2'],0]
def kml(kind,coords,name):
 seq=' '.join(','.join(format(n,'.15g') for n in p) for p in coords)
 shape='<Polygon><outerBoundaryIs><LinearRing><coordinates>'+seq+'</coordinates></LinearRing></outerBoundaryIs></Polygon>' if kind=='polygon' else '<LineString><coordinates>'+seq+'</coordinates></LineString>'
 return '<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>'+name+'</name>'+shape+'</Placemark></Document></kml>'
def numeric(c,metrics,tolerances=None):
 return {'id':c,'kind':'numeric','metrics':metrics,'absoluteTolerances':tolerances or {k:1e-9 for k in metrics}}
def check(c,required):return {'id':c,'kind':'fields','required':required}
angle=math.radians(R.uniform(11,29));cx,cy=11.2,8.3;w,h=R.uniform(8,11),R.uniform(5,7)
xy=[[cx+u*math.cos(angle)-v*math.sin(angle),cy+u*math.sin(angle)+v*math.cos(angle)] for u,v in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
poly=[point(*p) for p in xy];poly.append(poly[0]);rawpoly=kml('polygon',poly,'QA polygon alpha')
pa=PolygonArea(Geodesic.WGS84,False)
for lon,lat,z in poly[:-1]:pa.AddPoint(lat,lon)
_,perim,area=pa.Compute(False,True)
line=[point(*p) for p in [[5.7,5.2],[13.4,6.7],[18.3,12.1]]];rawline=kml('corridor',line,'QA corridor beta')
length=sum(Geodesic.WGS84.Inverse(a[1],a[0],b[1],b[0])['s12'] for a,b in zip(line,line[1:]))
alt=R.randint(12,18);speed=R.choice([1.2,1.4,1.6]);fo=R.choice([81,83,86]);so=R.choice([73,77,79]);fpw=alt*36/35;fph=alt*24/35
optics={'footprintAcrossM':fpw,'footprintAlongM':fph,'gsdMPerPixel':fpw/6000,'triggerSpacingM':fph*(1-fo/100),'lineSpacingM':fpw*(1-so/100),'triggerIntervalS':fph*(1-fo/100)/speed}
def simple(cmd,frame,params,n):return {'type':'SimpleItem','command':cmd,'frame':frame,'autoContinue':True,'doJumpId':n,'params':params}
qitems=[simple(22,3,[0,0,0,None,home['lat'],home['lon'],alt],1),simple(178,2,[1,speed,-1,0,0,0,0],2),simple(16,3,[0,0,0,None,line[0][1],line[0][0],alt],3),simple(206,2,[optics['triggerSpacingM'],0,1,0,0,0,0],4),simple(16,3,[0,0,0,None,line[1][1],line[1][0],alt],5),simple(206,2,[0,0,0,0,0,0,0],6),simple(20,2,[0,0,0,0,0,0,0],7)]
qplan={'fileType':'Plan','version':1,'groundStation':'QA authored, not actual QGC output','geoFence':{'version':2,'circles':[],'polygons':[]},'rallyPoints':{'version':2,'points':[]},'mission':{'version':2,'firmwareType':3,'vehicleType':2,'cruiseSpeed':speed,'hoverSpeed':2,'globalPlanAltitudeMode':1,'plannedHomePosition':[home['lat'],home['lon'],10],'items':qitems}}
qraw=json.dumps(qplan,ensure_ascii=False,indent=2)+'\n'
qvariants={}
for name in ['placeholder','home-change','terrain','unknown-extension','fence','rally','complex']:
 p=copy.deepcopy(qplan)
 if name=='placeholder':p['mission']['items'][3]=simple(0,2,[0]*7,4)
 if name=='home-change':p['mission']['plannedHomePosition'][2]=7
 if name=='terrain':p['mission']['items'][4]['frame']=10
 if name=='unknown-extension':p['mission']['items'][4]['qaUnknownExecutable']={'mode':'must-not-strip'}
 if name=='fence':p['geoFence']['circles']=[{'inclusion':True,'circle':[home['lat'],home['lon'],17]}]
 if name=='rally':p['rallyPoints']['points']=[[home['lat'],home['lon'],alt]]
 if name=='complex':p['mission']['items'][4]={'type':'ComplexItem','complexItemType':'survey','version':5,'polygon':[[p[1],p[0]] for p in poly[:-1]],'TransectStyleComplexItem':{'version':2,'Items':[qitems[4]],'CameraCalc':{'DistanceMode':1},'FollowTerrain':False,'HoverAndCapture':False,'Refly90Degrees':False}}
 qvariants[name]=json.dumps(p,ensure_ascii=False,indent=2)+'\n'
cohortStart=R.randint(41000,51000);order=list(range(20));R.shuffle(order)
valid=[cohortStart+131*i for i in range(20)]
pose={'northM':R.uniform(7,19),'eastM':R.uniform(-12,-3),'downM':-R.uniform(9,21),'bodyQuaternionNED':[1,0,0,0]}
checks=[numeric('H01.area',{'areaM2':abs(area),'perimeterM':perim},{'areaM2':.03,'perimeterM':.01}),numeric('H01.optics',optics),check('H01.source',{'sourceSha256':sha(rawpoly.encode()),'sourceKind':'KML','operationalWorld':'SYNTHETIC_FLAT','physicalImages':0}),numeric('H02.length',{'centerlineLengthM':length},{'centerlineLengthM':.01}),check('H02.source',{'sourceSha256':sha(rawline.encode()),'sourceKind':'KML','centerlineVertices':3}),check('H03.source',{'sourceSha256':sha(qraw.encode()),'sourceKind':'QGC_SIMPLE_ITEMS','cameraCommandPreserved':True,'nullYawRetainedInOriginal':True,'roundTripSemanticEqual':True,'physicalImages':0}),check('H03.cameraMutation',{'semanticEqual':False,'operationalUploadAllowed':False}),numeric('H03.homeMutation',{'impliedAmslDeltaM':-3},{'impliedAmslDeltaM':0}),check('H03.homeGate',{'operationalUploadAllowed':False}),*[check('H04.'+k,{'operationalUploadAllowed':False,'originalBytesRetained':True}) for k in ['terrain','unknown-extension','fence','rally','complex']],check('H05.valid',{'cohortReady':True,'firstReceiptRestamped':False,'historyRetained':True}),check('H05.overSpan',{'cohortReady':False,'autoWireCount':0}),check('H05.stale',{'cohortReady':False,'autoWireCount':0}),check('H05.wrongType',{'cohortReady':False,'autoWireCount':0}),numeric('H06.pose',{'threeEastM':pose['eastM'],'threeUpM':-pose['downM'],'threeSouthM':-pose['northM']},{'threeEastM':1e-6,'threeUpM':1e-6,'threeSouthM':1e-6}),check('H06.expiry',{'knownAtAge999':True,'staleAtAge1001':True,'pausedAtAge2001':True,'wrongRunRejected':True,'futureClockRejected':True,'wireWrites':0}),check('H07.crew',{'oldOwnerPostWalWrites':0,'lateAckCompletesNewIntent':False,'newOwnerInheritedPending':False,'newSessionGrants':0,'cameraGimbalScopesIndependent':True}),check('H08.export',{'wrongRunAccepted':False,'wrongReceiverAccepted':False,'corruptRawAccepted':False,'restartRestoredAuthority':False,'restartAutoReconnects':0})]
d={'format':'aeris-integration03-qa-heldout','version':1,'provenance':'QA_AUTHORED_PRECOMMITTED_UNSEEN_TO_BUILDER','seed':0xA3E120261020,'TIP_SHA256':sha((ROOT/'planning/integration03/TIP.md').read_bytes()),'groups':8,'inputs':{'home':home,'polygonKml':rawpoly,'corridorKml':rawline,'options':{'altitudeAglM':alt,'speedMS':speed,'frontOverlapPct':fo,'sideOverlapPct':so,'headingDeg':math.degrees(angle),'corridorWidthM':R.randint(6,10),'datumAcknowledged':True},'camera':{'sensorWidthMm':36,'sensorHeightMm':24,'focalLengthMm':35,'imageWidthPx':6000,'imageHeightPx':4000,'provenance':'SYNTHETIC_FIXTURE'},'qgcRaw':qraw,'qgcVariants':qvariants,'cohort':{'startMs':cohortStart,'validReceiptMs':valid,'arrivalPermutation':order,'overSpanReceiptMs':[cohortStart+167*i for i in range(20)],'staleDecisionMs':valid[-1]+10001,'wrongTypeIndex':R.randint(4,16),'agedHistoryRows':R.randint(9000,12000),'noTimeRestamp':True},'observer':{'run':'qa-i03-run-'+str(R.randrange(10**7,10**8)),'poseNED':pose,'sourceAgesMs':[999,1001,2001],'mountMapping':'Three=(East,-Down,-North); model fixed mounting transform must be disclosed separately'},'crew':{'frontZoomPct':[R.randint(24,39),R.randint(71,89)],'frontFocusPct':[R.randint(21,37),R.randint(56,73)],'gimbalAnglesDeg':[-R.randint(31,67),R.randint(43,87)],'leaseRevokeNativeAgesMs':[3000,3250],'receiver':'rtr-evaluator','nonce':'i03qa_'+str(R.randrange(10**9,10**10))}},'checks':checks,'oracle':{'method':'GeographicLib.WGS84 Direct/Inverse/PolygonArea via pinned mission55 vendor; independent analytical rectilinear optics; exact semantic and safety contracts','geometryQualification':'Small AOI planar-vs-ellipsoid approximation explicitly tolerated; no terrain/surface/field coverage claim','expectedBeforeProductionFreeze':True},'actualOnlyObligations':['3 declared aged cohorts including owned host load','Actual Android polygon/corridor accepted review with B','Same consent B capture + exact Adevice1/Bdevice2 wire','Current B partition and pilot-loss observer','Foreground30s actual browser quality metrics and stale interaction','Selected-run SAF/provider readback + process/coldboot/old private'],'outOfScope':['Manual training','External physics1x','Hera/load/battery/acoustic calibration','Collision/sensor-loss safety','Physical PhaseOne/HeraHub','Production signing/commercial comparison']}
assert not OUT.exists(),OUT
OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print(sha(OUT.read_bytes()))
