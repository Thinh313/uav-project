"""Authenticated diagnostic annotations never participate in health authority.

The original error class/string and schema-before-freshness rejection order stay
unchanged. A failure envelope is always rejected, including fully bound ones.
"""
import json,threading
_lock=threading.Lock();_observed={};MAX_FAILURE=640
FORMAT='aeris-guardian-failure-diagnostic11'

def fault_envelope(binding,challenge,failure,at):
 if type(failure)is not str or not failure or type(at)is not int:raise ValueError('GUARDIAN11_FAULT_ARGUMENT')
 value={**binding,'diagnosticFormat':FORMAT,'diagnosticOnly':True,'challenge':challenge,'responseHostNs':at,'failure':failure.encode('utf8',errors='replace')[:MAX_FAILURE].decode('utf8',errors='ignore')}
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
 if len(raw)>4096:raise ValueError('GUARDIAN11_FAULT4096')
 return raw

def annotate(error,response,binding,challenge,started,ended,peer):
 """Failure-only side metadata after the ORIGINAL exchange/schema failure."""
 if type(response)is not dict or response.get('diagnosticOnly')is not True:return None
 status='UNTRUSTED_DIAGNOSTIC';reason='MALFORMED_OR_FOREIGN';failure=None
 expected=set(binding)|{'diagnosticFormat','diagnosticOnly','challenge','responseHostNs','failure'}
 if peer!=binding['pid']:reason='KERNEL_PEER_MISMATCH'
 elif type(started)is not int or type(ended)is not int or not 0<=ended-started<=100_000_000:reason='ORIGINAL_EXCHANGE_LATE_OR_UNKNOWN'
 elif set(response)!=expected or response.get('diagnosticFormat')!=FORMAT:reason='EXACT_FORMAT_OR_FIELDS'
 elif response.get('challenge')!=challenge:reason='CHALLENGE_MISMATCH'
 elif any(type(response.get(k))is not type(v)or response.get(k)!=v for k,v in binding.items()):reason='SOURCE_CAMPAIGN_BINDING_MISMATCH'
 elif type(response.get('responseHostNs'))is not int or not started<=response['responseHostNs']<=ended:reason='RESPONSE_TIME_NOT_CAUSAL'
 elif type(response.get('failure'))is not str or not response['failure']or len(response['failure'].encode('utf8'))>MAX_FAILURE:reason='FAULT_TEXT_BOUND'
 else:status='SOURCE_BOUND_DIAGNOSTIC_ONLY';reason='AUTHENTICATED_FAILURE_NOT_AUTHORITY';failure=response['failure']
 result={'status':status,'reason':reason,'failure':failure,'authority':False,'originalPrimaryClass':type(error).__name__,'originalPrimaryMessage':str(error)[:256],'peerPID':peer,'responseHostNs':response.get('responseHostNs')if type(response.get('responseHostNs'))is int else None,'exchangeElapsedNs':ended-started if type(ended)is int and type(started)is int else None}
 with _lock:
  if id(error)not in _observed:
   if len(_observed)>=16:_observed.pop(next(iter(_observed)))
   _observed[id(error)]=(error,result)
 return dict(result)

def diagnostic(error):
 """Source-owned exception identity lookup; caller attributes are not trusted."""
 with _lock:
  entry=_observed.get(id(error))
  return dict(entry[1])if entry is not None and entry[0]is error else None
