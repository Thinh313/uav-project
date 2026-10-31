"""Complete bounded G8 proof serialization; authoritative finite slots and writes are shared MJS."""
from pathlib import Path
import json,subprocess
R=Path(__file__).resolve().parents[2]
def write_proof(path,report,*,kind,scenario=None):
 path=Path(path);absolute=path if path.is_absolute()else R/path;scope=R/'evidence/beta06/generation08';assert absolute.is_relative_to(scope)and '..'not in absolute.parts,'PROOF_ACTIVE_SCOPE_REQUIRED'
 raw=(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();maximum=4*2**20 if kind=='final'else 128*2**10 if kind=='campaign'else 2*2**20;assert len(raw)<=maximum,'COMPLETE_PROOF_SERIALIZATION_BOUND_NO_TRUNCATION'
 args={'path':str(absolute.relative_to(R)),'kind':kind}
 if scenario is not None:args['scenario']=scenario
 proc=subprocess.run(['node',str(R/'pilot/beta06g8/proof-writer.mjs'),json.dumps(args,separators=(',',':'))],input=raw,cwd=R,capture_output=True,timeout=15)
 assert len(proc.stdout)<=64*2**10 and len(proc.stderr)<=64*2**10,'PROOF_WRITER_RESPONSE_BOUND'
 if proc.returncode:raise RuntimeError('AUTHORITATIVE_PROOF_WRITE_REFUSED:'+proc.stderr.decode(errors='replace')[-2048:])
 receipt=json.loads(proc.stdout);assert receipt.get('status')=='PROOF_WRITTEN','EXACT_DURABLE_PROOF_WRITE_RECEIPT_REQUIRED';return receipt
