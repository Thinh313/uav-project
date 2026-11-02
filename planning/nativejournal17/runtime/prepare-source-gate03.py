#!/usr/bin/env python3
"""Before HOLD only: discover exact selected readonly inputs, emit closed pins.
Default is inspection only. --write mutates only the two new source assets.
This does not build, sign, freeze, admit or launch any actual runtime actor.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,os
P=Path(__file__).resolve();REPO=P.parents[3];SOURCE=P.parent/'source';os.environ['AERIS_REPOSITORY_ROOT']=str(REPO);sys.path[:0]=[str(SOURCE),str(REPO)]
from aeris_runtime.product_inputs import discover,CONTRACT
from aeris_runtime.pipeline_contract import source_pins,sites,owners,health_contract,PINS
from aeris_runtime.metadata_budget import observer_envelope
from aeris_runtime.dependencies import LEAVES
p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--node',required=True);args=p.parse_args()
node=Path(args.node);assert node.is_absolute()and node.is_file()
script="""import{PRODUCT_READ_INPUTS}from'./planning/nativejournal17/product/server-codec09c.mjs';import{MEDIA_READ_INPUTS}from'./planning/nativejournal17/product/media-server-codec09.mjs';import{ASSETS}from'./planning/betasim-integrated01/scene/assets.mjs';console.log(JSON.stringify([...new Set([...PRODUCT_READ_INPUTS,...MEDIA_READ_INPUTS,...Object.values(ASSETS)])].sort()));"""
r=subprocess.run([str(node),'--input-type=module','-e',script],cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True);assert not r.stderr and len(r.stdout)<=65536;reads=json.loads(r.stdout)
entries=['planning/nativejournal17/runtime/product-companion-codec09.mjs','planning/nativejournal17/runtime/verified-loader.mjs','planning/nativejournal17/runtime/root-owner-native17-adopt03.py','planning/nativejournal17/runtime/preview-native17-adopt03.py','planning/nativejournal17/runtime/scenario-native-only17.py'];reads+=['planning/nativejournal17/receiver17.py','planning/nativejournal17/archive_verifier17.py','planning/nativejournal17/verify-signatures17.mjs'];adoption=json.loads((SOURCE/'aeris_runtime/assets/adoption17-originals.json').read_bytes());reads+=list(adoption['files']);graph=discover(entries,reads)
enc=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
if args.write:CONTRACT.write_bytes(enc(graph))
pins={'format':'aeris-positive-campaign-writer-contract','version':4,'sourceSHA256':source_pins(SOURCE/'aeris_runtime'),'sites':sites(SOURCE/'aeris_runtime',include_source_sha=False),'siteFileHashBinding':'SOURCE_SHA256_BY_EXACT_LOGICAL_MODULE','owners':owners(),'envelope':observer_envelope(),'frozenLeafSHA256':{n:hashlib.sha256((REPO/n).read_bytes()).hexdigest()for n in LEAVES},'productInputClosure':graph,'healthContract':health_contract(),'metadataBoundary':'EXPLICIT_PREWRITE_HOOK_OR_PARENT_BOUNDED_PIPE'}
if args.write:
 PINS.write_bytes(enc(pins))
 from aeris_runtime.pipeline_contract import require_closed_contract
 proof=require_closed_contract()
else:proof={'status':'INSPECT_ONLY_NOT_HELD','writerAssetNotUpdated':True}
print(json.dumps({'format':'aeris-betasim-prehold-source-discovery','write':args.write,'modules':len(graph['moduleInputs']),'readInputs':len(graph['readInputs']),'allPins':len(graph['pins']),'graphSHA256':hashlib.sha256(enc(graph)).hexdigest(),'sourceFiles':len(pins['sourceSHA256']),'potentialWriterSites':len(pins['sites']),'nativeBuildNotPerformed':True,'runtimeActorsStarted':False,'proof':proof}))
