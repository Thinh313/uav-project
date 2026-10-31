"""Source-envelope and cross-channel ordering edge tests, no services."""
from pathlib import Path
import sys,json,copy,hashlib
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control05.bootstrap import StartupEnvelope
from pilot.betaintegrated01.control05.audit import audit_transport
from pilot.betaintegrated01.control05.native_release import wire_release_observations
from pilot.betaintegrated01.control05.transport import PassiveStartup
from pilot.betaintegrated01.control01.mavlink import Framer,FramingError

def main():
 cases=[]
 def check(n,v):assert v,n;cases.append({'case':n,'status':'PASS'})
 for pairs in range(4):
  envelope=StartupEnvelope();classified=[];out=b''
  for i,c in enumerate(b'0 '*pairs+b'\xfd'):
   raw,p=envelope.feed(bytes([c]),i*10_000_000);out+=raw;classified+=p
  check('fragmented_exact_pairs_'+str(pairs),out==b'\xfd'and len(classified)==pairs and envelope.mav_started)
 for name,raw in [('unknown',b'hello'),('orphan20',b' '),('fourpairs',b'0 '*4),('wrongpair',b'0!'),('prefixhalf_thenmagic',b'0\xfd')]:
  try:StartupEnvelope().feed(raw,1);raise AssertionError('MUST_REJECT:'+name)
  except ValueError:cases.append({'case':name,'status':'PASS'})
 e=StartupEnvelope();e.feed(b'0',1);check('incomplete_boundary200ms',e.feed(b' ',200_000_001)[1][0]['pair']==1)
 e=StartupEnvelope();e.feed(b'0',1)
 try:e.feed(b' ',200_000_002);raise AssertionError('OVER200MS')
 except ValueError:cases.append({'case':'incomplete_over200ms','status':'PASS'})
 e=StartupEnvelope();e.feed(b'0 ',1);check('calibration_delay_after_completepair_is_not_incompletebyte_timeout',e.feed(b'\xfd',3_000_000_000)[0]==b'\xfd')
 e=StartupEnvelope();e.feed(b'\xfd',1);check('lateprefix_not_reclassified',e.feed(b'0 ',2)==(b'0 ',[]))
 # Live and cold strict Framer own late nonMAV byte refusal; envelope never skips it.
 try:Framer().feed(b'0 ',2);raise AssertionError('STRICTFRAMER_MUST_REJECT')
 except FramingError:cases.append({'case':'strict_framer_still_rejects_nonMAV','status':'PASS'})
 startup=PassiveStartup();startup.begin(0);startup.receive(b'0 ')
 try:startup.eof(1);raise AssertionError('PREFIXEOF_MUST_BE_FATAL')
 except RuntimeError:cases.append({'case':'EOF_after_prefix_is_terminal_not_startup_retry','status':'PASS'})
 try:startup.check(20_000_000_001);raise AssertionError('PREFIX_MUST_NOT_DISABLE20S_FIRSTMAV_BOUND')
 except RuntimeError:cases.append({'case':'prefix_doesnot_disable20s_initialMAV_bound','status':'PASS'})
 base=R/'evidence/betaintegrated01-m1control02/host/startup05-mock01/initial-eof-then-valid'
 result=json.loads((base/'transport-result.json').read_text());wire=audit_transport(base,'run-initial-eof-then-valid','epoch-initial-eof-then-valid','boot-initial-eof-then-valid',expected_anchor=result['commitAnchor'])
 check('cold_exact_raw_startup_classification',wire['startupResetPairsClassified']==3 and wire['startupRawBytesRetained']==6)
 def cmd(t,k,**x):return {'hostNs':int(t*1e9),'kind':k,**x}
 # Passive HB17 comes after neutral on hostclock. Native RX17 precedes neutral
 # in the guest journal. Comparing these unrelated clocks would be a falsefail.
 cmds=[cmd(1,'RC_OVERRIDE',channels=[1500,1475]+[65535]*16,forwardPitchHeld=True),cmd(2,'SET_MODE',mode=17,wireSHA256='b'),cmd(3,'RC_OVERRIDE',channels=[1500]*4+[65535]*14,forwardPitchHeld=False,wireSHA256='n'),cmd(3.1,'RC_OVERRIDE',channels=[0]*8+[65534]*10,forwardPitchHeld=False,wireSHA256='r'),cmd(5,'SET_MODE',mode=9,wireSHA256='l')]
 states=[cmd(3.5,'heartbeat',mode=17,armed=True)]
 w={'nativeForwardedTimeline':cmds,'passiveTimeline':states};tx={'b':[(10,10**12)],'n':[(20,10**12+200_000_000)],'r':[(21,10**12+210_000_000)],'l':[(30,10**12+500_000_000)]};modes=[(15,10**12+100_000_000,'crcMode17SHA')]
 check('dual_channel_phase_positive_no_absolute_clock_comparison',wire_release_observations(w,tx,modes)['status']=='HOST_NATIVE_RELEASE_WITNESS_PASS')
 for name,change in [('ACKonly',lambda ww,tt,mm:mm.clear()),('native_mode_after_neutral',lambda ww,tt,mm:mm.__setitem__(0,(22,10**12+100_000_000,'x'))),('stale_native_mode',lambda ww,tt,mm:mm.__setitem__(0,(15,10**12-2_000_000_000,'x'))),('wrong_wire_bytes',lambda ww,tt,mm:tt.pop('n')),('passive_mode_afterLAND',lambda ww,tt,mm:ww['passiveTimeline'][0].update(hostNs=6_000_000_000)),('native_reordered_cleanup',lambda ww,tt,mm:tt.__setitem__('r',[(19,10**12+210_000_000)]))]:
  ww,tt,mm=copy.deepcopy((w,tx,modes));change(ww,tt,mm);check(name,wire_release_observations(ww,tt,mm)['status']=='HOST_NATIVE_RELEASE_NOT_READY')
 out=R/'evidence/betaintegrated01-m1control02/host/control05-mock01';out.mkdir()
 (out/'results.json').open('x').write(json.dumps({'status':'PASS_BUILDER_CONTROL05_MOCK','groups':len(cases),'cases':cases,'APStarts':0,'realSocketsCreated':0,'scope':'Protocolstartupclassification+coldraw+purecrosschannelwitness; nativelease/consent remains independent'},indent=2)+'\n');print(json.dumps({'status':'PASS','groups':len(cases)}))
if __name__=='__main__':main()
