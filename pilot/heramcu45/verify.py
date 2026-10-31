from pathlib import Path
from datetime import datetime,timezone
import importlib.util,json,subprocess,hashlib,os
from zipfile import ZipFile
import xml.etree.ElementTree as X
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;E=R/'evidence/heramcu45'
s=importlib.util.spec_from_file_location('g40',R/'pilot/apstream40/guard.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
FLOOR=20*2**30;BUDGET=16*2**20;checks=[]
def check(name,v):
 assert v,name
 checks.append({'name':name,'pass':True})
def read(n):return json.loads((E/n).read_text())
def allocated():return sum(p.stat().st_blocks*512 for d in [H,E] for p in d.rglob('*') if p.is_file())
check('floor20GiB beforeverification',g.free()>FLOOR+2**20)
b=read('preservation-before1.json');bad=g.bad(b['files']);same=g.endure()==b['endureGuardPaths']
check('protected14074 exact',len(b['files'])==14074 and not bad)
check('ENDURE5051 same inventory and protectedbytes',len(g.endure())==5051 and same)
manifest=read('source-manifest.json');originals=[]
for x in manifest['sources']:
 p=R/x['capturedPath'];check('captured sourceSHA '+x['id'],g.sha(p)==x['sha256'])
 q=Path(x['originalPath']);originals.append({'path':str(q),'exists':q.is_file(),'matchesSHA':g.sha(q)==x['sha256'] if q.is_file() else None})
blocks=read('sources/mcu-legacy.docx.blocks.json');c=json.loads((H/'contract.json').read_text())
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with ZipFile(E/'sources/mcu-legacy.docx') as z:
 body=X.fromstring(z.read('word/document.xml')).find('w:body',ns);rebuilt=[]
 for i,node in enumerate(body):rebuilt.append({'block':i,'kind':'table' if node.tag.endswith('}tbl') else 'paragraph','text':' | '.join(''.join(t.text or '' for t in q.findall('.//w:t',ns)) for q in node.findall('.//w:p',ns)) if node.tag.endswith('}tbl') else ''.join(t.text or '' for t in node.findall('.//w:t',ns))})
 check('source blocks reconstructed exact from capturedDOCX',blocks==rebuilt)
 check('original XML and relationships exact',all((E/'sources'/out).read_bytes()==z.read(src) for out,src in [('mcu-document.xml','word/document.xml'),('mcu-document-rels.xml','word/_rels/document.xml.rels')]))
 images=[n for n in z.namelist() if n.startswith('word/media/')]
 check('all6 diagram bytes exact',len(images)==6 and all((E/'sources/mcu-diagrams'/Path(n).name).read_bytes()==z.read(n) for n in images))
 rels={x.attrib['Id']:x.attrib['Target'] for x in X.fromstring(z.read('word/_rels/document.xml.rels'))}
 diagramBlocks={i for i,node in enumerate(body) if any(rels.get(b.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed'),'').startswith('media/') for b in node.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'))}
check('contract revision45.2 source hash and16unresolved',c['revision']=='45.2' and c['source']['sha256']==manifest['sources'][0]['sha256'] and len(c['unknowns'])==16 and all(x['status']=='UNRESOLVED' and x['requiredEvidence'] for x in c['unknowns']))
for claim in c['claims']:check('claim locators '+claim['id'],claim['status']=='DOCUMENT_CLAIM' and all(blocks[n]['text'] or n in diagramBlocks for n in claim['sourceBlocks']))
check('16message headings/field literal sourceexact',len(c['messageCatalog'])==16 and all(x['documentHeading']==blocks[x['sourceBlock']]['text'] and all(f['literal']==blocks[f['block']]['text'] for f in x['fields']) and x['wireId'] is None and x['crcExtra'] is None for x in c['messageCatalog']))
check('21enum rawentries no inferred values',len(c['documentEnums'])==21 and all(x['nameLiteral']==blocks[x['sourceBlock']]['text'] and all(v['literal']==blocks[v['sourceBlock']]['text'] and v['inferredNumericValue'] is None for v in x['entries']) for x in c['documentEnums']))
check('wireunknown codecblocked and applicabilityunconfirmed',c['wire']['codecPermitted'] is False and c['wire']['mavlinkVersion'] is None and all(v is None for v in c['wire']['commandIds'].values()) and c['hardwareObserved'] is False and 'UNCONFIRMED' in c['applicability'])
check('RF_RC association proposed notobserved',c['mockPolicy']['rfRoutes']['status']=='PROPOSED_MOCK_TOPOLOGY_NOT_OBSERVED')
check('priorfailures retained notrelabeled',read('mock1.json')['passed']==75 and read('mock1.json')['status']=='FAIL' and read('qa1.json')['status']=='FAIL')
check('finalcorpus76pass',read('mock5.json')['total']==76 and read('mock5.json')['passed']==76 and read('mock5.json')['status']=='PASS')
q=read('qa4.json');check('50additionalchecks pass oncorpus5',q['checks']==50 and q['passed']==50 and q['status']=='PASS' and q['corpus']=='corpus5.json')
reboot=read('mock-reboot-readback4.json');check('mockpairedreboot equality and freshhandshake flags',reboot['comparison']['equal'] and reboot['comparison']['expectedConfigSha256']==reboot['comparison']['currentConfigSha256'] and reboot['fresh']['summary']['savedReadbackMock'] is False and reboot['fresh']['authorityRestorable'] is False)
cold=read('cold-regression1.json');check('protected43cold38+4+3sessions',len(cold['corpus43'])==38 and all(x['pass'] for x in cold['corpus43']) and len(cold['lifecycle43'])==4 and len(cold['raw43']['sessions'])==3)
check('protected42coldactual13',cold['raw42']['checkCount']==13)
text=(E/'native-regression1.txt').read_text();check('native33_35 115tests0fail',all(x in text for x in ['ℹ tests 115\n','ℹ pass 115\n','ℹ fail 0\n']))
syntax=[]
for p in sorted(H.glob('*.mjs')):
 v=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);check('syntax '+p.name,v.returncode==0);syntax.append(str(p.relative_to(R)))
sourcefiles={str(p.relative_to(R)):g.sha(p) for p in sorted(H.rglob('*')) if p.is_file()}
check('no runtime/scratch namespace created',not (R/'.local/heramcu45').exists())
check('namespace16MiB and final20GiB floor',allocated()+65536<BUDGET and g.free()>FLOOR+2**20)
out={'at':datetime.now(timezone.utc).isoformat(),'status':'PASS_SCOPED_LOGICAL_MOCK_REPLAY','checks':len(checks),'results':checks,'requirementCoverage':{'total':8,'implementedInAuthorizedMockScope':8,'passed':8,'ratio':1,'ids':['R45-0'+str(i) for i in range(1,9)],'notProductReadinessPercentage':True},'preservation':{'protectedCount':len(b['files']),'failures':bad,'endureUnchanged':same,'endureCount':len(g.endure())},'originalSourcePaths':originals,'capturedSourcesExact':True,'sourceFingerprints':sourcefiles,'syntaxFiles':len(syntax),'resources':{'freeBytes':g.free(),'allocatedBytes':allocated(),'floorBytes':FLOOR,'budgetBytes':BUDGET},'limits':{'actualUSB':'NOT_CHECKED','wireMAVLinkCodec':'BLOCKED_UNKNOWN','HeraHubSDKDevice':'NOT_CHECKED','physicalCalibration':'NOT_CHECKED','AndroidRuntime':'NOT_CHECKED','newAPK':False,'newSoftwareSignature':False,'newSITL':False,'ENDURE24hAcceptance':'NOT_ACHIEVED_BY_THIS_TASK','independentReview':False},'cleanup':{'scratchCreated':False,'runtimeStarted':False,'dependencyInstalled':False,'deletedUserData':False}}
n=1
while (E/f'verification{n}.json').exists():n+=1
with (E/f'verification{n}.json').open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'syntaxFiles':len(syntax),'freeGiB':g.free()/2**30,'allocatedBytes':allocated(),'protectedFailures':len(bad)}))
