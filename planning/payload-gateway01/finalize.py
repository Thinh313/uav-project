"""Scoped preservation, persisted journal and evidence checks. No service/flight commands."""
from pathlib import Path
import datetime,hashlib,json,re,shutil,subprocess
R=Path(__file__).resolve().parents[2];E=R/'evidence/payload-gateway01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
out=E/'final-verification01.json'
if out.exists():raise ValueError('NEW_RECEIPT_REQUIRED')
assert shutil.disk_usage(R).free>=20*2**30,'DISK_FLOOR'
baseline=read(E/'preservation-before01.json');pin_results=[]
for rel,expected in baseline['files'].items():
 p=R/rel;actual=sha(p)if p.is_file()else None
 assert actual==expected,rel
 pin_results.append({'path':rel,'sha256':actual,'unchanged':True})
core=read(E/'mock04/results.json');http=read(E/'http01.json')
assert core['passed']==22 and not core['failed'];assert http['passed']==6 and not http['failed']
for p in [E/'receiver01.json',E/'receiver02-ir.json',E/'receiver03-final-rgb.json']:
 j=read(p);assert j['result']['status']=='ACCEPTED_SYNTHETIC_INTEGRITY_AND_MATH_ONLY';assert len(j['negativeControls'])==4
 export=Path(j['archive']);assert sha(export)==j['archiveSha256'];dest=E/export.name
 if dest.exists():raise ValueError('EXPORT_COPY_EXISTS')
 shutil.copyfile(export,dest);assert sha(dest)==j['archiveSha256']
narrow=read(E/'browser04/narrow-layout-final.json');wide=read(E/'browser04/wide-layout-final.json')
for layout,pane in [(narrow,'panel'),(wide,'review')]:
 assert layout[pane]['y']>=layout['strip']['bottom']+8
 assert layout[pane]['bottom']<=layout['status']['y']-8
assert narrow['shutterDisabled'];assert wide['theme']=='day'and wide['themeIcon']=='#i-sun'
rows=[];head='0'*64
for line in (E/'browser02/workspace/journal.jsonl').read_text().splitlines():
 row=json.loads(line);base={k:v for k,v in row.items()if k!='digest'}
 assert base['seq']==len(rows)+1 and base['prev']==head
 computed=hashlib.sha256(json.dumps(base,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 assert computed==row['digest'];head=computed;rows.append(row)
heads={r['digest']for r in rows};closures=[]
for run in ['browser02','browser03','browser04']:
 launch=read(E/run/'launch.json');closure=read(E/run/'closure.json')
 assert closure['journalHead']in heads and closure['reason']=='EXPLICIT_STOP'and not closure['journalReadOnly']
 process=subprocess.run(['ps','-p',str(launch['pid']),'-o','command='],capture_output=True,text=True)
 assert '/payload/gateway01/server.mjs'not in process.stdout,'OWNED_PROCESS_ALIVE'
 closures.append({'run':run,'pid':launch['pid'],'reason':closure['reason'],'journalHead':closure['journalHead']})
assert read(E/'browser04/closure.json')['journalHead']==head
assert not (E/'browser02/workspace/.writer.lock').exists()
assert not (R/'.local/payload-gateway01/stage').exists()
listener=subprocess.run(['lsof','-nP','-iTCP:8866','-sTCP:LISTEN'],capture_output=True,text=True)
assert listener.returncode==1 and not listener.stdout,'PORT_STILL_LISTENING'
committed=[r for r in rows if r['kind']=='CAPTURE_COMMITTED'];assert len(committed)==4
launches=[r for r in rows if r['kind']=='HOST_SESSION_STARTED'];assert len(launches)==3 and all(r['data']['authorityRestored']is False for r in launches)
sources={str(p.relative_to(R)):sha(p)for folder in ['payload/gateway01','planning/payload-gateway01']for p in sorted((R/folder).rglob('*'))if p.is_file()and '__pycache__'not in p.parts}
source_id=hashlib.sha256(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()).hexdigest()
source_ready={'sourceId':source_id,'format':'MOCK_HOST_ENGINEERING_HASH_NOT_SOFTWARE_SIGNATURE','files':sources,'reusedPins':baseline['files']}
(E/'source-ready01.json').write_text(json.dumps(source_ready,indent=2)+'\n')
doc=R/'delivery/COMPLETION-PAYLOAD-GATEWAY01.md'
for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
 if '://'not in link:assert (doc.parent/link).resolve().is_file()or(doc.parent/link).resolve()==out,link
bytes_total=sum(p.stat().st_size for p in E.rglob('*')if p.is_file());assert bytes_total<16*2**20
receipt={'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'READY_SCOPED_HOST_MOCK_NOT_READY_REAL_PAYLOAD','sourceId':source_id,
 'requirements':{'implementedHostMock':7,'hostMockTotal':7,'hardwareAndroidProduction':'NOT_CHECKED_NOT_IMPLEMENTED_REAL_DRIVERS'},
 'coreCorpus':{'passedGroups':22,'failedGroups':0,'evidence':'mock04/results.json','authorship':'SELF_AUTHORED_NOT_INDEPENDENT_REVIEW'},
 'http':{'passedGroups':6,'failedGroups':0,'evidence':'http01.json'},
 'receiver':{'browserDownloadedPackagesAccepted':3,'differentNegativeCategories':4,'implementationIndependent':True,'humanIndependentReview':False},
 'browserObservations':{'provenance':'ROOT_OBSERVED_CUA_UI_ACTIONS_AND_READ_ONLY_DOM','rgbAndIrCapture':True,'gimbalAndIsoReadbackMock':True,'noEventDidNotCreateImage':True,'restartRetainedPriorPackageId':True,'reloadNoAuthorityRestored':True,'clearedReadbackOnSelection':True,'sourceFinalTooltipDelta':'Targeted reload checked day/#i-sun/title then restored night;4 review entries,no rights','viewports':[[1280,800],[900,500]],'viewportReset':True,'ownedTabClosed':True,'perFrameAgeNotCameraLatency':True},
 'durability':{'journalRows':len(rows),'head':head,'committedSyntheticCaptures':4,'hostSessions':3,'closures':closures,'partialUncommittedEvidenceRetained':True},
 'preservation':{'checkedPaths':len(pin_results),'changedOrMissing':[],'results':pin_results,'scope':'Selected PHONE06/BIG02/APK/internal/ENDURE identity pins only, not all historical paths or 24h acceptance'},
 'priorFailuresRetained':['mock01 fixture/client envelope SCHEMA; fixed caller without loosening gate','browser01 sandbox listen EPERM; no UI journey','individual JSON download timeout, full TAR path subsequently passed'],
 'remaining':['Physical Sony/Pixy/PhaseOne drivers and SDK','Android/HeraHub integration','Real GNSS/exposure synchronization and radiometry','Onboard deployment, RF/multi-viewer/performance/field/production','Operator time advantage versus prior workflow unmeasured'],
 'cleanup':{'removed':['.local/payload-gateway01/stage (curated 4.6MiB stage after each run)'],'ownedPortClosed':8866,'outsideRepoScratch':False,'dependenciesInstalled':False,'dockerUsed':False,'browserDownloadsRetainedAsExports':True},
 'resources':{'newEvidenceBytes':bytes_total,'freeBytes':shutil.disk_usage(R).free,'floorBytes':20*2**30},
 'reportSha256':sha(doc),'evidenceSha256':{str(p.relative_to(R)):sha(p)for p in sorted(E.rglob('*'))if p.is_file()}}
assert receipt['resources']['freeBytes']>=20*2**30
with out.open('x')as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:receipt[k]for k in ['status','sourceId','requirements','resources']},ensure_ascii=False))
print('Pins',len(pin_results),'journal rows',len(rows),'exports3, stage removed, port8866 closed')
