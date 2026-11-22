"""Explicit selected H7 transport schema; never fallback from an old-reader error."""
from pathlib import Path
import json,hashlib
from .paths import PACKAGE_ROOT,repository
from planning.betarc01.tar_profile_h7 import reader
PROFILE=reader.PROFILE
def profile():
 v=json.loads((PACKAGE_ROOT/'assets/native-tar-profile-h7.json').read_bytes());need(v.get('profile')==PROFILE and v.get('version')==1,'PROFILE')
 for k in('pythonReader','nodeReader'):
  row=v[k];p=repository()/row['path'];need(p.is_file()and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],'SELECTED_SOURCE')
 need(all(v.get(k)==n for k,n in {'receiverRawLimitBytes':192*2**20,'currentNativeProducerRawLimitBytes':64*2**20,'legacyProducerRawLimitBytes':168*2**20,'logicalLimitBytes':512*2**20,'entryLimit':8192,'pathUTF8LimitBytes':240,'derivedViewCreated':False,'originalCaptureVersion':1}.items()),'EXACT_LAYER_BOUNDS');need(v['pythonReader']['path']=='planning/betarc01/tar_profile_h7/reader.py'and v['nodeReader']['path']=='planning/betarc01/tar_profile_h7/native-tar.mjs','EXACT_READERS');return v
def need(v,n):
 if not v:raise ValueError('H7_PROFILE_'+n)
def validate_tar_shape(path):
 profile();return reader.validate_tar_shape(path)
def observe(path):
 return {'selection':profile(),**reader.observation(reader.scan(path))}
def native_tar(*args,**kwargs):
 profile();return reader.native_tar(*args,**kwargs)
