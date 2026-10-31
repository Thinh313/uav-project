"""Closed new Android application selection, no SDK/ADB/actors or installation."""
from pathlib import Path
from types import SimpleNamespace
import copy,hashlib,json,sys
P=Path(__file__).resolve();T=P.parents[1];R=T.parents[2];sys.path[:0]=[str(T/'source'),str(R)]
from aeris_runtime.application09 import AndroidDomain09,PACKAGE,ACTIVITY,RECEIVER,ACTION,COLD_ABSENCE_SCRIPT
from aeris_runtime.android import AndroidDevice
from aeris_runtime.product_types import selected_types,is_product_probe
from aeris_runtime.product_native09 import ProductNativeProbe09
from aeris_runtime.candidate import _product_native_verify
from aeris_runtime.metadata_budget import encoded

def deny(fn):
 try:fn()
 except (ValueError,KeyError):return
 raise AssertionError('expected fixed domain refusal')
def make(cls):
 d=cls.__new__(cls);d.serial='emulator-5582';d.observer=SimpleNamespace(tag='AERIS_PRODUCT_STATUS');d.status_socket=None;d._install_authorization=None;d._fresh_domain_install_authorization=None;return d
def run():
 d=make(AndroidDomain09);old=make(AndroidDevice);groups=[]
 assert d._command_bound(['shell','am','start','-n',ACTIVITY])==2048;assert d._command_bound(['shell','am','broadcast','-a',ACTION,'-n',RECEIVER,'--es','requestNonce','a'*32])==2048;assert d._command_bound(['shell','run-as',PACKAGE,'pwd','-P'])==256
 for args in [['shell','am','start','-n',PACKAGE+'/.ProductActivity'],['shell','am','broadcast','-a',PACKAGE+'.PRODUCT_STATUS','-n',RECEIVER,'--es','requestNonce','a'*32],['shell','run-as','vn.rtr.aeris.mission','cat','files/product-observations01/status-'+('a'*32)+'.json'],['shell','am','start','-n',PACKAGE+'/.CockpitActivity']]:deny(lambda:d._command_bound(args))
 assert old._command_bound(['shell','am','start','-n','vn.rtr.aeris.mission/.ProductActivity'])==2048;deny(lambda:old._command_bound(['shell','am','start','-n',ACTIVITY]));groups.append('new-fixed-application-full-original-Java-components-and-old-status-action-sourceallowlist-legacy-branch-retained')
 deny(lambda:d._command_bound(['install','/new.apk']));d._fresh_domain_install_authorization={'APKPath':'/new.apk'};assert d._command_bound(['install','/new.apk'])==2048;deny(lambda:d._command_bound(['install','/foreign.apk']));d.serial='real-phone';deny(lambda:d._command_bound(['shell','run-as',PACKAGE,'pwd','-P']));groups.append('freshinstall-private-one-target-authorization-and-only-owned5582-no-real-device-or-arbitrarypackage')
 assert selected_types({'native':{'package':PACKAGE}})==(AndroidDomain09,ProductNativeProbe09);assert selected_types({'native':{'package':'vn.rtr.aeris.mission'}})[0]is AndroidDevice;deny(lambda:selected_types({'native':{'package':'foreign'}}));groups.append('closed-provider-factory-selects-only-two-explicit-sourcebound-packages')
 receipt=json.loads((R/'evidence/betasim-integrated01/product/native-application09-build01.json').read_bytes());archive=(R/receipt['inputArchive']).read_bytes();apk=(R/receipt['apk']).read_bytes();_product_native_verify(receipt,archive,apk)
 bad=copy.deepcopy(receipt);bad['package']='foreign';deny(lambda:_product_native_verify(bad,archive,apk));bad=copy.deepcopy(receipt);key=next(iter(bad['sourcePins']));bad['sourcePins']['native/foreign/x.java']=bad['sourcePins'].pop(key);deny(lambda:_product_native_verify(bad,archive,apk));groups.append('actual-newAPK-full11mixed-prefix-original-sourcearchive-and-packagedidentity-foreign-package-or-inputrefused')
 out=R/'evidence/betasim-integrated01/runtime/application09-source-mock01.json';assert not out.exists();paths=['application09.py','android.py','product_types.py','product_native09.py','candidate.py'];report={'format':'aeris-explicit-development-application-domain09-mock','status':'PASS_SOURCE_SELECTION_AND_ACTUAL_BUILT_ARTIFACT_BYTES_NO_DEVICE_EXECUTION','groups':groups,'sourcePins':{n:hashlib.sha256((T/'source/aeris_runtime'/n).read_bytes()).hexdigest()for n in paths},'APK_SHA256':receipt['sha256'],'actorsStarted':False,'installOrADBDispatched':False,'nativePerFilesDirGenerationCap':8,'allOriginalCounterLimitsUnchanged':True,'originalPrivateFilesPreservationActual':'NOT_CHECKED_UNTIL_OWNED_DEVICE_PREPARATION'};out.write_bytes(encoded(report));print(json.dumps(report))
if __name__=='__main__':run()
