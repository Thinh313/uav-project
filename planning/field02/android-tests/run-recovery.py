from pathlib import Path
import subprocess,shutil,json,hashlib
R=Path(__file__).resolve().parents[3];W=R/'planning/field02/android-tests/.classes';W.mkdir(exist_ok=True);(W/'BuildInfo02.java').write_text('package vn.rtr.aeris.field02;public final class BuildInfo02{public static final String SOURCE_ID="MOCK_TEST_ONLY";}')
J='/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home/bin/';A='/opt/homebrew/share/android-commandlinetools/platforms/android-37.0/android.jar';G='/opt/homebrew/share/android-commandlinetools/cmdline-tools/latest/lib/external/com/google/code/gson/gson/2.11.0/gson-2.11.0.jar';cp=A+':'+G
try:
 sources=[*list((R/'native/field02/src').glob('*.java')),*list((R/'planning/field02/android-tests/stubs').rglob('*.java')),W/'BuildInfo02.java',R/'planning/field02/android-tests/Recovery02Test.java']
 p=subprocess.run([J+'javac','-cp',cp,'-d',str(W),*map(str,sources)],capture_output=True,text=True);assert p.returncode==0,p.stderr
 q=subprocess.run([J+'java','-cp',str(W)+':'+cp,'vn.rtr.aeris.field02.Recovery02Test',str(R/'evidence/field02/android-recovery-jvm01'),str(R/'evidence/field02/qa-native-saf-journal02.jsonl')],capture_output=True,text=True);print(q.stdout,q.stderr)
 report={'compileExit':p.returncode,'runtimeExit':q.returncode,'output':q.stdout,'stderr':q.stderr,'scope':'EXACT_FROZEN_RECOVER_HOST_JVM_JSON_TIME_FSYNC_ADAPTERS_NOT_ART_OR_DURABILITY','seedSha256':hashlib.sha256((R/'evidence/field02/qa-native-saf-journal02.jsonl').read_bytes()).hexdigest(),'gsonSha256':hashlib.sha256(Path(G).read_bytes()).hexdigest(),'cacheRemoved':str(W.relative_to(R)),'harnessCorrection':'First adapter compile lacked unrelated JSONObject methods required by complete Activity; adapter completed, production code unchanged.'}
 (R/'evidence/field02/android-recovery-jvm01.json').open('x').write(json.dumps(report,indent=2)+'\n');assert q.returncode==0
finally:shutil.rmtree(W)
