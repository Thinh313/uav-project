// Owner-authorized JXA/CGEvent fallback for the pinned QGC desktop test only.
ObjC.import('CoreGraphics');
function run(args) {
 const field=args[0]==='field';if((field&&(args.length!==4||!Number.isFinite(Number(args[3]))))||(!field&&(args.length<3||args.length%2!==1||args[0]!=='click')))throw Error('Usage: click globalX globalY');
 const points=[];for(let i=1;i<(field?3:args.length);i+=2){const x=Number(args[i]),y=Number(args[i+1]);if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||y<0)throw Error('Invalid point');points.push({x:x,y:y});}
 const q=Application('QGroundControl');const proc=Application('System Events').processes.byName('QGroundControl');if(!proc.frontmost()){q.activate();delay(.4);}
 const bounds=proc.windows[0].position(),size=proc.windows[0].size();if(points.some(p=>p.x<bounds[0]||p.y<bounds[1]||p.x>=bounds[0]+size[0]||p.y>=bounds[1]+size[1]))throw Error('Point outside QGC window; re-observe before input');
 for(const point of points){const x=point.x,y=point.y;for(const type of [$.kCGEventMouseMoved,$.kCGEventLeftMouseDown,$.kCGEventLeftMouseUp]){const e=$.CGEventCreateMouseEvent(null,type,{x:x,y:y},$.kCGMouseButtonLeft);$.CGEventSetIntegerValueField(e,1,1);$.CGEventPost($.kCGHIDEventTap,e);delay(.06);}delay(.3);}
 if(field){const se=Application('System Events');se.keystroke('a',{using:'command down'});se.keystroke(args[3]);se.keyCode(36);delay(.3);}
 return JSON.stringify({app:'QGroundControl',action:args[0],points:points,time:new Date().toISOString()});
}
