"""Fixed source-pinned whole-pipeline writer and ownership admission contract.

Explicit source hooks and finite bounds close the cooperative metadata boundary.
No caller supplies bounds, integration booleans, or a waiver of unknown writers.
"""
from pathlib import Path
import ast,fcntl,hashlib,json,os,shutil
from .metadata_budget import observer_envelope,CAP,CLOSURE
from .paths import PACKAGE_ROOT
MIB=2**20;ENTRY=256*1024
PINS=PACKAGE_ROOT/'assets/pipeline-writer-pins.json'
# This discovery set deliberately includes indirect process output and print.
# Dynamic aliases/leaf implementations require manual owners listed below.
WRITE_CALLS={'put','exclusive','write','write_bytes','write_text','open_exclusive','Popen','print','replace','rename','link','mkdir','bind','sendall','unlink','chmod'}

def encoded(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()+b'\n'
def sites(root,include_source_sha=True):
 result=[]
 for p in sorted(Path(root).rglob('*.py')):
  if '__pycache__'in p.parts:continue
  raw=p.read_bytes();module='aeris_runtime/'+str(p.relative_to(root));tree=ast.parse(raw)
  for node in ast.walk(tree):
   if not isinstance(node,ast.Call):continue
   name=getattr(node.func,'attr',None)or getattr(node.func,'id','')
   if name=='open':
    # Include only literal write modes or an unknown mode. os.open flags are
    # classified as potential writers even when currently O_RDONLY.
    method=isinstance(node.func,ast.Attribute)and not(isinstance(node.func.value,ast.Name)and node.func.value.id=='os')
    index=0 if method else 1;mode=node.args[index]if len(node.args)>index else next((k.value for k in node.keywords if k.arg=='mode'),None)
    if isinstance(mode,ast.Constant)and type(mode.value)is str and not any(c in mode.value for c in 'wax+'):continue
   elif name not in WRITE_CALLS:continue
   snippet=ast.get_source_segment(raw.decode(),node)or ''
   enclosing=[v for v in ast.walk(tree)if isinstance(v,(ast.FunctionDef,ast.AsyncFunctionDef))and v.lineno<=node.lineno<=v.end_lineno]
   function=max(enclosing,key=lambda v:v.lineno).name if enclosing else '<module>'
   result.append({'function':function,'module':module,'line':node.lineno,'call':name,'siteSHA256':hashlib.sha256(snippet.encode()).hexdigest(),'sourceSHA256':hashlib.sha256(raw).hexdigest()})
 if not include_source_sha:result=[{k:v for k,v in row.items()if k!='sourceSHA256'}for row in result]
 return sorted(result,key=lambda v:(v['module'],v['line'],v['call'],v['siteSHA256']))

def owners():
 from .metadata_budget import OWNERS
 hooks={
 'dto':['product_writer.py','dispatch','shared15MiB owner; genuine immutable native STATUS<=16KiB and declared media files<=15MiB through Root prewrite budget; encoded video frames memory-only'],
 'stream':['ack_observer.py','_pump','2MiB pre-ready history;2KiB ACK line;4MiB cumulative; failed captured prefix uses closure'],
 'commands':['android.py','_command','atomic operation claim;bounded pipe+argv original byte refs'],
 'command_receipts':['once_store.py','receipt','1280-byte source command row;3700 shared count;navigation proof1280 with predispatch claim;coupled5MiB appendjournals'],
 'requests':['product_native09.py','status','selected fixed DEV application09;900 shared genuine STATUS/240 task bound; ACK/SDK immutable DTO<=16KiB; no reset across rollover; legacy product_native.py remains separately source-pinned'],
 'barriers':['ack_observer.py','barrier','512-byte same-stream readiness row'],
 'lifecycle':['product_writer.py','dispatch','Root shared prewrite MetadataBudget adapter for Workbench WAL/AJZ/plaintext semantic records; original combined8MiB owner guard unchanged; staged JS bytes are not durable'],
 'host_queries':['commands.py','_call','32 source allowlist queries;16KiB stdout/4KiB stderr;atomic capture claim'],
 'child_output':['resources.py','start','predispatch persistent lease;4 campaign children,2 pipes500KiB each plus16KiB perchild overhead;EOF/join before unused lease release'],
 'monitor':['host_health.py','_run','powerhelper16KiB existingownerlease+diagnosticChild; 2 life leases1MiB each withinmonitor3MiB;2100 originaldisk/power rows perlife;boundedlosslessaudit;terminalstage traces;inventory/entries retain remaining1MiB'],
 'guardian':['host_health.py','_run','powerhelper16KiB existingownerlease+diagnosticChild; guardian2MiB prefundedhealth audit+500KiBconsole/16KiBoverhead;4200disk/power rows;startup/IPC4KiB+boundedqueries fitremainingguardian3MiB;terminalstage traces'],
 'campaign':['campaign.py','_put','source bounded32 records8KiB;explicit Root clock/config writes'],
 'audit':['audit/receiver.py','__call__','unchanged full raw validators;32KiB summary+immutable raw refs;4 compact reports'],
 'external_task':['metadata_budget.py','write','Root diagnostics/reports/assisted-progress only;explicit bounded owned pipe APIs;1MiB cumulative']}
 return [{'owner':owner,'futureBytes':maximum,'sourceModule':hooks[owner][0],'hook':hooks[owner][1],'sourceEnforcement':hooks[owner][2]}for owner,maximum in OWNERS.items()]

def artifact_cap_contract(manifest=None):
 """Pure source/config consistency, before actors. No synthetic inventory facts."""
 import importlib
 from . import candidate
 cap=candidate.CAP
 if type(cap)is not int or not 0<cap<2**63:raise ValueError('ARTIFACT_SHARED_CAP_TYPED')
 def source(name):
  module=importlib.import_module('aeris_runtime.'+name);path=PACKAGE_ROOT/(name+'.py')
  if Path(module.__file__).resolve()!=path.resolve()or path.is_symlink():raise ValueError('ARTIFACT_CAP_MODULE_SOURCE_ORIGIN')
  raw=path.read_bytes();return module,ast.parse(raw),hashlib.sha256(raw).hexdigest()
 def function(tree,name,cls=None):
  scope=tree if cls is None else next((n for n in tree.body if isinstance(n,ast.ClassDef)and n.name==cls),None)
  if scope is None:raise ValueError('ARTIFACT_CAP_PREDICATE_SOURCE')
  values=[n for n in scope.body if isinstance(n,ast.FunctionDef)and n.name==name]
  if len(values)!=1:raise ValueError('ARTIFACT_CAP_PREDICATE_SOURCE')
  return values[0]
 def values(fn,key):
  return [v for node in ast.walk(fn)if isinstance(node,ast.Dict)for k,v in zip(node.keys,node.values)if isinstance(k,ast.Constant)and k.value==key]
 rows=[]
 for name,method,cls in [('host_health','_inventory_counters',None),('monitor','_caps','ResourceMonitor'),('emulator','_caps',None)]:
  module,tree,digest=source(name);items=values(function(tree,method,cls),'artifactBytes')
  if type(module.ARTIFACT_CAP)is not int or module.ARTIFACT_CAP!=cap or len(items)!=1 or not isinstance(items[0],ast.Name)or items[0].id!='ARTIFACT_CAP':raise ValueError('ARTIFACT_ACTOR_CAP_SOURCE_BINDING:'+name)
  rows.append({'module':name,'predicate':method,'capBytes':cap,'sourceSHA256':digest})
 module,tree,digest=source('preview10');fn=function(tree,'preview');items=values(fn,'artifactCap');checks=values(fn,'artifactAdmitted');delegate=function(tree,'_artifact_admitted')
 if type(module.ARTIFACT_CAP)is not int or module.ARTIFACT_CAP!=cap or module.artifact_cap_admitted is not candidate.artifact_cap_admitted or len(items)!=1 or not isinstance(items[0],ast.Name)or items[0].id!='ARTIFACT_CAP'or len(checks)!=1 or not isinstance(checks[0],ast.Call)or not isinstance(checks[0].func,ast.Name)or checks[0].func.id!='_artifact_admitted'or len(delegate.body)!=1 or not isinstance(delegate.body[0],ast.Return)or not isinstance(delegate.body[0].value,ast.Call)or not isinstance(delegate.body[0].value.func,ast.Name)or delegate.body[0].value.func.id!='artifact_cap_admitted':raise ValueError('ARTIFACT_PREVIEW_CAP_SOURCE_BINDING')
 rows.append({'module':'preview10','predicate':'_artifact_admitted','capBytes':cap,'sourceSHA256':digest})
 module,tree,digest=source('candidate');fn=function(tree,'artifact_cap_admitted')
 if not any(isinstance(n,ast.Name)and n.id=='CAP'for n in ast.walk(fn)):raise ValueError('ARTIFACT_CANDIDATE_CAP_SOURCE_BINDING')
 rows.append({'module':'candidate','predicate':'artifact_cap_admitted','capBytes':cap,'sourceSHA256':digest})
 policy=json.loads((PACKAGE_ROOT/'assets/resource-policy.json').read_bytes());reserves={'campaign':policy['campaign']['newIsolatedAPKAndArchiveReserve']}
 for seconds in ('180','760','1960'):reserves[seconds]=policy['cases'][seconds]['budget']['categories']['newIsolatedAPKAndArchiveReserve']
 if any(type(v)is not int or v!=cap for v in reserves.values()):raise ValueError('ARTIFACT_RESOURCE_POLICY_CAP_MISMATCH')
 if manifest is not None and(type(manifest)is not dict or type(manifest.get('artifactCapBytes'))is not int or manifest['artifactCapBytes']!=cap):raise ValueError('ARTIFACT_SELECTED_MANIFEST_CAP_MISMATCH')
 return {'format':'aeris-single-source-artifact-cap','version':1,'centralModule':'candidate.CAP','capBytes':cap,'actorSourceBindings':rows,'resourcePolicyReserves':reserves,'manifestCapChecked':manifest is not None,'pureSourceOnly':True,'inventoryOrNativeFactsProduced':False,'actorsStarted':False}

def metadata_cap_contract():
 """Host metadata only; native journal/private backup domains are unchanged."""
 import importlib
 from . import metadata_budget,policy
 cap=metadata_budget.CAP
 if type(cap)is not int or cap!=100*2**20:raise ValueError('HOST_METADATA_AUTHORIZED_CAP')
 rows=[]
 for name,method in [('host_health','_inventory_counters'),('monitor','_caps'),('emulator','_caps'),('lifecycle','_proof_capacity')]:
  module=importlib.import_module('aeris_runtime.'+name);path=PACKAGE_ROOT/(name+'.py');raw=path.read_bytes();tree=ast.parse(raw);fn=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name==method)
  imports=[n for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)and n.module=='metadata_budget'and n.level==1 and any(a.name=='CAP'and a.asname=='METADATA_CAP'for a in n.names)]
  values=[v for n in ast.walk(fn)if isinstance(n,ast.Dict)for k,v in zip(n.keys,n.values)if isinstance(k,ast.Constant)and k.value=='metadataBytes']
  if Path(module.__file__).resolve()!=path.resolve()or path.is_symlink()or len(imports)!=1:raise ValueError('HOST_METADATA_CENTRAL_SOURCE_BINDING:'+name)
  if name=='lifecycle':
   if not any(isinstance(n,ast.Compare)and any(isinstance(v,ast.Name)and v.id=='METADATA_CAP'for v in n.comparators)for n in ast.walk(fn)):raise ValueError('HOST_METADATA_PROOF_CAP_BINDING')
  elif len(values)!=1 or not isinstance(values[0],ast.Name)or values[0].id!='METADATA_CAP'or module.METADATA_CAP!=cap:raise ValueError('HOST_METADATA_ACTOR_CAP_BINDING:'+name)
  rows.append({'module':name,'predicate':method,'sourceSHA256':hashlib.sha256(raw).hexdigest()})
 if policy._DATA['campaign']['globalMetadataCapBytes']!=cap or any(c['budget']['categories']['globalMetadata']!=cap or sum(c['budget']['categories'].values())!=c['budget']['taskHardPeakBytes']or c['budget']['requiredFreeBytes']!=c['budget']['taskHardPeakBytes']+10*2**30+256*2**20 for c in policy._DATA['cases'].values()):raise ValueError('HOST_METADATA_RESOURCE_POLICY_CAP_OR_RESERVE_MISMATCH')
 return {'format':'aeris-central-host-metadata-cap','version':1,'capBytes':cap,'centralModule':'metadata_budget.CAP','actorSourceBindings':rows,'native64MiBUnchanged':True,'pureSourceOnly':True,'actorsStarted':False}

def health_contract():
 from .host_health import AUDIT_LEASE,ROW_LIMIT,QUEUE_ROWS,ROW_BYTES,MAX_PENDING,HEADER,DISK_ROW,POWER_ROW,INVENTORY_INTERVAL_NS,INVENTORY_DEADLINE_NS,INVENTORY_MAX_AGE_NS,INVENTORY_ROW_LIMIT
 from .stage_trace import CODES,MAX_ROWS,MAX_EVENTS,MAX_SNAPSHOT
 from .power_worker import BINDING as POWER_BINDING,LIFETIME_LEASE,REQUEST,RESPONSE_MAX
 return {'format':'aeris-private-host-health-bounds','version':2,'powerHelperIsolation':{'powerFormat':'POWER_HELPER14_BOUND_ROWS','bindingBytes':POWER_BINDING.size,'perLifeReservedBytes':LIFETIME_LEASE,'requestBytes':REQUEST.size,'responseMaximumBytes':RESPONSE_MAX,'processesPerCase':2,'existingDiagnosticChildrenCeiling':4,'oneCaseOnly':True,'periodicAcquisitionOutsideServingProcess':True},'ownersRemainOriginal':True,'healthLedgerCountersAreReservedNotProduced':True,'auditLeaseBytes':dict(AUDIT_LEASE),'diskAndPowerRowCreditsPerLife':dict(ROW_LIMIT),'queueRows':QUEUE_ROWS,'payloadMaximumBytes':ROW_BYTES,'maximumPendingIncludingInFlightRejected':MAX_PENDING,'binaryHeaderBytes':HEADER.size,'diskFrameBytes':HEADER.size+DISK_ROW.size,'acceptedPowerFrameMaximumBytes':HEADER.size+POWER_ROW.size+192+POWER_BINDING.size,'oneFailurePowerPrefixMaximumBytes':HEADER.size+POWER_ROW.size+193+129+POWER_BINDING.size,'logicalMaximumAuditBytes':{owner:limit*(HEADER.size+DISK_ROW.size+HEADER.size+POWER_ROW.size+192+POWER_BINDING.size)+INVENTORY_ROW_LIMIT[owner]*(HEADER.size+ROW_BYTES)+3*(HEADER.size+ROW_BYTES) for owner,limit in ROW_LIMIT.items()},'inventoryRowLimit':dict(INVENTORY_ROW_LIMIT),'inventoryCadenceNs':INVENTORY_INTERVAL_NS,'inventoryInFlightDeadlineNs':INVENTORY_DEADLINE_NS,'inventoryMaximumAgeNs':INVENTORY_MAX_AGE_NS,'socketNamespaceChargedBytes':4096,'maximumFreshSocketNames':3,'requestMaximumBytes':256,'replyMaximumBytes':4096,'readDeadlineNs':100000000,'powerFreshnessAndQueryDeadlineNs':2000000000,'actualSamplerCadenceNs':100000000,'traceCodes':len(CODES),'traceTailRows':MAX_ROWS,'traceEventMaximum':MAX_EVENTS,'traceSnapshotMaximumBytes':MAX_SNAPSHOT,'tracePersistence':'TWO_SNAPSHOTS_WITHIN_EXISTING_TERMINAL_RECORD_CAPS','hotHealthWaitsOnMetadataLedger':False,'inventorySnapshotPublicationLock':'SAME_CAMPAIGN_METADATA_FLOCK','inventoryDeadlineIncludesLockWait':True,'scanTimeAccountingContext':True,'artifactCapPolicy':artifact_cap_contract(),'hostMetadataCapPolicy':metadata_cap_contract(),'productWriterTrace':{'format':'PWST15','maximumBytes':4096,'maximumOperationsRetained':2,'firstFailureRetained':True,'fullHistory':False,'owner':'closure','closureOwnerCapUnchangedBytes':224*1024,'dataCommitGuardNs':200000000,'namespaceSync':'ALWAYS_FILE_AND_IMMEDIATE_PARENT_PLUS_ACTUAL_MKDIR_PARENTS','repairScope':'FIXED_PRODUCT_WRITER_PATHS_ONLY'},'rawDomains':'EXACT_REGISTERED_RAW_AND_AP_STATE_ROOTS','exportDomains':'FOUR_EXACT_REGISTERED_EXPORT_PATHS_ONE_SHARED_192M_HOST_CAP','missingFilePolicy':'FAIL_NO_SKIP_RETRY_OR_ZERO','transportProjectionPublicationDeadlineNs':250000000,'managedClosing':'NONACCEPTING_INVENTORY_ONLY_QUIESCE_BEFORE_OWNED_EMULATOR_EXIT','inventoryFinalSlotReserved':True,'shutdownGenuineHealthCheckMaximumWaitNs':100000000,'managedFinalInventoryUsesOriginalDeadlineAndCaps':True,'originalRowsRequireDurableBarrier':True}

def source_pins(root):
 root=Path(root)
 return {'aeris_runtime/'+str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(root.rglob('*'))if p.is_file()and p.suffix in('.py','.json','.txt','.parm')and p.name!='pipeline-writer-pins.json'and '__pycache__'not in p.parts}

def require_closed_contract():
 artifact_cap_contract()
 from .dependencies import LEAVES
 from .paths import repository
 expected=json.loads(PINS.read_bytes())
 if expected.get('format')!='aeris-positive-campaign-writer-contract'or type(expected.get('version'))is not int or expected['version']not in(3,4):raise ValueError('CLOSED_WRITER_CONTRACT_SCHEMA')
 if expected.get('sourceSHA256')!=source_pins(PACKAGE_ROOT)or expected.get('sites')!=sites(PACKAGE_ROOT,include_source_sha=expected['version']==3):raise ValueError('CLOSED_WRITER_SOURCE_OR_SITE_DRIFT')
 from .metadata_budget import observer_envelope
 if expected.get('envelope')!=observer_envelope()or expected.get('owners')!=owners():raise ValueError('SOURCE_OWNER_ENVELOPE_DRIFT')
 actual={name:hashlib.sha256((repository()/name).read_bytes()).hexdigest()for name in LEAVES}
 if expected.get('frozenLeafSHA256')!=actual:raise ValueError('FROZEN_LEAF_BOUNDARY_DRIFT')
 clients=expected.get('runtimeClientSHA256',{})
 if expected['version']==3:
  if len(clients)!=2 or {Path(n).name for n in clients}!={'root-client.py','scenario10.py'}:raise ValueError('ROOT_CLIENT_EXACT_SOURCE_SET')
 else:
  from .product_inputs import validate
  if expected.get('siteFileHashBinding')!='SOURCE_SHA256_BY_EXACT_LOGICAL_MODULE':raise ValueError('WORKBENCH_SITE_FILE_HASH_BINDING')
  product=validate();clients=expected.get('runtimeClientSHA256',expected.get('productInputClosure',{}).get('pins',{}))
  if clients!=product['pins']or expected.get('productInputClosure')!=product:raise ValueError('WORKBENCH_PRODUCT_FULL_SOURCE_SET')
 for name,digest in clients.items():
  if Path(name).is_absolute()or '..'in Path(name).parts or hashlib.sha256((repository()/name).read_bytes()).hexdigest()!=digest:raise ValueError('ROOT_CLIENT_WRITER_SOURCE_DRIFT')
 if expected.get('healthContract')!=health_contract():raise ValueError('SOURCE_HEALTH_BOUNDARY_DRIFT')
 if expected.get('metadataBoundary')!='EXPLICIT_PREWRITE_HOOK_OR_PARENT_BOUNDED_PIPE':raise ValueError('CLOSED_METADATA_BOUNDARY')
 return {'format':'aeris-source-closed-writer-contract','version':expected['version'],'sourceFiles':len(expected['sourceSHA256'])+1,'sites':len(expected['sites']),'owners':len(expected['owners']),'futureBytes':expected['envelope']['totalFutureBytes'],'frozenLeafs':len(actual),'sourcePinsSHA256':hashlib.sha256(PINS.read_bytes()).hexdigest(),'metadataBoundaryClosed':True,'allOtherRuntimeGatesStillRequired':True}

def evaluate(inventory):
 from .inventory import Inventory
 if type(inventory)is not Inventory or not inventory.baselinePersisted:raise ValueError('EXACT_ORIGINAL_INVENTORY_REQUIRED')
 from .metadata_budget import observer_envelope
 proof=require_closed_contract()
 from .metadata_budget import MetadataBudget
 entry=MetadataBudget(inventory.evidence/'metadata-budget').snapshot_inventory(inventory);plan=observer_envelope();current=entry['metadataBytes']
 if type(current)is not int or current<0:raise ValueError('EXACT_FULL_CURRENT_INVENTORY')
 return {'format':'aeris-campaign-writer-admission','version':3,'entryInventory':entry,'sourceContract':proof,'envelope':plan,'currentPlusSourceFutureBytes':current+plan['totalFutureBytes'],'metadataCapBytes':CAP,'admitted':current+plan['totalFutureBytes']<=CAP,'rawAndExportClassesUnchanged':True}

def admit_or_refuse(root,inventory,*,owner_root,free=None):
 """One shared campaign ledger; case paths never reset or create a new budget."""
 from .metadata_budget import MetadataBudget
 from .inventory import Inventory
 owner=Path(owner_root).resolve()
 if type(inventory)is not Inventory or inventory.evidence!=owner or not inventory.baselinePersisted:raise ValueError('EXACT_ORIGINAL_INVENTORY_ROOT_REQUIRED')
 if not Path(root).resolve().is_relative_to(owner):raise ValueError('CASE_ADMISSION_OWNER_ROOT')
 ledger=owner/'metadata-budget'
 if(ledger/'metadata-ledger.json').exists():
  budget=MetadataBudget.attach(ledger);budget.inventory=inventory;budget.require_real_actor();budget.check()
 else:
  budget=MetadataBudget(ledger,inventory,free=free);budget.admit()
 return budget
