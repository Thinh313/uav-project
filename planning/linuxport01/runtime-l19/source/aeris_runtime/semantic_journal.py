"""Cold lossless AJZ01 decoder, exact original JS UTF8 rows retained."""
from pathlib import Path
import hashlib,json,struct,zlib
MAGIC=b'AJZ01\n';MIB=2**20

def need(v,n):
 if not v:raise ValueError('AJZ_'+n)
def decode_files(paths):
 need(1<=len(paths)<=8,'SEGMENTS8');sequence=0;rowhead='';name=None;decoded=[];files=[];last_ns=-1;totalstored=0
 for ordinal,path in enumerate(paths,1):
  need(path.is_file()and not path.is_symlink()and path.stat().st_size<=8*MIB,'ORIGINAL_FILE8M');raw=path.read_bytes();totalstored+=len(raw);need(raw.startswith(MAGIC)and len(raw)>=len(MAGIC)+4,'MAGIC');h=struct.unpack_from('!I',raw,len(MAGIC))[0];at=len(MAGIC)+4+h;need(0<h<=2048 and at<=len(raw),'HEADER_BOUND');header=json.loads(raw[len(MAGIC)+4:at]);need(header.get('format')=='aeris-lossless-semantic-journal'and header.get('version')==1 and header.get('codec')=='AJZ01_DEFLATE_RAW_SYNC'and header.get('segment')==ordinal and header.get('firstSequence')==sequence+1 and header.get('previousRowSHA256')==rowhead,'HEADER_IDENTITY');name=header['name']if name is None else name;need(header['name']==name,'SAME_JOURNAL');blockhead='0'*64;compressed=[];ranges=[];plain_size=0;closed=False
  while at<len(raw):
   need(not closed and at+80<=len(raw),'TORN_PREFIX_AFTER_CLOSE');n,length,first,last=struct.unpack_from('!IIII',raw,at);need(n<=131072 and length<=65536 and at+80+n<=len(raw)and raw[at+16:at+48].hex()==blockhead,'BLOCK_BOUND_CHAIN');body=raw[at:at+48+n];head=raw[at+48+n:at+80+n].hex();need(hashlib.sha256(body).hexdigest()==head,'BLOCK_SHA');compressed.append(raw[at+48:at+48+n]);ranges.append((length,first,last));plain_size+=length;need(plain_size<=8*MIB,'DECODED_SEGMENT8M');closed=length==0
   if closed:need(first==last+1,'CLOSE_RANGE')
   else:need(first<=last,'ROW_RANGE')
   blockhead=head;at+=80+n
  need(closed,'MISSING_CLOSE');decoder=zlib.decompressobj(-15);plain=decoder.decompress(b''.join(compressed),8*MIB+1);need(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(plain)==plain_size,'DEFLATE_EOF_LENGTH');offset=0
  for size,first,last in ranges:
   if not size:need(last==sequence,'CLOSE_SEQUENCE');continue
   chunk=plain[offset:offset+size];offset+=size;need(chunk.endswith(b'\n')and first==sequence+1,'ROW_BOUNDARY')
   for line in chunk.splitlines():
    need(0<len(line)<=65536,'ROW64K');row=json.loads(line);need(row['n']==sequence+1 and row['previous']==rowhead and row['hostClockDomain']=='NODE_HRTIME_NS'and int(row['hostNs'])>=last_ns,'ROW_SEQUENCE_CLOCK_CHAIN');sequence+=1;rowhead=row['sha256'];last_ns=int(row['hostNs'])
   need(sequence==last,'ROW_COUNT_RANGE');decoded.append(chunk)
  files.append({'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'segment':ordinal,'finalBlockSHA256':blockhead})
 result=b''.join(decoded);need(len(result)<=64*MIB,'FULL_LOGICAL64M');return result,files
