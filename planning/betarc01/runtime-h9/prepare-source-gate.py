#!/usr/bin/env python3
"""Before HOLD only: discover exact selected readonly inputs, emit closed pins.
Default is inspection only. --write mutates only the two new source assets.
This does not build, sign, freeze, admit or launch any actual runtime actor.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os,stat
P=Path(__file__).resolve();REPO=P.parents[3];SOURCE=P.parent/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(REPO);sys.path[:0]=[str(SOURCE),str(REPO)]
from aeris_runtime.product_inputs import discover,CONTRACT
from aeris_runtime.pipeline_contract import source_pins,sites,owners,health_contract,PINS
from aeris_runtime.metadata_budget import observer_envelope
from aeris_runtime.dependencies import LEAVES
p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--node',required=True);args=p.parse_args()
node=Path(args.node);assert node.is_absolute()and node.is_file()
script="""import{PRODUCT_READ_INPUTS}from'./planning/betarc01/product/server-codec09c.mjs';import{MEDIA_READ_INPUTS}from'./planning/nativejournal17/product/media-server-codec09.mjs';import{ASSETS}from'./planning/betasim-integrated01/scene/assets.mjs';console.log(JSON.stringify([...new Set([...PRODUCT_READ_INPUTS,...MEDIA_READ_INPUTS,...Object.values(ASSETS)])].sort()));"""
r=subprocess.run([str(node),'--input-type=module','-e',script],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True);assert not r.stderr and len(r.stdout)<=65536;reads=json.loads(r.stdout)
entries=['planning/betarc01/runtime/product-companion-rc01.mjs','planning/betarc01/node_alias_h9/verified-loader.mjs','planning/betarc01/runtime/root-owner-rc01.py','planning/betarc01/runtime-h9/root-native-h9.py','planning/betarc01/runtime-h9/root-maintenance-h9.py','planning/betarc01/runtime/root-observe-reboot-rc01.py','planning/betarc01/runtime-h9/root-reconcile-h9.py'];reads+=['planning/betarc01/runtime/scenario-rc01.py','planning/betarc01/runtime/preview-rc01.py','planning/betarc01/diagnostics/package_device01.py','planning/nativejournal17/runtime/scenario-native-only17.py','planning/nativejournal17/receiver17.py','planning/nativejournal17/archive_verifier17.py','planning/nativejournal17/verify-signatures17.mjs'];reads+=[str(q.relative_to(REPO))for q in (REPO/'planning/betarc01/archive').iterdir()if q.is_file()and q.suffix in('.py','.mjs')and not q.name.startswith('test')];reads+=list(json.loads((SOURCE/'aeris_runtime/assets/reconcile-g103-originals.json').read_bytes())['files']);reads+=[str(q.relative_to(REPO))for q in (REPO/'planning/betarc01/tar_profile_h7').iterdir()if q.is_file()and q.suffix in('.py','.mjs')and not q.name.startswith('test')];adoption=json.loads((SOURCE/'aeris_runtime/assets/adoption17-originals.json').read_bytes());reads+=list(adoption['files']);graph=discover(entries,reads)
enc=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def write_generated(path,raw,*,_source_root=SOURCE):
 """Prepare-only atomic COW, limited to this unaccepted source's two assets."""
 root=Path(_source_root).absolute();path=Path(path).absolute();owned=P.parent.resolve()
 assert root.is_relative_to(owned) and root.is_dir() and not any(q.is_symlink()for q in[root,*root.parents]),'H7_GENERATED_ROOT'
 assert path in {root/'aeris_runtime/assets/product-input-closure.json',root/'aeris_runtime/assets/pipeline-writer-pins.json'},'H7_GENERATED_EXACT_TWO_ASSETS'
 assert type(raw)is bytes and 0<len(raw)<=2**20 and path.is_file() and not any(q.is_symlink()for q in[path,*path.parents]),'H7_GENERATED_SOURCE_SHAPE'
 before=path.stat();assert stat.S_ISREG(before.st_mode),'H7_GENERATED_REGULAR'
 pending=path.with_name('.'+path.name+'.pending-h7');assert not pending.exists()and not pending.is_symlink(),'H7_GENERATED_PENDING_EXISTS'
 fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,stat.S_IMODE(before.st_mode))
 try:
  os.fchmod(fd,stat.S_IMODE(before.st_mode));offset=0
  while offset<len(raw):
   n=os.write(fd,raw[offset:]);assert n>0,'H7_GENERATED_WRITE';offset+=n
  os.fsync(fd)
 finally:os.close(fd)
 current=path.stat();assert(current.st_dev,current.st_ino,current.st_mtime_ns,current.st_size)==(before.st_dev,before.st_ino,before.st_mtime_ns,before.st_size),'H7_GENERATED_SOURCE_CHANGED'
 os.replace(pending,path);directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(directory)
 finally:os.close(directory)

if args.write:write_generated(CONTRACT,enc(graph))
pins={'format':'aeris-positive-campaign-writer-contract','version':4,'sourceSHA256':source_pins(SOURCE/'aeris_runtime'),'sites':sites(SOURCE/'aeris_runtime',include_source_sha=False),'siteFileHashBinding':'SOURCE_SHA256_BY_EXACT_LOGICAL_MODULE','owners':owners(),'envelope':observer_envelope(),'frozenLeafSHA256':{n:hashlib.sha256((REPO/n).read_bytes()).hexdigest()for n in LEAVES},'productInputClosure':graph,'healthContract':health_contract(),'metadataBoundary':'EXPLICIT_PREWRITE_HOOK_OR_PARENT_BOUNDED_PIPE'}
if args.write:
 write_generated(PINS,enc(pins))
 from aeris_runtime.pipeline_contract import require_closed_contract
 proof=require_closed_contract()
else:proof={'status':'INSPECT_ONLY_NOT_HELD','writerAssetNotUpdated':True}
print(json.dumps({'format':'aeris-betasim-prehold-source-discovery','write':args.write,'modules':len(graph['moduleInputs']),'readInputs':len(graph['readInputs']),'allPins':len(graph['pins']),'graphSHA256':hashlib.sha256(enc(graph)).hexdigest(),'sourceFiles':len(pins['sourceSHA256']),'potentialWriterSites':len(pins['sites']),'nativeBuildNotPerformed':True,'runtimeActorsStarted':False,'proof':proof}))
