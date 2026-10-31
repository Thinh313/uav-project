"""Public SAF raw package integrity receiver. Never authenticates aircraft or accepts a mission."""
from pathlib import Path
import argparse,zipfile,json,hashlib,base64,re,sys,struct,io,stat
sys.dont_write_bytecode=True
from phase06 import unique
SHA=lambda b:hashlib.sha256(b).hexdigest()
LINE=re.compile(rb'\{"n":([0-9]+),"previous":"([a-f0-9]*)","elapsedMs":([0-9]+),"kind":"([A-Z0-9_]{1,60})","dataBase64":"([A-Za-z0-9+/=]*)","sha256":"([a-f0-9]{64})"\}')
def obj(b):return json.loads(b.decode('utf-8','strict'),object_pairs_hook=unique,parse_constant=lambda v:(_ for _ in()).throw(ValueError(v)))
def verify(path,run,expect,expect_sha256):
 if not re.fullmatch("[a-f0-9]{64}",expect_sha256)or expect.is_symlink()or not expect.is_file()or not 1<=expect.stat().st_size<=16384:raise ValueError("INDEPENDENT_EXPECTATION_REQUIRED")
 expected_bytes=expect.read_bytes()
 if SHA(expected_bytes)!=expect_sha256:raise ValueError("PREDECLARED_EXPECTATION_SHA_CHANGED")
 expected=obj(expected_bytes)
 if set(expected)!={"format","version","run","receiver","nonce","snapshot","exporterSourceId","rawSourceId"}or expected.get("format")!="aeris-phone06-public-export-expectation"or expected.get("version")!=1 or expected.get("run")!=run:raise ValueError("EXPECTATION_CONTEXT")
 if not re.fullmatch("[A-Za-z0-9_-]{3,64}",expected["receiver"])or not re.fullmatch("[A-Za-z0-9_-]{16,96}",expected["nonce"])or not re.fullmatch("[a-f0-9-]{36}",expected["snapshot"])or any(not re.fullmatch("[a-f0-9]{64}",expected[k])for k in ["exporterSourceId","rawSourceId"]):raise ValueError("EXPECTATION_FIELDS")
 if not re.fullmatch('s[a-f0-9]{20}',run):raise ValueError('EXPECTED_RUN_REQUIRED')
 if path.is_symlink()or not path.is_file()or not 1<=path.stat().st_size<=40*2**20:raise ValueError('ZIP_BOUND')
 package=path.read_bytes()
 if package[:4]!=b'PK\x03\x04'or len(package)<22 or package[-22:-18]!=b'PK\x05\x06':raise ValueError('ZIP_ENCLOSURE')
 _,disk,cdisk,ndisk,nentries,csize,cstart,comment=struct.unpack('<4s4H2IH',package[-22:])
 if disk or cdisk or comment or ndisk!=nentries or nentries not in [3,4]or cstart+csize!=len(package)-22:raise ValueError('ZIP_CENTRAL_ENCLOSURE')
 with zipfile.ZipFile(io.BytesIO(package))as z:
  entries=z.infolist();names=[x.filename for x in entries]
  if len(names)!=len(set(names))or set(names)not in[{'manifest.json','raw.jsonl','source-meta.json'},{'manifest.json','raw.jsonl','source-meta.json','review.json'}]or sum(x.file_size for x in entries)>40*2**20 or any(x.compress_type!=zipfile.ZIP_STORED or x.flag_bits&1 or x.file_size<1 for x in entries):raise ValueError('ZIP_MEMBERS_OR_COMPRESSION')
  position=0;files={}
  for x in entries:
   if x.header_offset!=position or x.flag_bits&~0x800 or x.file_size!=x.compress_size or stat.S_IFMT(x.external_attr>>16)==stat.S_IFLNK:raise ValueError('ZIP_LOCAL_ORDER_OR_SYMLINK')
   local=struct.unpack('<IHHHHHIIIHH',package[position:position+30])
   if local[0]!=0x04034b50 or local[2]!=x.flag_bits or local[3]!=0 or local[6]!=x.CRC or local[7]!=x.compress_size or local[8]!=x.file_size or package[position+30:position+30+local[-2]].decode('utf-8')!=x.filename:raise ValueError('ZIP_LOCAL_CENTRAL_MISMATCH')
   position+=30+local[-2]+local[-1]+x.file_size;files[x.filename]=z.read(x)
  if position!=cstart:raise ValueError('ZIP_GAPS_OR_OVERLAP')
 if len(files['manifest.json'])>16384 or len(files['source-meta.json'])>2**20 or len(files.get('review.json',b''))>2**20:raise ValueError('METADATA_BOUND')
 m=obj(files['manifest.json'])
 if m.get('format')!='aeris-native96-raw'or m.get('version')!=1 or m.get('sourceAuthenticated')is not False or m.get('authorityRestorable')is not False or m.get('missionAcceptance')!='NOT_ASSERTED_BY_PACKAGE':raise ValueError('PACKAGE_CLAIM_POLICY')
 listed=m['files']
 if not isinstance(listed,list)or len(listed)!=len(files)-1 or len({x['name']for x in listed})!=len(listed):raise ValueError('MANIFEST_LIST')
 for x in listed:
  if set(x)!={'name','bytes','sha256'}or x['name']=='manifest.json'or x['name']not in files or x['bytes']!=len(files[x['name']])or x['sha256']!=SHA(files[x['name']]):raise ValueError('MEMBER_SHA')
 raw=files['raw.jsonl']
 if not 1<=len(raw)<=32*2**20:raise ValueError('RAW_BOUND')
 start=0;n=0;head='';last=-1;kind='';meta=None
 for line in raw.splitlines(keepends=True):
  if not line.endswith(b'\n'):break
  if len(line)>180001:raise ValueError('RAW_LINE_BOUND')
  match=LINE.fullmatch(line[:-1])
  if not match:raise ValueError('RAW_FORMAT')
  seq,prev,t,k,payload,digest=match.groups();seq=int(seq);t=int(t)
  if seq!=n+1 or prev.decode()!=head or t<last:raise ValueError('RAW_ORDER_CLOCK')
  data=base64.b64decode(payload,validate=True)
  if len(data)>131072 or base64.b64encode(data)!=payload:raise ValueError('RAW_DATA_BOUND')
  body=line[:-1].rsplit(b',"sha256":',1)[0]+b'}'
  if SHA(body)!=digest.decode():raise ValueError('RAW_SHA')
  n=seq;head=digest.decode();last=t;kind=k.decode();start+=len(line)
  if n==1:
   if kind!='META':raise ValueError('META_FIRST')
   meta=data
 if not n or len(raw)-start>180000 or meta!=files['source-meta.json']:raise ValueError('RAW_META_PREFIX')
 metadata=obj(meta)
 if metadata.get('ownedLaunchAssertion',{}).get('run')!=run:raise ValueError('WRONG_SELECTED_RUN')
 context=m.get('context',{})
 if set(context)!={'snapshot','run','receiver','nonce','exporterSourceId','rawSourceId','captureElapsedMs','authorityRestorable'}or any(context.get(k)!=expected[k]for k in ['snapshot','run','receiver','nonce','exporterSourceId','rawSourceId'])or context.get('authorityRestorable')is not False or type(context.get('captureElapsedMs'))is not int or context['captureElapsedMs']<0 or metadata.get('sourceId')!=expected['rawSourceId']:raise ValueError('INDEPENDENT_RECEIVER_CONTEXT_BINDING')
 extent='CLOSED_RAW'if kind=='CLOSED'and start==len(raw)else'TORN_TAIL_RETAINED'if start<len(raw)else'UNTERMINATED_PREFIX'
 expected={'extent':extent,'records':n,'head':head,'committedBytes':start,'tailBytes':len(raw)-start}
 if m['raw']!=expected:raise ValueError('RAW_MANIFEST_PREFIX')
 if 'review.json'in files:
  review=obj(files['review.json'])
  if review.get('run')!=run or review.get('rawHead')!=head or review.get('rawRecords')!=n or review.get('authorityRestorable')is not False:raise ValueError('REVIEW_RAW_BINDING')
 return {'expectationSha256':expect_sha256,'status':'PASS_PUBLIC_PACKAGE_INTEGRITY_ONLY','run':run,'packageSha256':SHA(path.read_bytes()),'raw':expected,'sourceId':metadata.get('sourceId'),'reviewIncluded':'review.json'in files,'missionAcceptance':'NOT_ASSERTED','sourceAuthenticated':False,'authorityRestorable':False,'actualPhoneAcceptance':'SEPARATE_REQUIRED','scope':'Public ZIP/SHA chain only; TLS/crew audit/manual/failsafe require separate pinned evidence'}
def main():
 a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--run',required=True);a.add_argument('--expect',type=Path,required=True);a.add_argument('--expect-sha256',required=True);args=a.parse_args()
 try:print(json.dumps(verify(args.package,args.run,args.expect,args.expect_sha256),indent=2));return 0
 except Exception as e:print(json.dumps({'status':'FAIL_PUBLIC_PACKAGE_INTEGRITY','error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
