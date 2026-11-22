"""Shared strict JSON payload decoder; no runtime effects or permissive constants."""
import json

def _pairs(items):
 d={}
 for k,v in items:
  if k in d:raise ValueError('DUPLICATE_NATIVE_JSON_KEY')
  d[k]=v
 return d

def strict_json(raw):return json.loads(raw,object_pairs_hook=_pairs,parse_constant=lambda v:(_ for _ in()).throw(ValueError('NONFINITE_NATIVE_JSON')))
