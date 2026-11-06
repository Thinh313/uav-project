"""One pre-spawn selected Node alias loader boundary for every RC companion."""
from pathlib import Path
import os
from .paths import repository
from .product_inputs import validate
from .candidate import sha
LOADER='planning/betarc01/node_alias_h9/verified-loader.mjs'
LEGACY='planning/nativejournal17/runtime/verified-loader.mjs'
LEGACY_ENTRY='planning/betarc01/runtime/product-companion-rc01.mjs'
ENTRY='planning/betarc01/command_h10/product-companion-h10.mjs'
def need(v,n):
 if not v:raise ValueError('NODE_ALIAS_H9_'+n)
def companion_argv(owner,argv):
 repo=repository();need(not(os.environ.get('NODE_OPTIONS','').strip()or os.environ.get('NODE_PATH','').strip()),'UNCONTROLLED_NODE_ENV')
 need(type(argv)is list and len(argv)==14 and all(type(v)is str for v in argv),'EXACT_COMPANION_ARGV')
 need(Path(argv[0]).is_absolute()and Path(argv[0]).is_file()and argv[1]=='--import'and argv[2]in[str(repo/LEGACY),str(repo/LOADER)]and argv[3]in[str(repo/LEGACY_ENTRY),str(repo/ENTRY)],'EXACT_PREFIX')
 need(argv[4::2]==['--manifest','--candidate-sha','--descriptor','--owner-pid','--maximum-seconds'],'EXACT_FLAGS')
 need(argv[5]==str(owner.candidate/'candidate.json')and argv[7]==owner.digest and argv[9]==str(owner.root/'reports'/('product-descriptor-%02d.json'%owner.budget.snapshot()['counters']['cases']))and argv[11]==str(os.getpid())and argv[13].isdigit()and 180<=int(argv[13])<=1800,'CURRENT_SELECTED_OWNER_ARGS')
 graph=validate(owner.manifest['productInputClosure']);need(graph['aliases'].get(LEGACY)==LOADER and graph['pins'].get(LOADER)==sha(repo/LOADER)and graph['pins'].get(ENTRY)==sha(repo/ENTRY),'SOURCE_HELD_ALIAS_AND_ENTRY')
 need(graph['aliases'].get(LEGACY_ENTRY)==ENTRY,'SOURCE_HELD_COMPANION_ALIAS')
 result=list(argv);result[2]=str(repo/LOADER);result[3]=str(repo/ENTRY);return result
