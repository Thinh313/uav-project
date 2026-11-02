#!/usr/bin/env python3
"""Pure-JDK Registry17 verification. Disposable classes only inside new E17/qa."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[3];Q=R/'evidence/nativejournal17/qa';J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');S=R/'native/nativejournal17/src/vn/rtr/aeris/mission'
files=[S/x for x in ('JournalGuard17.java','JournalLifecycle17.java','JournalRegistry17.java')]+[Path(__file__).with_name('Registry17Test.java')]
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p.relative_to(R)):H(p)for p in files};env={k:v for k,v in os.environ.items()if k not in('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS')};Q.mkdir(exist_ok=True,parents=True)
work=Path(tempfile.mkdtemp(prefix='registry-jvm-owned-',dir=Q))
try:
 for argv in ([str(J/'bin/javac'),'-J-Xmx256m','-d',str(work),*map(str,files)],[str(J/'bin/java'),'-Xmx128m','-cp',str(work),'vn.rtr.aeris.mission.Registry17Test',str(Q)]):
  result=subprocess.run(argv,cwd=R,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
  if len(result.stdout)>1024*1024 or len(result.stderr)>1024*1024:raise RuntimeError('REGISTRY_QA_CAPTURE_BOUND')
  print(result.stdout.decode(),end='');print(result.stderr.decode(),end='')
  if result.returncode:raise RuntimeError('REGISTRY_QA_COMMAND_FAILED:'+str(result.returncode))
 if before!={str(p.relative_to(R)):H(p)for p in files}:raise RuntimeError('REGISTRY_QA_SOURCE_CHANGED_DURING_RUN')
 print(json.dumps({'format':'aeris-registry17-jvm-source-proof','sourceSHA256':before,'hardwareScope':'CURRENT_MAC_HOST_PURE_JDK_NOT_ANDROID','javaMaximumHeapMiB':128,'temporaryClassDirectoryRemovedOnExit':True},separators=(',',':')))
finally:
 shutil.rmtree(work)
