"""Contractor outside-raw confirmation binding from closed actual/native parent anchors."""
import sys,json,hashlib,os
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from pilot.betaintegrated01.control04.confirmation import create_confirmation_descriptor

def main():
    attempt=sys.argv[1];assert attempt in ('02','03')
    C=R/'evidence/betaintegrated01-m1control02'/('actual-nominal'+attempt)/'control'
    ext=json.loads((C/'external-anchors.json').read_text());location=json.loads((C/'native-export-location.json').read_text());binding=json.loads((C/'launch-binding.json').read_text());bracket=json.loads((C/'confirm-home-bracket.json').read_text())
    tar=Path(location['path']);assert hashlib.sha256(tar.read_bytes()).hexdigest()==location['sha256']
    native=ext['nativeClosedCheckpoint'];assert native['closed']and native['journal']['commitAnchor']
    context={k:binding[k]for k in ('run','epoch','boot','generation','operator','profileId','binarySHA256','configSHA256')}
    descriptor,anchor=create_confirmation_descriptor(tar,'files/control-runs/'+binding['run']+'/',native['journal']['commitAnchor'],bracket,context)
    for p,d in [(C/'native-confirmation-descriptor.json',descriptor),(C/'native-confirmation-external-anchor.json',{'canonicalSHA256':anchor,'basis':'RootbeforeActionandafterObservedConfirmationbracket+closednativeexternalcheckpoint+launchbinding','nativeTarSHA256':location['sha256'],'nativeFirstFailure':native['firstFailure'],'doesNotOverrideClosureFailure':True})]:
        with p.open('x')as f:json.dump(d,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps({'attempt':attempt,'descriptorAnchor':anchor,'nativeFirstFailure':native['firstFailure'],'binding':'LOCAL_ROOT_ORCHESTRATION_NOT_REMOTE_AUTH'}))
if __name__=='__main__':main()
