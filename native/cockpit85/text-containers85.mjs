// CUA-only DOM visual audit; no page mutation or flight access.
export async function textAudit85(tab,fs,dir,label){
 const data=await tab.playwright.evaluate(()=>{
  const r=e=>{const b=e.getBoundingClientRect();return{x:b.x,y:b.y,right:b.right,bottom:b.bottom,w:b.width,h:b.height}};
  const visible=e=>{const s=getComputedStyle(e);return s.display!=='none'&&s.visibility!=='hidden'&&r(e).w>0&&(!e.closest('details:not([open])')||e.closest('summary'))};
  const failures=[];let checked=0;
  for(const e of document.querySelectorAll('button')){if(!visible(e))continue;const b=r(e),cx=b.x+b.w/2,cy=b.y+b.h/2;const at=document.elementFromPoint(cx,cy);if(!at||!(at===e||e.contains(at)))continue;
   if(e.scrollHeight>e.clientHeight+1)failures.push({kind:'BUTTON_CONTENT_OVERFLOW',id:e.id||e.textContent.trim().slice(0,60),clientHeight:e.clientHeight,scrollHeight:e.scrollHeight});
   for(const n of e.querySelectorAll('strong,small,span')){
    if(n.children.length||!n.textContent.trim()||!visible(n))continue;const a=r(n);checked++;
    if(a.x<b.x-1||a.right>b.right+1||a.y<b.y-1||a.bottom>b.bottom+1)failures.push({kind:'BUTTON_TEXT_CONTAINER_SPILL',id:e.id||e.getAttribute('aria-label')||e.textContent.trim().slice(0,50),text:n.textContent.trim(),button:b,textBox:a});
   }
  }
  for(const pair of [['.mini-view','#native-fly-controls'],['.camera-meta','#native-fly-controls'],['.mini-view','.camera-meta']]){
   const a=document.querySelector(pair[0]),b=document.querySelector(pair[1]);if(!a||!b||!visible(a)||!visible(b))continue;const x=r(a),y=r(b);if(Math.min(x.right,y.right)-Math.max(x.x,y.x)>1&&Math.min(x.bottom,y.bottom)-Math.max(x.y,y.y)>1)failures.push({kind:'LOWER_INSTRUMENT_OVERLAP',pair});
  }
  return{viewport:{width:innerWidth,height:innerHeight},theme:document.body.dataset.theme,view:document.body.dataset.view,checkedTextNodes:checked,failures};
 });await fs.writeFile(dir+'/'+label+'-text.json',JSON.stringify(data,null,2));return{label,...data};
}
