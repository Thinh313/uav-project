"""Fixed target-Android anonymous capture conformance, no mission authority.

Pure source render/verification helpers. Root owns the one bounded DiagnosticJob
and original stdout/stderr; no pre-case OnceStore or native private IO is added.
"""
from pathlib import Path
import hashlib,re,shlex
from .metadata_budget import encoded
from .io_broker import _anonymous_capture,scratch_path
VECTORS=(
 ('B',"printf '\\000\\001\\177\\200\\377'; printf 'E42\\n' >&2; exit 7",7,bytes([0,1,127,128,255]),b'E42\n'),
 ('M','dd if=/dev/zero bs=16384 count=1 2>/dev/null',0,b'\0'*16384,b''),
 ('O','{ dd if=/dev/zero bs=16384 count=1 2>/dev/null; printf X; }',0,b'\0'*16384+b'X',b''),
 ('E',"printf '%065d' 0 >&2; exit 9",9,b'',b'0'*65),
)
def _sha(raw):return hashlib.sha256(raw).hexdigest()
def script(token):
 d=scratch_path(token);cleanup='rm -- '+ ' '.join(chr(34)+'$d/'+name+chr(34)for name in('out','err','rc','h1','h2'))+'; rmdir -- '+chr(34)+'$d'+chr(34)
 body='umask 077\nd='+d+'\nmkdir "$d" || exit 71\ntrap '+shlex.quote(cleanup)+' 0\nfor f in out err rc h1 h2; do : >"$d/$f" || exit 72; done\nprintf '+shlex.quote('C14_BEGIN '+token+'\n')+'\ncapture(){\n'+_anonymous_capture('"$@"',d,16384).decode()+'}\n'
 body+='check(){\n test "$rc:$h1:$h2:$olen:$elen" = "$2" || exit 81\n a=$(sha256sum "$d/out") || exit 82\n b=$(sha256sum "$d/err") || exit 82\n a=${a%% *}; b=${b%% *}\n test "$a" = "$3" && test "$b" = "$4" || exit 83\n printf \'C14 %s %s %s %s\\n\' "$1" "$2" "$a" "$b"\n}\n'
 for label,command,rc,out,err in VECTORS:
  body+='capture sh -c '+shlex.quote(command)+'\ncheck '+label+' '+shlex.quote(f'{rc}:0:0:{len(out)}:{len(err)}')+' '+_sha(out)+' '+_sha(err)+'\n'
 body+='rm -- '+ ' '.join(chr(34)+'$d/'+name+chr(34)for name in('out','err','rc','h1','h2'))+' && rmdir -- "$d" || exit 84\ntrap - 0\ntest ! -e "$d" || exit 85\nprintf '+shlex.quote('C14_CLEAN '+token+'\n')+'\nexit 0\n'
 return body.encode('ascii')
def expected_output(token):
 scratch_path(token)
 raw=('C14_BEGIN '+token+'\n').encode()
 for label,command,rc,out,err in VECTORS:raw+=f'C14 {label} {rc}:0:0:{len(out)}:{len(err)} {_sha(out)} {_sha(err)}\n'.encode()
 return raw+('C14_CLEAN '+token+'\n').encode()
def contract(adb,serial,token):
 if type(adb)is not str or not Path(adb).is_absolute()or len(adb.encode())>256 or serial!='emulator-5582':raise ValueError('CONFORMANCE_FIXED_OWNED_DEVICE')
 raw=script(token);argv=[str(Path(adb).resolve()),'-s',serial,'shell',shlex.join(['sh','-c',raw.decode('ascii')])]
 if len(encoded(argv))>4096:raise ValueError('CONFORMANCE_DIAGNOSTIC_ARGV4KiB')
 expected=expected_output(token)
 if len(expected)>16384:raise ValueError('CONFORMANCE_STDOUT16KiB')
 return {'format':'aeris-target-android-io-conformance-contract','version':1,'token':token,'argv':argv,'scriptSHA256':_sha(raw),'scriptBytes':len(raw),'expectedStdoutSHA256':_sha(expected),'expectedStdoutBytes':len(expected),'generatorSourceSHA256':_sha(Path(__file__).read_bytes()),'captureSourceSHA256':_sha((Path(__file__).parent/'io_broker.py').read_bytes()),'vectorCommandsSHA256':_sha(encoded([v[1]for v in VECTORS])),'maximumEachPipeBytes':16384,'diagnosticChildren':1,'missionCaseAllocated':False,'platformResultIsNotMissionRaw':True,'APKMutation':False}
def verify_capture(value,close):
 """Caller must additionally coldjoin the exact diagnostic launch/close bytes."""
 if type(value)is not dict or type(value.get('argv'))is not list or not value['argv']or encoded(value)!=encoded(contract(value['argv'][0],'emulator-5582',value.get('token'))):raise ValueError('CONFORMANCE_EXACT_SOURCE_CONTRACT')
 if close.get('format')!='aeris-diagnostic-child-close'or type(close.get('version'))is not int or close.get('version')!=3 or type(close.get('exit'))is not int or close.get('exit')!=0:raise ValueError('CONFORMANCE_DIAGNOSTIC_COMPLETE_EXIT0')
 captures=close.get('capture')
 if type(captures)is not dict or set(captures)!={'stdout','stderr'}:raise ValueError('CONFORMANCE_ORIGINAL_BOTH_PIPES')
 rows={}
 for name,row in captures.items():
  if row.get('captureComplete')is not True or row.get('failure')is not None or type(row.get('bytes'))is not int or not 0<=row['bytes']<=16384:raise ValueError('CONFORMANCE_ORIGINAL_CAPTURE_BOUNDS')
  p=Path(row['path'])
  if p.is_symlink()or not p.is_file()or p.stat().st_size!=row['bytes']:raise ValueError('CONFORMANCE_ORIGINAL_CAPTURE_FILE')
  raw=p.read_bytes()
  if name=='stderr'and raw or name=='stdout'and raw!=expected_output(value['token']):raise ValueError('CONFORMANCE_ORIGINAL_BYTES_MISMATCH')
  rows[name]={'path':str(p),'bytes':len(raw),'sha256':_sha(raw)}
 return {'status':'PASS_TARGET_ANDROID_IO_CONFORMANCE_NOT_MISSION','originalPipes':rows,'scriptSHA256':value['scriptSHA256'],'generatorSourceSHA256':value['generatorSourceSHA256'],'captureSourceSHA256':value['captureSourceSHA256'],'vectors':4,'binarySeparationAndExitChecks':True,'max16384AndOverflow16385Observed':True,'stderr64Overflow65Observed':True,'remoteExactScratchCleanupObserved':True,'hostChildExitAndBothEOFObserved':True,'missionAcceptance':False,'rawMissionEvidence':False,'authorityRestored':False}
