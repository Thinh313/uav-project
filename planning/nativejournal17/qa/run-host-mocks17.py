#!/usr/bin/env python3
"""Bounded host-only fixtures. No Android, AP, actors or source mutation."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
R=Path(__file__).resolve().parents[3];Q=Path(__file__).resolve().parent;J=Path('/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home');S=R/'native/nativejournal17/src/vn/rtr/aeris/mission'
files=[S/x for x in ('JournalGuard17.java','JournalLifecycle17.java','JournalRegistry17.java')]+[Q/'LifecycleCoreTest17.java',Q/'RegistryReplayFixture17.java',Q/'test-receiver17.py',Q/'test-archive17.py',Q.parent/'receiver17.py',Q.parent/'archive_verifier17.py'];H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p.relative_to(R)):H(p)for p in files};work=Path(tempfile.mkdtemp(prefix='host-mock-owned-',dir=Q));env={k:v for k,v in os.environ.items()if k not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS')};env.update(PYTHONDONTWRITEBYTECODE='1',NATIVE17_QA_CLASSES=str(work))
try:
 commands=[[str(J/'bin/javac'),'-J-Xmx128m','-d',str(work),*map(str,[p for p in files if p.suffix=='.java'])],[str(J/'bin/java'),'-Xmx128m','-cp',str(work),'LifecycleCoreTest17',str(work/'fixtures')],['python3',str(Q/'test-receiver17.py')],['python3',str(Q/'test-archive17.py')]]
 for argv in commands:
  q=subprocess.run(argv,cwd=R,env=env,capture_output=True,timeout=90)
  if len(q.stdout)+len(q.stderr)>1048576:raise RuntimeError('MOCK_CAPTURE_BOUND')
  print(q.stdout.decode(),end='');print(q.stderr.decode(),end='')
  if q.returncode:raise RuntimeError('MOCK_COMMAND_FAILED:'+str(q.returncode))
 if before!={str(p.relative_to(R)):H(p)for p in files}:raise RuntimeError('SOURCE_CHANGED_DURING_MOCK')
 print(json.dumps({'status':'PASS_HOST_FILESYSTEM_MOCK_NOT_ANDROID','sourcePins':before,'ownedTemporaryClassesAndFixturesRemovedOnExit':True},separators=(',',':')))
finally:shutil.rmtree(work)
