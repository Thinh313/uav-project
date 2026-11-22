"""LINUXPORT01 exact patches for runtime-l18 (team decisions, not the owner's).

runtime-l18 is runtime-l17 plus (A) the Linux port of the G2/G3 path (the owner's SITL autopilot, "AP", in a
container, the physics backend on the host) and (B) a new team G1 chain m909/m910/g110, so that one candidate
serves G1 and G2/G3 (G2/G3 must run on the candidate of the accepted G1). Every item replaces an owner guard or
an owner file by a declared patch. All were decided by the user (Thinh) in chat, in the words quoted here, not by
the owner and not by Claude; the owner has not been asked or told (report 4zzz (tiep), parts of 2026-11-10..12).

A. G2/G3 on this x86_64 Linux PC
1. AP identity, "Option (a): keep key". The owner's AP is ARM64-only and runs under the user-installed
   qemu-user-static (binfmt flags POF). There /proc/<pid>/exe is the emulator, not the AP (log 2026-11-11/03), so
   the owner's check ACTUAL_AP_EXECUTABLE would refuse every run. The receipt key actualAPExecutableSHA256 is kept
   (supervisor.py stays byte-identical) and redefined as the SHA-256 of the AP file the process has mapped. It is
   written only if all of these hold, read by bounded host queries through docker exec: the harness's own
   sha256sum /proc/<pid>/exe equals the pinned emulator ("Yes, pin qemu": e4f8d99e...; a new pin only on the
   user's word); cmdline is exactly the binfmt interpreter, the AP path, then the command the AP supervisor
   recorded; sha256sum of the AP file equals the pinned AP; every maps line that names the AP file has exactly that
   path, at least one at offset 0. readlink /proc/<pid>/exe is recorded only. Any mismatch refuses the launch
   (ACTUAL_AP_MAPPED_ARTIFACT_L18:<reason>). commands.py gets exact allowlist entries for the four new query forms.
2. Physics kernel, "Yes, provider only". dependencies.LEAVES gains the Linux build of the owner's
   pilot/sim32/kernel.c (a0dbf90d..., build command in log 2026-11-10/29; the darwin entry stays). Only
   assets/workbench-provider.json changes its modelKernelSHA256 to that hash; the owner's run-profile02.json files
   are not copied or changed (G2/G3 never load them). The backend entry always requires that the loaded kernel is
   that file with that hash and that the run config declares it (never skipped when no kernel is loaded).
   Consequence: expectedConfigSHA256 of a team G2/G3 run differs from the owner's.
3. AP argv: --model JSON:192.168.65.254 (Docker Desktop's host address on the owner's Mac; on this PC it routes out
   of the machine) becomes JSON:172.17.0.1 (the Docker bridge). No --platform ("Accept all seven", item 1).
4. JSON forwarder, "R: forwarder" and "Accept all seven" item 5. The backend keeps listening only on
   127.0.0.1:9012. aeris_runtime/json_forwarder.py is the forwarding function of the tested team tool
   tools/sitl_json_udp_forwarder.py (logs 2026-11-11/01-02; copied unchanged into runtime-l18 and pinned by
   SHA-256), without its selftest/bench helpers, with a harness entry and a ready line that carries run, epoch and
   boot. launch.py starts it after the backend is ready and before the AP, after checking that 172.17.0.1:9012 can
   be bound, and reads its ready line from its own captured stdout.
5. The forwarder is a third owned child, "Yes, write it" (2026-11-12, after these consequences were listed).
   Three owner guards fix the child set to ap and backend and are widened to ap, forwarder, backend: resources.py
   (start, and the stop order ap, forwarder, backend), disposal.py (ONLY_SOURCE_SIMULATION_CHILDREN and its stop
   loop), raw_export.py (NORMAL_WORKBENCH_SOURCE_DRAIN_REQUIRED). metadata_budget.py: the children counter 4
   becomes 6 (two cases, three children each) and the child-output path pattern admits forwarder. The child_output
   owner cap stays 4 MiB: the owner's four leases use 4 x 1,040,384 B and leave 32,768 B; each forwarder lease is
   16,384 B (two 4,096 B pipes, 8,192 B for missing parent directories), so the worst case is exactly 4 MiB.
   entry.py admits the component json_forwarder.

B. G1 chain m909/m910/g110, "Path A: pinned state" (2026-11-12)
   g109 attempt 1 failed (owner guard NAVIGATION_ACTUAL_DISPATCH200MS) and left the app data changed. The chain
   starts from the pinned contract-l16 state (avd-before-g109.tar = avd-after-m908.tar), to which the real AVD must
   be restored before the first boot (a separate step on the user's word). The data admission stays contract-l16
   (pin 15039006...), the team verifier runtime-l16/native-unused-l16.mjs and the emulator spec are unchanged.
   continuation_l18.py is continuation_l17.py moved to the new slots; the prior boot of m909 is the clean m908
   boot of runtime-l17 (candidate 70af1371...), read back from its own raw records as m907 read back m906.

The writer limit (200 ms), the 40 MiB artifact cap, the 64 MiB Private bound and every guard not named above are
unchanged. root-owner-h10.py (the G2/G3/G4 entry) stays byte-identical to the owner's. Every file below is
generated from its runtime-l17 original (or from the pinned tool) by these replacements, and test-linuxport18.py
re-derives each one. Each `old` must occur exactly once, or exactly the count given as a third element.
"""

L17_CANDIDATE='70af1371a616595b8b8eaba2611ea0db3967d0f0bccade8be0eb92b41d279e6e'
LINUX_KERNEL='pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-x86_64-linux-gnu.so'
LINUX_KERNEL_SHA256='a0dbf90dd96ba72e37bca85ba955c84b5bc0ef9c8c1f4ca92605ceb46cf616c4'
DARWIN_KERNEL_SHA256='3db9ac03292378fa51aa269561befa87c6cd6a7a60e8c176b85d7abc26c84247'
EMULATOR_SHA256='e4f8d99e9ff69c3cefffab71cee358ce2af1ecba1282d04c3eeb44ef76f5a71e'
AP_ARTIFACT='/candidate/arducopter-m1-stagepipe-03'
# The tested team tool, copied unchanged from aeris-private/tools into runtime-l18/ (never change a tool a log used).
FORWARDER_TOOL='sitl_json_udp_forwarder.py'
FORWARDER_TOOL_SHA256='266a94547ec1d335b02020b04aea9e2a9f67949ab99adacc94db13d2ed7995a2'

# ---------------------------------------------------------------------------------------------------------------
# A. Source modules: runtime-l17/source/aeris_runtime/<name> -> runtime-l18/source/aeris_runtime/<name>
# ---------------------------------------------------------------------------------------------------------------
LAUNCH_WAIT=''' def _wait_forwarder(self,resources,campaign_deadline):
  """runtime-l18 (team): wait for the JSON forwarder's ready line, read from its own captured stdout."""
  from .json_forwarder import ready_line
  start=self.now();deadline=min(start+5_000_000_000,campaign_deadline);log=Path(resources.children['forwarder'].stdout_path)
  while True:
   self.check();resources.require_alive('forwarder')
   value=ready_line(log.read_bytes()if log.exists()else b'',self.config)
   if value is not None:return value,{'startHostNs':start,'readyHostNs':self.now(),'gateSeconds':5}
   if self.now()>deadline:raise TimeoutError('OWNED_FORWARDER_START_DEADLINE')
   self.sleep(.05)
'''
LAUNCH_IDENTITY=r'''
AP_ARTIFACT_L18='/candidate/arducopter-m1-stagepipe-03';BINFMT_INTERPRETER_L18='/usr/libexec/qemu-binfmt/aarch64-binfmt-P'
EMULATOR_SHA256_L18='e4f8d99e9ff69c3cefffab71cee358ce2af1ecba1282d04c3eeb44ef76f5a71e';FORWARDER_LISTEN_L18=('172.17.0.1',9012)
def ap_identity_l18(query,name,ap,cfg):
 """runtime-l18 (team decisions "Option (a): keep key" and "Yes, pin qemu", not the owner's). Under ARM user
 emulation /proc/<pid>/exe is the emulator, so the AP is identified by the artifact the process has mapped. Returns
 the receipt fields only if the executable is the pinned emulator, cmdline is the binfmt interpreter plus the AP
 path plus the recorded AP command, the AP file has the pinned SHA-256 and every maps line naming the AP file has
 exactly that path (one at offset 0). The harness's own exe query comes first and the maps query last."""
 def refuse(reason):raise ValueError('ACTUAL_AP_MAPPED_ARTIFACT_L18:'+reason)
 pid=ap.get('APPID');command=ap.get('command')
 if type(pid)is not int or pid<=0 or type(command)is not list or not command or any(type(v)is not str for v in command)or command[0]!=AP_ARTIFACT_L18:refuse('LAUNCH_RECORD')
 proc='/proc/'+str(pid)
 emulator=query(['docker','exec',name,'sha256sum',proc+'/exe']).split()[:1]
 if emulator!=[EMULATOR_SHA256_L18]:refuse('PINNED_EMULATOR_SHA256')
 path=query(['docker','exec',name,'readlink',proc+'/exe']).rstrip('\n')
 if query(['docker','exec',name,'sha256sum',AP_ARTIFACT_L18]).split()[:1]!=[cfg['APSHA256']]:refuse('ARTIFACT_SHA256')
 raw=query(['docker','exec',name,'cat',proc+'/cmdline'])
 if not raw.endswith('\0')or raw[:-1].split('\0')!=[BINFMT_INTERPRETER_L18,AP_ARTIFACT_L18,*command]:refuse('CMDLINE')
 lines=query(['docker','exec',name,'grep','-F',AP_ARTIFACT_L18,proc+'/maps']).splitlines();rows=[line.split(None,5)for line in lines]
 if not 0<len(rows)<=16 or any(len(row)!=6 or row[5]!=AP_ARTIFACT_L18 for row in rows)or not any(row[2]=='00000000'for row in rows):refuse('MAPS')
 return {'actualAPExecutableSHA256':cfg['APSHA256'],'APIdentityMethod':'ARM_USER_EMULATION_MAPPED_ARTIFACT_L18','emulatorExecutablePath':path,'emulatorExecutableSHA256':emulator[0],'APCmdline':raw[:-1].split('\0'),'APMappedArtifactLines':lines}
'''
DEPENDENCIES_KERNEL='''
LINUX_KERNEL='pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-x86_64-linux-gnu.so';LINUX_KERNEL_SHA256='a0dbf90dd96ba72e37bca85ba955c84b5bc0ef9c8c1f4ca92605ceb46cf616c4'
def require_linux_kernel(declared):
 """runtime-l18 (team decision "Yes, provider only", not the owner's): the backend process must have loaded exactly the
 pinned Linux build of the owner's pilot/sim32/kernel.c, and its run config must declare that SHA-256. Unlike the
 allowlist above, this refuses when no kernel is loaded."""
 row=loaded_leaf_origins().get('pilot.betaintegrated01.runtime._sim32_kernel')
 if row!={'path':LINUX_KERNEL,'sha256':LINUX_KERNEL_SHA256}or declared!=LINUX_KERNEL_SHA256:raise RuntimeError('L18_PINNED_LINUX_SIM32_KERNEL_REQUIRED')
 return row
'''
MODULES={
 # A1 AP identity under ARM user emulation; A4 forwarder start and ready hand-off
 'launch.py':[
  ("   with socket.socket(socket.AF_INET,kind) as s:s.bind(('127.0.0.1',port))\n",
   "   with socket.socket(socket.AF_INET,kind) as s:s.bind(('127.0.0.1',port))\n  with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:s.bind(FORWARDER_LISTEN_L18)\n"),
  (" def __call__(self,resources,campaign_deadline):\n",LAUNCH_WAIT+" def __call__(self,resources,campaign_deadline):\n"),
  ("  docker=['docker','run','--rm','--name',name,",
   "  forwarder_argv=['python3','-B','-m','aeris_runtime.entry','json_forwarder','--config',str(out/'run-config.json')]\n  self.check();need_budget(cfg);resources.start('forwarder',forwarder_argv,deadline_ns=campaign_deadline,candidate_python=True)\n  forwarder,forwarder_timing=self._wait_forwarder(resources,campaign_deadline)\n  docker=['docker','run','--rm','--name',name,"),
  ("  exe=self.query(['docker','exec',name,'sha256sum','/proc/'+str(ap['APPID'])+'/exe']).split()[0]\n  if exe!=cfg['APSHA256']:raise ValueError('ACTUAL_AP_EXECUTABLE')\n",
   "  proof_l18=ap_identity_l18(self.query,name,ap,cfg)\n"),
  ("'actualAPExecutableSHA256':exe,'backendTiming':backend_timing,",
   "**proof_l18,'forwarder':forwarder,'forwarderTiming':forwarder_timing,'backendTiming':backend_timing,"),
  ("\ndef need_budget(config):\n",LAUNCH_IDENTITY+"\ndef need_budget(config):\n"),
 ],
 # A1 the four new read-only query forms (the owner's sha256sum /proc/<pid>/exe form is already allowed)
 'commands.py':[
  ("argv[3]=='sha256sum'and re.fullmatch('/proc/[1-9][0-9]*/exe',argv[4])is not None)\n",
   "argv[3]=='sha256sum'and re.fullmatch('/proc/[1-9][0-9]*/exe',argv[4])is not None)\n"
   "  permitted=permitted or(len(argv)in(5,7)and argv[:2]==['docker','exec']and argv[2].startswith('aeris-')and(argv[3:]==['sha256sum','/candidate/arducopter-m1-stagepipe-03']or(len(argv)==5 and argv[3]=='readlink'and re.fullmatch('/proc/[1-9][0-9]*/exe',argv[4])is not None)or(len(argv)==5 and argv[3]=='cat'and re.fullmatch('/proc/[1-9][0-9]*/cmdline',argv[4])is not None)or(len(argv)==7 and argv[3:6]==['grep','-F','/candidate/arducopter-m1-stagepipe-03']and re.fullmatch('/proc/[1-9][0-9]*/maps',argv[6])is not None)))\n"),
 ],
 # A2 Linux physics kernel declared next to the darwin one; the always-on check
 'dependencies.py':[
  ("'pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so',",
   "'pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-darwin.so','pilot/betaintegrated01/runtime/_sim32_kernel.cpython-314-x86_64-linux-gnu.so',"),
  (" return out\n"," return out\n"+DEPENDENCIES_KERNEL),
 ],
 # A2 the backend entry requires the pinned Linux kernel; A5 the forwarder component
 'entry.py':[
  ("choices=['backend','ap_supervisor','inspect']","choices=['backend','ap_supervisor','json_forwarder','inspect']"),
  ("module_origin_receipt(path);sys.argv=[module.__file__,",
   "module_origin_receipt(path)\n if args.component=='backend':\n  from .dependencies import require_linux_kernel\n  require_linux_kernel(json.loads(Path(args.config).read_bytes()).get('modelKernelSHA256'))\n sys.argv=[module.__file__,"),
 ],
 # A3 the AP reaches the host at the Docker bridge address
 'ap_supervisor.py':[
  ("'--model', 'JSON:192.168.65.254',","'--model', 'JSON:172.17.0.1',"),
 ],
 # A5 the forwarder as a third owned child
 'resources.py':[
  ("if name not in('ap','backend')or type(self.budget)is not MetadataBudget","if name not in('ap','backend','forwarder')or type(self.budget)is not MetadataBudget"),
  ("lease=self.budget.reserve_lease({'child_output':2*500*1024+16384})","lease=self.budget.reserve_lease({'child_output':2*4096+8192 if name=='forwarder'else 2*500*1024+16384})"),
  ("maximum_each=500*1024,lease=lease)","maximum_each=4096 if name=='forwarder'else 500*1024,lease=lease)"),
  ("  for name in ('ap','backend'):\n","  for name in ('ap','forwarder','backend'):\n",2),
 ],
 'disposal.py':[
  ("need(set(resources.children).issubset({'ap','backend'}),'ONLY_SOURCE_SIMULATION_CHILDREN')","need(set(resources.children).issubset({'ap','forwarder','backend'}),'ONLY_SOURCE_SIMULATION_CHILDREN')"),
  (" for name in('ap','backend'):\n"," for name in('ap','forwarder','backend'):\n"),
  ("for k,v in rows.items()if k in('ap','backend'))","for k,v in rows.items()if k in('ap','forwarder','backend'))"),
 ],
 'raw_export.py':[
  ("set(closure['children'])=={'ap','backend'}","set(closure['children'])=={'ap','forwarder','backend'}"),
 ],
 'metadata_budget.py':[
  ("'cases':2,'children':4,'diagnosticChildren':4,","'cases':2,'children':6,'diagnosticChildren':4,"),
  (r"child_output=session+r'processes/(?:ap|backend)\.(?:stdout|stderr)\.log'",r"child_output=session+r'processes/(?:ap|forwarder|backend)\.(?:stdout|stderr)\.log'"),
 ],
 'pipeline_contract.py':[
  ("'predispatch persistent lease;4 campaign children,2 pipes500KiB each plus16KiB perchild overhead;EOF/join before unused lease release'",
   "'predispatch persistent lease;4 AP/backend campaign children,2 pipes500KiB each plus16KiB perchild overhead;2 runtime-l18 forwarder children,2 pipes4KiB each plus8KiB perchild overhead;together exactly the unchanged4MiB owner;EOF/join before unused lease release'"),
 ],
 # B. G1 chain m909/m910/g110 (as l17_patches.py did for m907/m908/g109)
 'mission16.py':[
  ("SLOTS={'m907':180,","SLOTS={'m909':180,'m910':180,'g110':180,'m907':180,"),
 ],
 'rc01.py':[
  ("KINDS={'g109':'native',","KINDS={'g110':'native','g109':'native',"),
  ("REMAINING={'g109':0,","REMAINING={'g110':0,'g109':0,"),
  ("ARCHIVE_BOUNDARY['g109']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n",
   "ARCHIVE_BOUNDARY['g109']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\nARCHIVE_BOUNDARY['g110']='G1_UNUSED_PLUS_G2_CLOSED_BEFORE_FAULTS'\n"),
 ],
 'product_runtime.py':[
  ("'m905','m906','m907','m908')and not c['APStarted']","'m905','m906','m907','m908','m909','m910')and not c['APStarted']"),
  ("  elif self.root.name in('m907','m908'):\n   from .continuation_l17 import verify_sdk\n   verify_sdk(self,proof)\n",
   "  elif self.root.name in('m907','m908'):\n   from .continuation_l17 import verify_sdk\n   verify_sdk(self,proof)\n  elif self.root.name in('m909','m910'):\n   from .continuation_l18 import verify_sdk\n   verify_sdk(self,proof)\n"),
  ("if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908')else",
   "if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908','m909','m910')else"),
  ("  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908'):result.update",
   "  if self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908','m909','m910'):result.update"),
  ("  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')",
   "  need(self.root.name in('m401','m402','m501','m502','m701','m702','m901','m902','m903','m904','m905','m906','m907','m908','m909','m910'),'SDK_ONLY_POSITIVE_CLOSE_SCOPE')"),
 ],
 'product_native09.py':[
  (" if domain.get('nativeLifecycleContinuationL17')is True:\n  from .continuation_l17 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n",
   " if domain.get('nativeLifecycleContinuationL17')is True:\n  from .continuation_l17 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n if domain.get('nativeLifecycleContinuationL18')is True:\n  from .continuation_l18 import verify_continuation_domain\n  return verify_continuation_domain(root,ref,manifest)\n"),
 ],
}

# A2 Asset: runtime-l17/source/aeris_runtime/assets/workbench-provider.json -> runtime-l18 (one field)
ASSET='assets/workbench-provider.json'
ASSET_PATCHES=[
 ('"modelKernelSHA256": "'+DARWIN_KERNEL_SHA256+'"','"modelKernelSHA256": "'+LINUX_KERNEL_SHA256+'"'),
]

# ---------------------------------------------------------------------------------------------------------------
# A4 New team module: runtime-l18/sitl_json_udp_forwarder.py (pinned tool) -> source/aeris_runtime/json_forwarder.py
# ---------------------------------------------------------------------------------------------------------------
FORWARDER_MODULE='json_forwarder.py'
FORWARDER_DOC='''"""LINUXPORT01 JSON physics forwarder for G2/G3 on Linux (team code, not the owner's; the user's decision "R: forwarder").

The owner's AP (in a container) sends its servo packets (UDP, 1200/s, lockstep) to the host. On the owner's Mac,
Docker Desktop passes them on to 127.0.0.1, where the backend listens (bind allowlist 127.0.0.1:9012) and sees one
127.0.0.1 sender. On Linux a container reaches the host only at the Docker bridge address, so this owned child
listens on 172.17.0.1:9012 (packets from docker0 only, first sender inside 172.17.0.0/16), sends every datagram
unchanged to 127.0.0.1:9012 from one fixed 127.0.0.1 socket and every reply unchanged back to the AP. The backend,
its allowlist and its peer lock stay as the owner wrote them.

hist_stats and forward are the functions of the tested team tool sitl_json_udp_forwarder.py (logs 2026-11-11/01-02),
unchanged except that forward takes the run context and prints it in its ready line (l18_patches.FORWARDER_PATCHES);
the tool's selftest and bench helpers are left out. forward fails closed: any stop but a signal ends forwarding for
good, so the backend's own SERVO_STALE_3S fails the run. Nothing is written to disk; the ready line and the summary
line go to stdout, which the harness captures (4 KiB bound). Exit 0 on SIGTERM/SIGINT, 3 peer rule, 4 backend
refused, 5 other.
"""
'''
FORWARDER_FIRST='import hashlib,ipaddress,json,os,platform,select,signal,socket,struct,subprocess,sys,time\n'
FORWARDER_CUT='def echo():\n'
FORWARDER_PATCHES=[
 (FORWARDER_FIRST,'import argparse,hashlib,ipaddress,json,os,select,signal,socket,time\nfrom pathlib import Path\n'),
 ("SERVO=struct.Struct('<HHI16H');PAD=bytes(range(256))+bytes(36);now=time.perf_counter_ns\n",
  "now=time.perf_counter_ns\nLISTEN_IP='172.17.0.1';LISTEN_PORT=9012;BACKEND_IP='127.0.0.1';BACKEND_PORT=9012;DEVICE='docker0';SUBNET='172.17.0.0/16'\n"),
 ("def forward(listen_ip,listen_port,backend_port,device,subnet):\n","def forward(listen_ip,listen_port,backend_port,device,subnet,context):\n"),
 (" print(json.dumps({'kind':'ready','tool':'sitl_json_udp_forwarder.py','pid':os.getpid(),",
  " print(json.dumps({**context,'kind':'ready','tool':'aeris_runtime.json_forwarder','pid':os.getpid(),"),
]
FORWARDER_TAIL=r'''def ready_line(raw,config):
 """For launch.py: None until the first stdout line is complete; then it must be this run's ready line, or the launch is refused."""
 if len(raw.split(b'\n',1)[0])>1024:raise ValueError('L18_FORWARDER_READY_BOUND')
 if b'\n'not in raw:return None
 value=json.loads(raw.split(b'\n',1)[0])
 if type(value)is not dict or any(value.get(k)!=config[k]for k in('run','epoch','boot')):raise ValueError('L18_FORWARDER_READY_CONTEXT')
 if value.get('kind')!='ready'or value.get('tool')!='aeris_runtime.json_forwarder'or type(value.get('pid'))is not int or value.get('listen')!=[LISTEN_IP,LISTEN_PORT]or value.get('backend')!=[BACKEND_IP,BACKEND_PORT]or value.get('device')!=DEVICE or value.get('subnet')!=SUBNET:raise ValueError('L18_FORWARDER_READY_ENDPOINTS')
 return value
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
 config=json.loads(Path(args.config).read_bytes())
 if config.get('bind')!=[BACKEND_IP,BACKEND_PORT]:raise ValueError('L18_FORWARDER_BACKEND_BIND')
 raise SystemExit(forward(LISTEN_IP,LISTEN_PORT,BACKEND_PORT,DEVICE,SUBNET,{k:config[k]for k in('run','epoch','boot')}))
if __name__=='__main__':main()
'''
def forwarder(text):
 """The pinned tool -> json_forwarder.py: keep only the part from its import line up to (not including) `def echo():`
 (imports, the constants line, hist_stats, forward), apply FORWARDER_PATCHES, put FORWARDER_DOC before and FORWARDER_TAIL after."""
 for mark in(FORWARDER_FIRST,FORWARDER_CUT):
  if text.count(mark)!=1:raise ValueError('L18_FORWARDER_MARK:%r'%mark[:40])
 a=text.index(FORWARDER_FIRST);b=text.index(FORWARDER_CUT)
 if not a<b:raise ValueError('L18_FORWARDER_MARK_ORDER')
 return FORWARDER_DOC+apply(text[a:b],FORWARDER_PATCHES,FORWARDER_MODULE)+FORWARDER_TAIL

# ---------------------------------------------------------------------------------------------------------------
# B. New team module: runtime-l17/source/aeris_runtime/continuation_l17.py -> runtime-l18/.../continuation_l18.py
# ---------------------------------------------------------------------------------------------------------------
NEW_MODULE_SOURCE='continuation_l17.py';NEW_MODULE='continuation_l18.py'
NEW_MODULE_PATCHES=[
 ('''continuation_l16.py (runtime-l16) for a new chain (m907/m908 qualification, G1 g109) from the
same pinned 89-file state, after g108 attempt 1 failed and the AVD was restored to the backup
taken right after m906 (the user's decision, path A, report 4zzs), with the team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m906 boot of runtime-l16) change. Replaces, for these''',
  '''continuation_l17.py (runtime-l17) for a new chain (m909/m910 qualification, G1 g110) from the
same pinned 89-file state, after g109 attempt 1 failed (owner guard NAVIGATION_ACTUAL_DISPATCH200MS);
the AVD must be restored to the backup taken right after m908 before the first boot (the user's
decision "Path A: pinned state", 2026-11-12), with the unchanged team emulator spec
emulator-spec-02.json. Only the slots, the run names, the format names and the prior boot of the
first qualification boot (now the clean m908 boot of runtime-l17) change. Replaces, for these'''),
 ("M906='evidence/betarc01/m906';M906_RUN='beta-rc01-sdk-continuation06';L16_CANDIDATE='b07badbf8e31d19d62bba7133ffd9cb34634660eb963f556d132d4a87784840d'\nSLOTS=('m907','m908');QUALIFICATION='aeris-linuxport01-l17-root-contract-sdk-cold-acceptance'\nRUNS={'m907':'beta-rc01-sdk-continuation07','m908':'beta-rc01-sdk-continuation08'}",
  "M908='evidence/betarc01/m908';M908_RUN='beta-rc01-sdk-continuation08';L17_CANDIDATE='"+L17_CANDIDATE+"'\nSLOTS=('m909','m910');QUALIFICATION='aeris-linuxport01-l18-root-contract-sdk-cold-acceptance'\nRUNS={'m909':'beta-rc01-sdk-continuation09','m910':'beta-rc01-sdk-continuation10'}"),
 ("raise ValueError('L17_'+n)","raise ValueError('L18_'+n)"),
 ("'aeris-linuxport01-l17-continuation-admission'","'aeris-linuxport01-l18-continuation-admission'"),
 # the prior boot of the first qualification boot: m906 of runtime-l16 -> m908 of runtime-l17
 ("def m906_prior():\n","def m908_prior():\n"),
 (''' """Prior boot UUID and codePath for m907, read back with the harness readers from the team m906 qualification boot of
 runtime-l16 (candidate b07badbf...): the last boot of the pinned state, to which the AVD was restored (report 4zzs).
''',''' """Prior boot UUID and codePath for m909, read back with the harness readers from the team m908 qualification boot of
 runtime-l17 (candidate 70af1371...): the last boot of the pinned state, to which the AVD must be restored before
 this chain (the user's decision "Path A: pinned state", 2026-11-12).
'''),
 ("repo=repository();root=repo/M906;","repo=repository();root=repo/M908;"),
 ("report.get('candidateSHA256')==L16_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L16_CANDIDATE,'M906_QUALIFICATION_SCOPE')",
  "report.get('candidateSHA256')==L17_CANDIDATE and term.get('status')=='SDK_ONLY_POSITIVE_CLOSED_AWAITING_ROOT_COLD_ACCEPTANCE'and term.get('candidateSHA256')==L17_CANDIDATE,'M908_QUALIFICATION_SCOPE')"),
 ("'M906_ORIGINAL_NORMAL_SDK_CLOSURE'","'M908_ORIGINAL_NORMAL_SDK_CLOSURE'"),
 ("tar=root/'sessions'/M906_RUN/'native-restart-metadata.tar'","tar=root/'sessions'/M908_RUN/'native-restart-metadata.tar'"),
 ("'M906_IS_PINNED_STATE'","'M908_IS_PINNED_STATE'"),
 ("store=root/'sessions'/M906_RUN/'android-api'","store=root/'sessions'/M908_RUN/'android-api'"),
 ("'M906_ORIGINAL_CODEPATH_BOOT'","'M908_ORIGINAL_CODEPATH_BOOT'"),
 # the chain itself
 ("reconcile_h7.require_qualification with the team m907/m908 proof format","reconcile_h7.require_qualification with the team m909/m910 proof format"),
 ("'SOURCE_BOUND_L17_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'","'SOURCE_BOUND_L18_METADATA_NOT_RAW_OR_FLIGHT_ACCEPTANCE'"),
 ("reconcile_h7.verify_sdk for m907/m908:","reconcile_h7.verify_sdk for m909/m910:"),
 ("if owner.root.name=='m908':\n  prior=decode((owner.repo/'evidence/betarc01/m907/reports/coldboot-h7.json')","if owner.root.name=='m910':\n  prior=decode((owner.repo/'evidence/betarc01/m909/reports/coldboot-h7.json')"),
 ("'aeris-linuxport01-l17-continuation-readonly-resume'","'aeris-linuxport01-l18-continuation-readonly-resume'",2),
 ("reconcile_h7.resume_existing for g109:","reconcile_h7.resume_existing for g110:"),
 ("resumeL17Attempted","resumeL18Attempted",2),
 ("'native17-continuation-l17.json'","'native17-continuation-l18.json'",2),
 ("case['resumeL17']=proof","case['resumeL18']=proof"),
 ("'nativeLifecycleContinuationL17'","'nativeLifecycleContinuationL18'",2),
 ("'application-domain17-continuation-l17.json'","'application-domain17-continuation-l18.json'"),
]

# Qualification entry: runtime-l17/root-qualify-l17.py -> runtime-l18/root-qualify-l18.py
QUALIFY_SOURCE='planning/linuxport01/runtime-l17/root-qualify-l17.py'
QUALIFY=[
 ('"""LINUXPORT01 (team entry): fresh coldboot qualification m907/m908 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, then runtime-l17/l17_patches.py. No install, Activity, AP or automatic repair."""',
  '"""LINUXPORT01 (team entry): fresh coldboot qualification m909/m910 checked by the m803 continuation contract.\nOwner root-reconcile-h9.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, then runtime-l18/l18_patches.py. No install, Activity, AP or automatic repair."""'),
 ("choices=('m907','m908')","choices=('m909','m910')"),
 ("proof.get('format')=='aeris-linuxport01-l17-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M906_L16_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m907'else",
  "proof.get('format')=='aeris-linuxport01-l18-root-sdk-prerequisite'and proof.get('version')==1 and proof.get('status')==('ROOT_COLD_VERIFIED_M908_L17_NORMAL_CLOSE_NOT_QUALIFICATION'if a.slot=='m909'else"),
 (" from aeris_runtime.continuation_l17 import m906_prior,rich_table,contract_check\n priorSlot='m906'if a.slot=='m907'else'm907';priorRun='beta-rc01-sdk-continuation06'if a.slot=='m907'else'beta-rc01-sdk-continuation07';",
  " from aeris_runtime.continuation_l18 import m908_prior,rich_table,contract_check\n priorSlot='m908'if a.slot=='m909'else'm909';priorRun='beta-rc01-sdk-continuation08'if a.slot=='m909'else'beta-rc01-sdk-continuation09';"),
 (" if a.slot=='m907':\n  priorBoot,path=m906_prior()\n"," if a.slot=='m909':\n  priorBoot,path=m908_prior()\n"),
 ("priorPath=R/'evidence/betarc01/m907/reports/coldboot-h7.json'","priorPath=R/'evidence/betarc01/m909/reports/coldboot-h7.json'"),
 ("run='beta-rc01-sdk-continuation07'if a.slot=='m907'else'beta-rc01-sdk-continuation08';need(intent.get('format')=='aeris-linuxport01-l17-root-sdk-positive-intent'",
  "run='beta-rc01-sdk-continuation09'if a.slot=='m909'else'beta-rc01-sdk-continuation10';need(intent.get('format')=='aeris-linuxport01-l18-root-sdk-positive-intent'"),
 ("need(a.slot!='m908'or","need(a.slot!='m910'or"),
]

# G1 entry: runtime-l17/root-native-l17.py -> runtime-l18/root-native-l18.py
NATIVE_SOURCE='planning/linuxport01/runtime-l17/root-native-l17.py'
NATIVE=[
 ('"""LINUXPORT01 (team entry): source-held native-only G1 slot g109 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, then runtime-l17/l17_patches.py. Never starts AP/backend or flight."""',
  '"""LINUXPORT01 (team entry): source-held native-only G1 slot g110 from the m803 continuation contract.\nOwner root-native-h10.py plus l11_patches.py, runtime-l13/l13_patches.py, runtime-l16/l16_patches.py, runtime-l17/l17_patches.py, then runtime-l18/l18_patches.py. Never starts AP/backend or flight."""'),
 ("choices=('g109',)","choices=('g110',)"),
 ("from aeris_runtime.continuation_l17 import require_qualification,resume_continuation\n","from aeris_runtime.continuation_l18 import require_qualification,resume_continuation\n"),
]

def gate(text):
 """runtime-l17/prepare-source-gate.py -> runtime-l18: entries point at runtime-l18, and the two new entries replace
 root-native-l17.py and root-qualify-l17.py (they only accept the used slots g109, m907, m908). Reads are unchanged:
 contract-l16 stays pinned, and the team verifier runtime-l16/native-unused-l16.mjs stays reached through the alias.
 The G2/G3 entry root-owner-h10.py stays an entry. The forwarder module is pinned with the source, and the Linux
 kernel with dependencies.LEAVES, by the gate's own code."""
 assert text.count('runtime-l17')==4,'L18_GATE_BASE'
 for a,b in(("'planning/linuxport01/runtime-l17/root-native-l17.py'","'planning/linuxport01/runtime-l18/root-native-l18.py'"),("'planning/linuxport01/runtime-l17/root-qualify-l17.py'","'planning/linuxport01/runtime-l18/root-qualify-l18.py'")):
  assert text.count(a)==1,'L18_GATE_ENTRY';text=text.replace(a,b)
 return text.replace('runtime-l17','runtime-l18')

def apply(text,patches,name):
 """Each patch is (old,new) with `old` exactly once in the text at that point, or (old,new,count)."""
 for patch in patches:
  old,new=patch[:2];count=patch[2]if len(patch)==3 else 1
  n=text.count(old)
  if n!=count:raise ValueError('L18_PATCH_ANCHOR_COUNT:%s:%d!=%d:%r'%(name,n,count,old[:60]))
  text=text.replace(old,new)
 return text
