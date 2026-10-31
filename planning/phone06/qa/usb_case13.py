from pathlib import Path
import sys,json,hashlib,importlib.util,datetime
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];E=R/'evidence/phone06-qa';freeze=R/'evidence/phone06/builder/source-ready04.json';q=json.loads(freeze.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p,h in q['files'].items():assert sha(R/p)==h,p
path=R/'planning/phone06/entrypoint.py';spec=importlib.util.spec_from_file_location('qa_phone_entry04',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);calls=[]
def command(args):
 calls.append(args)
 assert args==['adb','devices','-l'],'NO_OTHER_COMMAND_ALLOWED'
 return 'List of devices attached\nqa-device-73c92 device usb:4-3 product:qa model:QA transport_id:37'
m.command=command;error=None
try:m.usb_proof06('qa-device-73c91')
except ValueError as x:error=str(x)
assert error=='USB_EXACT_AUTHORIZED_ROW_REQUIRED'and calls==[['adb','devices','-l']]
for p,h in q['files'].items():assert sha(R/p)==h,p
out={'at':datetime.datetime.now().astimezone().isoformat(),'id':'PQ13','status':'PASS_SCOPED_HOST_FUNCTION','sourceFreeze':'evidence/phone06/builder/source-ready04.json','sourceFreezeSha256':sha(freeze),'actualModuleSha256':sha(path),'input':{'selectedSerial':'qa-device-73c91','enumeratedOtherSerial':'qa-device-73c92'},'refusal':error,'injectedCommands':calls,'actualCommands':0,'limits':['Only exact-row wrong-selected-serial branch executed','No ADB process, device, USB mapping, amstart, resourceadmission, or actualcleanup execution','Cleanup and serial/network refusal branches source-reviewed, not claimed dynamically covered']}
(E/'usb-heldout04.json').open('x').write(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
