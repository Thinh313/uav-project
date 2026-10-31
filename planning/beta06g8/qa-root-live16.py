"""Root-operated TTY entry point for the unchanged frozen G8 controller."""
from pathlib import Path
import importlib.util,json,os,sys
if __name__=='__main__':
 assert len(sys.argv)==1,'ROOT_LIVE16_NO_ARGUMENTS'
 assert sys.stdin.isatty() and os.isatty(sys.stdin.fileno()),'ROOT_LIVE16_TTY_REQUIRED_BEFORE_WRITER'
 spec=importlib.util.spec_from_file_location('g8_frozen_root_controller_live16',Path(__file__).with_name('qa-root-controller.py'))
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 Controller=m.Controller;b=m.b;E=m.E;plan=m.plan
 E.mkdir(parents=True,exist_ok=True)
 with b.BoundedFile(E/'root-controller16-live.jsonl',2*2**20,kind='controller-journal')as j:
   ctl=Controller('16',journal=j);ctl.emit('NEW_PROCESS_NO_RESTORED_ANCHORS',plan=plan())
   try:
    while True:
     line=sys.stdin.buffer.readline(8193)
     if not line:break
     try:
      assert len(line)<=8192 and line.endswith(b'\n'),'COMMAND_LINE_BOUND8192_NO_PARTIAL_PARSE';v=ctl.command(json.loads(line));print(json.dumps({'ok':True,'result':v},default=str),flush=True)
     except BaseException as e:
      ctl.emit('COMMAND_REFUSED_NO_AUTOMATIC_RETRY',error=str(e));print(json.dumps({'ok':False,'error':str(e)}),flush=True)
      if len(line)>8192 or not line.endswith(b'\n'):break
   finally:ctl.close()
