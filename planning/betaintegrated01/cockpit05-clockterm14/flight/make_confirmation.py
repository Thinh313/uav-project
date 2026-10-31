"""Root-only05 confirmation from selected160MiB long receiver, no legacy smalltar import."""
from pathlib import Path
import argparse,json,sys
from importlib import import_module
R=Path(__file__).resolve().parents[4];sys.path.insert(0,str(R))
H='planning.betaintegrated01.cockpit05-clockterm14.flight'
capture=import_module(H+'.capture_external');receiver=import_module(H+'.receiver05');contract=import_module(H+'.contract')


def make(case='actual-combined01'):
    contract.validate_release()
    if case not in('actual-short01','actual-combined01'):raise ValueError('SELECTED05_CASE_ONLY')
    C=R/contract.EVIDENCE/case/'control';read=capture.read
    if not(C/'confirm-home-bracket.json').is_file():raise ValueError('HOME_NOT_OBSERVED_NO_DESCRIPTOR_CREATED_USE_CLOSED_FAILURE_IF_FAILED')
    ext=read(C/'external-anchors.json');location=read(C/'native-export-location.json');binding=read(C/'launch-binding.json');bracket=read(C/'confirm-home-bracket.json');package=read(C/'installed-package-observation.json')
    path=Path(location['path'])
    if path.resolve()!= (C/'native-private.tar').resolve()or path.stat().st_size>168*2**20 or contract.sha(path)!=location['sha256']:raise ValueError('SELECTED05_NATIVE_EXPORT_OUTSIDE_SHA')
    context={k:binding[k]for k in('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')};native=ext['nativeClosedCheckpoint']
    descriptor,anchor=receiver.make_confirmation(path,'files/control-runs/'+binding['run']+'/',native['journal']['commitAnchor'],bracket,context,packageObservation=package)
    capture.write_metadata(C/'native-confirmation-descriptor.json',descriptor)
    capture.write_metadata(C/'native-confirmation-external-anchor.json',{'canonicalSHA256':anchor,'basis':'RootLiveClockTerm14PackageAPK/source+postARMactionbracket+closednativeexternalcheckpoint+launchbinding','nativeTarSHA256':location['sha256'],'nativeFirstFailure':native.get('firstFailure'),'doesNotOverrideClosureFailure':True,'selectedClockTerm14SourceSHA256':contract.SOURCE_SHA256})
    return {'case':case,'descriptorAnchor':anchor,'scope':'LOCAL_ROOT_ORCHESTRATION_NOT_REMOTE_AUTH','nativeFailureRetained':native.get('firstFailure')}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('case',nargs='?',default='actual-combined01');args=parser.parse_args();print(json.dumps(make(args.case)))
