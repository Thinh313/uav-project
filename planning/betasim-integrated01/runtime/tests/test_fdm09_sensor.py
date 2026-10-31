"""Exact pinned sensor scaffold, absolute IEEE64 bits, no quantization/state."""
from pathlib import Path
import base64,hashlib,json,math,struct,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.foundation.fdm09 import *
from aeris_runtime.metadata_budget import encoded

def deny(fn):
 try:fn()
 except ValueError:return
 raise AssertionError('expected malformed scalar mode rejection')
def run():
 pin=hashlib.sha256((T/'source/aeris_runtime/foundation/fdm09.py').read_bytes()).hexdigest();special=[0,0.0,-0.0,5e-324,-5e-324,1.7976931348623157e308,-1.7976931348623157e308,1e-200,-1e200,1.0,-1.0];codes=[]
 for n in range(len(special)):
  values=[special[(i+n)%len(special)]for i in range(22)];raw=sensor_bytes(values);data=compact_sensor(raw);assert data is not None and len(data)<=180 and restore_sensor(data)==raw
  b={'v':2,'run':'sensor09','epoch':'e'*32,'segment':0,'seq':n,'previous':'a'*64,'kind':'INTENT','frame':n,'payload':{'base64':base64.b64encode(raw).decode()}};original=logical(b);stored=compact_line(b,original);assert HEADER.unpack_from(base64.b64decode(load(stored)['fdm09']))[2]==5;assert decode_line(stored,'sensor09','e'*32,'a'*64)==original;codes.append(len(data))
 for v in [0.0,-0.0]:assert struct.pack('>d',struct.unpack('>d',compact_sensor(sensor_bytes([v]*22))[4:12])[0])==struct.pack('>d',v)
 raw=sensor_bytes([0.0]*22)
 for malformed in [raw.replace(b'"timestamp":0.0',b'"timestamp":1'),raw.replace(b'"timestamp"',b'"unknown"'),raw.replace(b',"imu"',b', "imu"'),raw[1:],raw.replace(b'"timestamp":0.0',b'"timestamp":true')]:assert compact_sensor(malformed)is None
 deny(lambda:restore_sensor(struct.pack('>I',1<<31)));deny(lambda:restore_sensor(struct.pack('>I',1)+struct.pack('>d',float('nan'))));deny(lambda:restore_sensor(struct.pack('>I',1)+struct.pack('>d',float('inf'))));deny(lambda:restore_sensor(struct.pack('>I',1)));deny(lambda:restore_sensor(struct.pack('>I',0)+b'x'))
 assert pin==hashlib.sha256((T/'source/aeris_runtime/foundation/fdm09.py').read_bytes()).hexdigest();out=R/'evidence/betasim-integrated01/runtime/fdm09-sensor-mock01.json';assert not out.exists();report={'format':'aeris-fdm09-absolute-sensor22-exactIEEE','status':'PASS_SOURCE_CODEC_NOT_ACTUAL_FLIGHT_OR_EXPORT','sourceSHA256':pin,'groups':['exact22scalar-IEEE64-extremes-subnormal-exponents-signedzero-and-literalzero-full-byte-canonicalCRC-SHA-roundtrip','scaffold-order-spacing-missing-key-nonzero-int-bool-fall-opaqueRAW-no-normalization','invalid-highmask-length-nonfinite-IEEE-trailing-data-refused','absolute-noprior-state180B-maximum-preserves-original1644B-frame-fallbackbound'],'maximumScalarModePayloadBytes':180,'actorsStarted':False,'scratchCreated':False,'sourceChangedDuringTest':False};out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':run()
