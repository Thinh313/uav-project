"""Read-only S01 corpus fixture, never current migration authorization."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];root=R/'evidence/missionintegrated16/s01/sessions/mission16-nominal-short01/android-api';backup=root.parent/'native-restart-metadata.tar'
def refs(kind):
 out=[];at=0
 for line in(root/'receipts'/(''+kind+'.jsonl')).read_bytes().splitlines(keepends=True):
  q=json.loads(line);ref={'format':'aeris-original-byte-ref','version':3,'path':'receipts/'+kind+'.jsonl','offset':at,'bytes':len(line),'sha256':hashlib.sha256(line).hexdigest()};out.append((q,ref));at+=len(line)
 return out
commands={q['sequence']:ref for q,ref in refs('command')};capture=next(ref for q,ref in refs('diagnostic')if q.get('format')=='aeris-native-export'and q.get('path')==str(backup))
v={'format':'aeris-journal17-original-cold-backup','version':1,'candidatePath':str(R/'evidence/missionintegrated16/candidates/9e01e2dc55f4c1545388204674b236bb1babf1a6da97fcbc57d383ffaac0190c'),'candidateSHA256':'9e01e2dc55f4c1545388204674b236bb1babf1a6da97fcbc57d383ffaac0190c','androidEvidenceRoot':str(root),'coldBeforeRef':commands[10],'coldAfterRef':commands[16],'installedPathRef':commands[12],'installedSHARef':commands[13],'backupCaptureRef':capture,'backupSHA256':hashlib.sha256(backup.read_bytes()).hexdigest(),'backupBytes':backup.stat().st_size};out=Path(__file__).with_name('historical-S01-cold-proof.json');out.write_text(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n');print(hashlib.sha256(out.read_bytes()).hexdigest())
