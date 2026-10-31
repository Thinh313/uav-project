"""Separate upstream AUTOPILOT_VERSION and raw typed parameter oracles."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import importlib.util
import json
import struct
import math
import hashlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'evidence/firmware38'
def library(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);assert not m.MAVLINK_IGNORE_CRC;return m
fw=library('fw38oracle',HERE/'oracle-version.py')
if len(sys.argv)==1:
 vectors=[]
 for i,cap in enumerate([0,24582,155652,24596,2**60+24582,2**64-1,2**53+1,131072]):
  fields={'capabilities':cap,'flight_sw_version':67568127,'middleware_sw_version':0,'os_sw_version':0,'board_version':38,'flight_custom_version':[77,79,67,75,48,48,51,56],'middleware_custom_version':[0]*8,'os_custom_version':[0]*8,'vendor_id':0,'product_id':38,'uid':2**64-1 if i==5 else 380001,'uid2':[0]*18}
  m=fw.MAVLink_autopilot_version_message(**fields);sender=fw.MAVLink(None,srcSystem=1,srcComponent=1);sender.seq=i;raw=m.pack(sender);parsed=fw.MAVLink(None).parse_char(raw);expected=parsed.to_dict();expected.pop('mavpackettype');expected['capabilities']=str(expected['capabilities']);expected['uid']=str(expected['uid']);fields['capabilities']=str(fields['capabilities']);fields['uid']=str(fields['uid']);vectors.append({'fields':fields,'meta':{'system':1,'component':1,'seq':i},'rawHex':raw.hex(),'expected':expected})
 with (OUT/'oracle-vectors.json').open('x') as f:json.dump({'vectors':vectors,'oracleSha256':hashlib.sha256((HERE/'oracle-version.py').read_bytes()).hexdigest()},f,indent=2);f.write('\n')
 print('8 upstream uint64/version vectors generated; no network')
else:
 common=library('common37oracle',ROOT/'pilot/mavflight37/oracle.py');data=json.loads((OUT/sys.argv[1]).read_text());results=[]
 for row in data['vectors']:
  raw=bytes.fromhex(row['rawHex']);lib=fw if row['kind']=='VERSION' else common;passed=False
  try:
   m=lib.MAVLink(None).parse_char(raw)
   if row['kind']=='VERSION':
    parsed=m.to_dict();parsed.pop('mavpackettype');parsed['capabilities']=str(parsed['capabilities']);parsed['uid']=str(parsed['uid']);passed=parsed==row['expected']
   else:
    payload=raw[10:-2];value_type=payload[24];float_value=struct.unpack('<f',payload[:4])[0]
    if value_type==9: value=float_value
    elif row['encoding']=='BYTEWISE':value=struct.unpack({1:'<B',2:'<b',3:'<H',4:'<h',5:'<I',6:'<i'}[value_type],payload[:{1:1,2:1,3:2,4:2,5:4,6:4}[value_type]])[0]
    else:value=float_value
    passed=m.get_msgId()==22 and value==row['expected']
  except Exception as e:passed=False
  results.append({'kind':row['kind'],'pass':passed})
 n=1
 while (OUT/f'oracle-check{n}.json').exists():n+=1
 report={'status':'PASS' if all(r['pass'] for r in results) else 'FAIL','checks':len(results),'results':results,'inputSha256':hashlib.sha256((OUT/sys.argv[1]).read_bytes()).hexdigest(),'oracleHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'oracle-version.py',ROOT/'pilot/mavflight37/oracle.py']},'networkSent':False}
 with (OUT/f'oracle-check{n}.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({'status':report['status'],'checks':report['checks']}));assert report['status']=='PASS'
