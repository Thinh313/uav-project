"""Bind explicit native post-ARM Home to a closed journal and outside-raw receipt."""
from pathlib import Path
import json,hashlib,tarfile,base64,struct,importlib.util,re
from pilot.betaintegrated01.runtime.ap_stage import canonical
from pilot.betaintegrated01.control01.mavlink import Framer
from .rx_group import RXAudit
from aeris_runtime.audit.geography import home_fields,POLICY
from aeris_runtime.paths import repository
ROOT=repository()


def descriptor_sha256(descriptor):
    body=canonical(descriptor)
    if len(body)>16384:raise ValueError('CONFIRMATION_DESCRIPTOR_BOUND')
    return hashlib.sha256(body).hexdigest()


def launch_context(context):
    keys={'run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256'}
    if type(context)is not dict or set(context)!=keys:raise ValueError('EXPECTED_LAUNCH_CONTEXT_SCHEMA')
    for key in ('run','epoch','boot','generation'):
        if type(context[key])is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,64}',context[key])is None:raise ValueError('LAUNCH_CONTEXT_IDENTIFIER')
    for key in ('operator','profileId'):
        if type(context[key])is not str or not 1<=len(context[key])<=128 or any(ord(c)<32 for c in context[key]):raise ValueError('LAUNCH_CONTEXT_LABEL')
    for key in ('binarySHA256','configSHA256'):
        if type(context[key])is not str or re.fullmatch(r'[0-9a-f]{64}',context[key])is None:raise ValueError('LAUNCH_CONTEXT_SHA256')
    return context


def input_bounds(path,prefix,anchor,context):
    launch_context(context)
    if type(path)is not str or not 1<=len(path)<=4096 or '\0'in path:raise ValueError('NATIVE_TAR_PATH_BOUND')
    if type(prefix)is not str or prefix!='files/control-runs/'+context['run']+'/':raise ValueError('EXACT_NATIVE_RUN_PREFIX_REQUIRED')
    if type(anchor)is not str or re.fullmatch(r'[0-9a-f]{64}',anchor)is None:raise ValueError('NATIVE_EXTERNAL_ANCHOR_SCHEMA')


def _closed_native(path,prefix,anchor):
    from .native_stream import closed_native
    return closed_native(path,prefix,anchor)


def create_confirmation_descriptor(nativeTarPath,prefix,nativeExternalAnchor,bracket,launchContext):
    input_bounds(str(nativeTarPath),prefix,nativeExternalAnchor,launchContext)
    cold,rows=_closed_native(nativeTarPath,prefix,nativeExternalAnchor)
    confirmations=[r for r in rows if r['kind']=='POST_ARM_HOME_EXPLICITLY_CONFIRMED']
    if len(confirmations)!=1:raise ValueError('UNIQUE_EXPLICIT_HOME_CONFIRMATION_REQUIRED')
    descriptor={'format':'aeris-native-home-confirmation-receipt','version':2,'expectedLaunchContext':dict(launchContext),'nativeTarPath':str(Path(nativeTarPath).resolve()),
                'prefix':prefix,'nativeExternalAnchor':nativeExternalAnchor,'confirmationRecordSHA256':confirmations[0]['sha256'],
                'hostBracket':bracket}
    return descriptor,descriptor_sha256(descriptor)


def verify_confirmation(descriptor,expected_anchor,run,epoch,boot):
    if descriptor_sha256(descriptor)!=expected_anchor:raise ValueError('CONFIRMATION_EXTERNAL_RECEIPT_ANCHOR')
    if type(descriptor)is not dict or set(descriptor)!={'format','version','nativeTarPath','prefix','nativeExternalAnchor','confirmationRecordSHA256','hostBracket','expectedLaunchContext'}or descriptor['format']!='aeris-native-home-confirmation-receipt'or type(descriptor['version'])is not int or descriptor['version']!=2:raise ValueError('CONFIRMATION_SCHEMA')
    context=launch_context(descriptor['expectedLaunchContext'])
    input_bounds(descriptor['nativeTarPath'],descriptor['prefix'],descriptor['nativeExternalAnchor'],context)
    if any(context[k]!=v for k,v in [('run',run),('epoch',epoch),('boot',boot)]):raise ValueError('EXPECTED_LAUNCH_CONTEXT_MISMATCH')
    if type(descriptor['confirmationRecordSHA256'])is not str or re.fullmatch(r'[0-9a-f]{64}',descriptor['confirmationRecordSHA256'])is None:raise ValueError('CONFIRMATION_RECORD_SHA_SCHEMA')
    bracket=descriptor['hostBracket']
    if type(bracket)is not dict or set(bracket)!={'beforeActionHostNs','afterObservedConfirmedHostNs','run','epoch','boot','generation','displayedHomeHash'}:raise ValueError('CONFIRMATION_BRACKET_SCHEMA')
    if any(bracket[k]!=v for k,v in [('run',run),('epoch',epoch),('boot',boot),('generation',context['generation'])]):raise ValueError('CONFIRMATION_CONTEXT')
    lo,hi=bracket['beforeActionHostNs'],bracket['afterObservedConfirmedHostNs']
    if type(lo)is not int or type(hi)is not int or not 0<=lo<=hi or hi-lo>POLICY['maximumConfirmationBracketNs']:raise ValueError('CONFIRMATION_BRACKET_CLOCK')
    cold,rows=_closed_native(descriptor['nativeTarPath'],descriptor['prefix'],descriptor['nativeExternalAnchor'])
    if cold['run']!=run or cold['epoch']!=epoch:raise ValueError('NATIVE_CONFIRMATION_CONTEXT')
    found=[];context_seen=False;provider_seen=False;context_count=0;touch_actions={};framer=Framer();last_seq=None;frame_n=0;armed=False;arm_rx=None;home_rx=None;rxGroups=RXAudit()
    for row in rows:
        kind=row['kind'];payload=base64.b64decode(row['base64'],validate=True);received=rxGroups.feed(row)
        if kind=='LIFECYCLE':
            value=json.loads(payload)
            if value.get('kind')=='OPENED':
                if any(value.get(k)!=v for k,v in [(k,context[k])for k in('run','epoch','boot','generation','operator','profileId','binarySHA256')]):raise ValueError('NATIVE_LIFECYCLE_CONTEXT')
                context_seen=True;context_count+=1
                if context_count!=1:raise ValueError('MULTIPLE_NATIVE_OPENED_EPISODES')
        if kind=='CONTROL_PROVIDER':
            provider=json.loads(payload)
            if provider_seen or not context_seen or any(provider.get(k)!=context[k]for k in('run','epoch','boot','generation','binarySHA256','configSHA256')):raise ValueError('NATIVE_PROVIDER_CONFIG_CONTEXT')
            provider_seen=True
        if kind=='OPERATOR_TOUCH_ACTION':
            action=json.loads(payload);identity=action.get('actionId')
            if type(identity)is not str or not identity or identity in touch_actions:raise ValueError('TOUCH_ACTION_ID_NOT_UNIQUE')
            touch_actions[identity]=(action,row['monotonicNs'],row['sha256'])
            if len(touch_actions)>256:raise ValueError('TOUCH_ACTION_COUNT_BOUND')
        if received is not None:
            for f in framer.feed(received['raw'],received['receiptElapsedNs']):
                if f['system']!=42 or f['component']!=1:continue
                delta=None if last_seq is None else(f['wireSequence']-last_seq)&255
                if delta==0 or delta is not None and delta>=128:continue
                last_seq=f['wireSequence'];frame_n+=1;p=f['payload']
                if f['id']==0:
                    new=bool(p[6]&128)
                    if new and not armed:arm_rx=(frame_n,received['receiptElapsedNs'])
                    armed=new
                if f['id']==242:
                    lat,lon,alt=struct.unpack_from('<iii',p)
                    home_rx=(frame_n,received['receiptElapsedNs'],home_fields({'latE7':lat,'lonE7':lon,'altMSLmm':alt,'datum':'AP_HOME_MSL_IN_SYNTHETIC_EXTERNAL_PROFILE'}))
        if kind=='POST_ARM_HOME_EXPLICITLY_CONFIRMED':
            if row['sha256']!=descriptor['confirmationRecordSHA256']:raise ValueError('UNEXPECTED_EXTRA_CONFIRMATION')
            data=json.loads(payload);home=home_fields(data['confirmedHome']);guest=[data.get(k)for k in('armObservedAtMs','postArmHomeObservedAtMs','atMs')]
            if not all(type(x)is int and x>=0 for x in guest)or not guest[0]<guest[1]<=guest[2]:raise ValueError('NATIVE_POST_ARM_HOME_ORDER')
            if not context_seen or not provider_seen or not armed or arm_rx is None or home_rx is None or not arm_rx[0]<home_rx[0]or home_rx[2]!=home:raise ValueError('NATIVE_CRC_HOME_AFTER_ARM_REQUIRED')
            if not(0<=guest[0]-arm_rx[1]//1000000<=200 and 0<=guest[1]-home_rx[1]//1000000<=200 and 0<=guest[2]-guest[1]<=3000):raise ValueError('NATIVE_HOME_APPLY_FRESHNESS')
            home_hash=hashlib.sha256(json.dumps(home,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
            if data.get('displayedHomeHash')!=home_hash or bracket['displayedHomeHash']!=home_hash:raise ValueError('DISPLAYED_HOME_HASH_NOT_RAW_HOME')
            if type(data.get('actionId'))is not str or data['actionId']not in touch_actions:raise ValueError('PRIOR_EXPLICIT_HOME_ACTION_REQUIRED')
            action,action_ns,action_sha=touch_actions[data['actionId']]
            producer,receipt=action.get('producerElapsedNs'),action.get('receiptElapsedNs')
            if (action.get('action')!='CONFIRM_HOME'or action.get('displayedHomeHash')!=home_hash
                or action.get('source')!='ANDROID_BUTTON_CLICK_NOT_NETWORK_RETIMESTAMPED'
                or type(producer)is not int or type(receipt)is not int
                or not 0<=producer<=receipt<=action_ns<=row['monotonicNs']
                or receipt-producer>1_000_000_000 or row['monotonicNs']-receipt>1_000_000_000):raise ValueError('HOME_TOUCH_PRODUCER_RECEIPT_FRESHNESS_OR_HASH')
            found.append({'home':home,'displayedHomeHash':home_hash,'nativeConfirmationRecordSHA256':row['sha256'],'nativeExternalAnchor':descriptor['nativeExternalAnchor'],
                          'hostBracketNs':[lo,hi],'nativeGuestOrdering':guest,'nativeIntegrity':cold['integrity'],'expectedLaunchContext':context,'nativeTouchActionRecordSHA256':action_sha,
                          'nativeTouchProducerElapsedNs':producer,'nativeTouchReceiptElapsedNs':receipt,
                          'scope':'EXTERNAL_LOCAL_ORCHESTRATION_BRACKET_NOT_REMOTE_AUTHENTICATION'})
    rxGroups.finish()
    if len(found)!=1:raise ValueError('UNIQUE_VERIFIED_CONFIRMATION_REQUIRED')
    return found[0]

create_confirmation_descriptor_long=create_confirmation_descriptor
