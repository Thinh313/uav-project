"""Bind explicit native post-ARM Home to a closed journal and outside-raw receipt."""
from pathlib import Path
import json,hashlib,tarfile,base64,struct,importlib.util
from pilot.betaintegrated01.runtime.ap_stage import canonical
from pilot.betaintegrated01.control01.mavlink import Framer
from .geography import home_fields,POLICY
ROOT=Path(__file__).resolve().parents[3]


def descriptor_sha256(descriptor):return hashlib.sha256(canonical(descriptor)).hexdigest()


def _closed_native(path,prefix,anchor):
    # Reuse the independently exercised prior full-chain receiver, without edits.
    source=ROOT/'planning/betaintegrated01/m1control01/qa/native_cold.py'
    spec=importlib.util.spec_from_file_location('m1_control01_native_cold_frozen',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    cold=module.native_cold_tar(path,prefix,anchor)
    table={};total=0
    with tarfile.open(path)as archive:
        for member in archive:
            if not member.isfile()or not member.name.startswith(prefix):continue
            name=member.name[len(prefix):]
            if name in table or member.size>8*2**20:raise ValueError('NATIVE_TAR_MEMBER_DUPLICATE_OR_BOUND')
            total+=member.size
            if total>16*2**20:raise ValueError('NATIVE_TAR_TOTAL_BOUND')
            table[name]=archive.extractfile(member).read()
    terminal=json.loads(table['session.json']);rows=[]
    for segment in range(terminal['segments']):
        rows.extend(json.loads(line)for line in table[f'segment-{segment:06}.jsonl'].splitlines())
    return cold,rows


def create_confirmation_descriptor(nativeTarPath,prefix,nativeExternalAnchor,bracket):
    cold,rows=_closed_native(nativeTarPath,prefix,nativeExternalAnchor)
    confirmations=[r for r in rows if r['kind']=='POST_ARM_HOME_EXPLICITLY_CONFIRMED']
    if len(confirmations)!=1:raise ValueError('UNIQUE_EXPLICIT_HOME_CONFIRMATION_REQUIRED')
    descriptor={'format':'aeris-native-home-confirmation-receipt','version':1,'nativeTarPath':str(Path(nativeTarPath).resolve()),
                'prefix':prefix,'nativeExternalAnchor':nativeExternalAnchor,'confirmationRecordSHA256':confirmations[0]['sha256'],
                'hostBracket':bracket}
    return descriptor,descriptor_sha256(descriptor)


def verify_confirmation(descriptor,expected_anchor,run,epoch,boot):
    if descriptor_sha256(descriptor)!=expected_anchor:raise ValueError('CONFIRMATION_EXTERNAL_RECEIPT_ANCHOR')
    if type(descriptor)is not dict or set(descriptor)!={'format','version','nativeTarPath','prefix','nativeExternalAnchor','confirmationRecordSHA256','hostBracket'}or descriptor['format']!='aeris-native-home-confirmation-receipt'or type(descriptor['version'])is not int or descriptor['version']!=1:raise ValueError('CONFIRMATION_SCHEMA')
    bracket=descriptor['hostBracket']
    if type(bracket)is not dict or set(bracket)!={'beforeActionHostNs','afterObservedConfirmedHostNs','run','epoch','boot','generation','displayedHomeHash'}:raise ValueError('CONFIRMATION_BRACKET_SCHEMA')
    if any(bracket[k]!=v for k,v in [('run',run),('epoch',epoch),('boot',boot)]):raise ValueError('CONFIRMATION_CONTEXT')
    lo,hi=bracket['beforeActionHostNs'],bracket['afterObservedConfirmedHostNs']
    if type(lo)is not int or type(hi)is not int or not 0<=lo<=hi or hi-lo>POLICY['maximumConfirmationBracketNs']:raise ValueError('CONFIRMATION_BRACKET_CLOCK')
    cold,rows=_closed_native(descriptor['nativeTarPath'],descriptor['prefix'],descriptor['nativeExternalAnchor'])
    if cold['run']!=run or cold['epoch']!=epoch:raise ValueError('NATIVE_CONFIRMATION_CONTEXT')
    found=[];context_seen=False;framer=Framer();last_seq=None;frame_n=0;armed=False;arm_rx=None;home_rx=None
    for row in rows:
        kind=row['kind'];payload=base64.b64decode(row['base64'],validate=True)
        if kind=='LIFECYCLE':
            value=json.loads(payload)
            if value.get('kind')=='OPENED':
                if any(value.get(k)!=v for k,v in [('run',run),('epoch',epoch),('boot',boot),('generation',bracket['generation'])]):raise ValueError('NATIVE_LIFECYCLE_CONTEXT')
                context_seen=True
        if kind=='RX':
            for f in framer.feed(payload,row['monotonicNs']):
                if f['system']!=42 or f['component']!=1:continue
                delta=None if last_seq is None else(f['wireSequence']-last_seq)&255
                if delta==0 or delta is not None and delta>=128:continue
                last_seq=f['wireSequence'];frame_n+=1;p=f['payload']
                if f['id']==0:
                    new=bool(p[6]&128)
                    if new and not armed:arm_rx=(frame_n,row['monotonicNs'])
                    armed=new
                if f['id']==242:
                    lat,lon,alt=struct.unpack_from('<iii',p)
                    home_rx=(frame_n,row['monotonicNs'],home_fields({'latE7':lat,'lonE7':lon,'altMSLmm':alt,'datum':'AP_HOME_MSL_IN_SYNTHETIC_EXTERNAL_PROFILE'}))
        if kind=='POST_ARM_HOME_EXPLICITLY_CONFIRMED':
            if row['sha256']!=descriptor['confirmationRecordSHA256']:raise ValueError('UNEXPECTED_EXTRA_CONFIRMATION')
            data=json.loads(payload);home=home_fields(data['confirmedHome']);guest=[data.get(k)for k in('armObservedAtMs','postArmHomeObservedAtMs','atMs')]
            if not all(type(x)is int and x>=0 for x in guest)or not guest[0]<guest[1]<=guest[2]:raise ValueError('NATIVE_POST_ARM_HOME_ORDER')
            if not context_seen or not armed or arm_rx is None or home_rx is None or not arm_rx[0]<home_rx[0]or home_rx[2]!=home:raise ValueError('NATIVE_CRC_HOME_AFTER_ARM_REQUIRED')
            if not(0<=guest[0]-arm_rx[1]//1000000<=200 and 0<=guest[1]-home_rx[1]//1000000<=200 and 0<=guest[2]-guest[1]<=3000):raise ValueError('NATIVE_HOME_APPLY_FRESHNESS')
            home_hash=hashlib.sha256(json.dumps(home,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            if data.get('displayedHomeHash')!=home_hash or bracket['displayedHomeHash']!=home_hash:raise ValueError('DISPLAYED_HOME_HASH_NOT_RAW_HOME')
            if type(data.get('actionId'))is not str or not data['actionId']:raise ValueError('EXPLICIT_HOME_ACTION_REQUIRED')
            found.append({'home':home,'displayedHomeHash':home_hash,'nativeConfirmationRecordSHA256':row['sha256'],'nativeExternalAnchor':descriptor['nativeExternalAnchor'],
                          'hostBracketNs':[lo,hi],'nativeGuestOrdering':guest,'nativeIntegrity':cold['integrity'],
                          'scope':'EXTERNAL_LOCAL_ORCHESTRATION_BRACKET_NOT_REMOTE_AUTHENTICATION'})
    if len(found)!=1:raise ValueError('UNIQUE_VERIFIED_CONFIRMATION_REQUIRED')
    return found[0]
