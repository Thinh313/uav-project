from pathlib import Path
import json,hashlib,zipfile,datetime,shutil,os
R=Path(__file__).resolve().parents[2];E=R/'evidence/native86';N=R/'native/native86'
checks=[]
def ck(name,ok):
 assert ok,name
 checks.append({'name':name,'pass':True})
rows=[json.loads(x)for x in(E/'android86-ui-final.jsonl').read_text().splitlines()];instance=rows[-1]['nativeInstance'];ui=[r['renderer']for r in rows if r['nativeInstance']==instance];matrix=json.loads((E/'android-ui-matrix01.json').read_text());ck('28 selected Android states captured',len(matrix['steps'])==28)
for theme in['night','day']:
 for view in['plan','preflight','fly','review']:ck(theme+' '+view+' observed',any(r['theme']==theme and r['view']==view for r in ui))
 for title in['Phiên & quyền điều khiển','Phòng kiểm UI','Pin & phương án quay về','Chạm & nút cứng','Camera đang xem','Camera & gimbal']:ck(theme+' popup '+title,any(r['theme']==theme and r['panel']=='#sheet' and r['sheetTitle']==title for r in ui))
 ck(theme+' workspace fallback observed',any(r['theme']==theme and r['panel']=='#panel83' and r['overlay']=='true' for r in ui))
 ck(theme+' glyph matches theme',any(r['theme']==theme and r['themeIcon']==('#i-moon'if theme=='night'else'#i-sun')for r in ui))
 ck(theme+' footer/logo alignment 0CSSpx',all(r['alignmentDelta']in[None,0]for r in ui if r['theme']==theme))
for r in ui:
 for c in r['controls']:
  if c['inPanel']and not c['disabled']:ck('visible enabled active-panel control clear '+r['theme']+' '+c['id'],not c['covered']and not c['textOverflow'])
 a=r['boxes'].get('.navrail');b=r['boxes'].get('.camera-tools')
 if a and b:ck('island Y centres align',abs(a['y']+a['height']/2-b['y']-b['height']/2)<=.5)
ck('actual WebView has no has support',all(not r['supports']['has']for r in ui));ck('blur support observed',all(r['supports']['backdrop']and r['glass']=='blur-supported'for r in ui));ck('1280x800 observed',all(r['viewport']['width']==1280 and r['viewport']['height']==800 for r in ui))
# Current source must be the exact bytes in the installed, signed development03 package.
build=json.loads((E/'build03.json').read_text());apk=R/build['apk'];ck('accepted signed APK SHA',hashlib.file_digest(apk.open('rb'),'sha256').hexdigest()==build['sha256'])
with zipfile.ZipFile(apk)as z:
 for a in json.loads((N/'asset-list.json').read_text()):ck('accepted APK asset byte match '+a,z.read('assets/cockpit'+a)==(N/('assets'+a)).read_bytes())
ck('installed APK matches accepted package',json.loads((E/'installed-apk01.json').read_text())['sha256']==build['sha256'])
ck('ART runtime no app crash log',not(E/'android-runtime-logcat.txt').read_text().strip())
# Old workspaces remain exactly as captured when leaving them; final stop made no extra journal writes.
final=json.loads((E/'android86-final-stopped.json').read_text());post=json.loads((E/'android86-final-before-close.json').read_text());ck('force-stop leaves exact journal bytes',final==post)
for old,receipt in [('workspaces/initial','android86-completed-before-restart.json'),('workspaces/w-fdd17184-a0ae-4ea5-9c4f-3388c5d31d9a','android86-before-fresh-check.json')]:
 before=json.loads((E/receipt).read_text());ck('prior workspace retained '+old,all(final['files'].get(k)==v for k,v in before['files'].items()if k.startswith(old+'/')))
closure=json.loads((E/'android-closure.json').read_text());ck('managed emulator clean closure',closure['exit']==0 and closure['error']is None);ck('20GiB disk floor retained',closure['minFreeBytes']>=20*2**30)
result={'status':'PASS_SELECTED_ANDROID_UI_AND_PACKAGE','at':datetime.datetime.now().astimezone().isoformat(),'checks':checks,'stateScreenshots':28,'distinctSelfReportsThisInstance':len(ui),'environment':rows[-1]['environment'],'visualReview':{'reviewer':'Single agent, build then QA role; no independent-team claim','evidence':['contact-night-1.jpg','contact-night-2.jpg','contact-day-1.jpg','contact-day-2.jpg','android86-review-completed.png','android86-altitude-31-ime.png'],'observed':'Selected scenes/sheets, scroll clips and close controls visually reviewed. Popup contents scroll rather than fit all at once. No global every-pixel or Hera device claim.'},'knownLimitations':['SAF file picker beyond 60 seconds reports unknown; independently reconciled second export. First export/import/provider-readback/activation/restart passed.','System AOSP WebView101 UIAutomator intermittently omits subtrees; current screenshots used, stale XML never used for action.','No frame-rate, GPU benchmark, HeraHub input/video or physical flight qualification.'],'rendererProvenance':'SELF_OBSERVED_NOT_ATTESTATION'}
(E/'verification-ui.json').open('x').write(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'states':28}))
