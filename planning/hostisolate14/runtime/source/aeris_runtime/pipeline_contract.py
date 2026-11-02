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

def health_contract():
 from .host_health import AUDIT_LEASE,ROW_LIMIT,QUEUE_ROWS,ROW_BYTES,MAX_PENDING,HEADER,DISK_ROW,POWER_ROW,INVENTORY_INTERVAL_NS,INVENTORY_DEADLINE_NS,INVENTORY_MAX_AGE_NS,INVENTORY_ROW_LIMIT
 from .stage_trace import CODES,MAX_ROWS,MAX_EVENTS,MAX_SNAPSHOT
 from .power_worker import BINDING as POWER_BINDING,LIFETIME_LEASE,REQUEST,RESPONSE_MAX
 return {'format':'aeris-private-host-health-bounds','version':2,'powerHelperIsolation':{'powerFormat':'POWER_HELPER14_BOUND_ROWS','bindingBytes':POWER_BINDING.size,'perLifeReservedBytes':LIFETIME_LEASE,'requestBytes':REQUEST.size,'responseMaximumBytes':RESPONSE_MAX,'processesPerCase':2,'existingDiagnosticChildrenCeiling':4,'oneCaseOnly':True,'periodicAcquisitionOutsideServingProcess':True},'ownersRemainOriginal':True,'healthLedgerCountersAreReservedNotProduced':True,'auditLeaseBytes':dict(AUDIT_LEASE),'diskAndPowerRowCreditsPerLife':dict(ROW_LIMIT),'queueRows':QUEUE_ROWS,'payloadMaximumBytes':ROW_BYTES,'maximumPendingIncludingInFlightRejected':MAX_PENDING,'binaryHeaderBytes':HEADER.size,'diskFrameBytes':HEADER.size+DISK_ROW.size,'acceptedPowerFrameMaximumBytes':HEADER.size+POWER_ROW.size+192+POWER_BINDING.size,'oneFailurePowerPrefixMaximumBytes':HEADER.size+POWER_ROW.size+193+129+POWER_BINDING.size,'logicalMaximumAuditBytes':{owner:limit*(HEADER.size+DISK_ROW.size+HEADER.size+POWER_ROW.size+192+POWER_BINDING.size)+INVENTORY_ROW_LIMIT[owner]*(HEADER.size+ROW_BYTES)+3*(HEADER.size+ROW_BYTES) for owner,limit in ROW_LIMIT.items()},'inventoryRowLimit':dict(INVENTORY_ROW_LIMIT),'inventoryCadenceNs':INVENTORY_INTERVAL_NS,'inventoryInFlightDeadlineNs':INVENTORY_DEADLINE_NS,'inventoryMaximumAgeNs':INVENTORY_MAX_AGE_NS,'socketNamespaceChargedBytes':4096,'maximumFreshSocketNames':3,'requestMaximumBytes':256,'replyMaximumBytes':4096,'readDeadlineNs':100000000,'powerFreshnessAndQueryDeadlineNs':2000000000,'actualSamplerCadenceNs':100000000,'traceCodes':len(CODES),'traceTailRows':MAX_ROWS,'traceEventMaximum':MAX_EVENTS,'traceSnapshotMaximumBytes':MAX_SNAPSHOT,'tracePersistence':'TWO_SNAPSHOTS_WITHIN_EXISTING_TERMINAL_RECORD_CAPS','hotHealthWaitsOnMetadataLedger':False,'inventorySnapshotPublicationLock':'SAME_CAMPAIGN_METADATA_FLOCK','inventoryDeadlineIncludesLockWait':True,'scanTimeAccountingContext':True,'rawDomains':'EXACT_REGISTERED_RAW_AND_AP_STATE_ROOTS','exportDomains':'FOUR_EXACT_REGISTERED_EXPORT_PATHS_ONE_SHARED_192M_HOST_CAP','missingFilePolicy':'FAIL_NO_SKIP_RETRY_OR_ZERO','transportProjectionPublicationDeadlineNs':250000000,'managedClosing':'NONACCEPTING_INVENTORY_ONLY_QUIESCE_BEFORE_OWNED_EMULATOR_EXIT','inventoryFinalSlotReserved':True,'shutdownGenuineHealthCheckMaximumWaitNs':100000000,'managedFinalInventoryUsesOriginalDeadlineAndCaps':True,'originalRowsRequireDurableBarrier':True}

def source_pins(root):
 root=Path(root)
 return {'aeris_runtime/'+str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(root.rglob('*'))if p.is_file()and p.suffix in('.py','.json','.txt','.parm')and p.name!='pipeline-writer-pins.json'and '__pycache__'not in p.parts}

def require_closed_contract():
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
