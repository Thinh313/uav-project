import{MockProvider}from'/mock-provider.mjs';
const key='aeris-workbench02-MOCK-native-store';let saved=null;try{saved=JSON.parse(localStorage.getItem(key)||'null');}catch{}
const provider=new MockProvider(async body=>{const r=await fetch('/api/native/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body})});if(!r.ok)throw Error('MOCK_SEMANTIC_REFUSED');},{body:saved?.body??null,head:saved?.head??'ROOT'});
provider.receiver=r=>{if(r.ok&&r.action==='save'){try{localStorage.setItem(key,JSON.stringify({body:provider.body,head:provider.head,platform:'MOCK_NATIVE_BRIDGE',authorityRestored:false}));}catch{r.ok=false;r.error='MOCK_NATIVE_BROWSER_QUOTA_NOT_COMMITTED';delete r.result;}}window.nativeWB02Reply?.(r);};window.NativeWB02=provider;
window.addEventListener('visibilitychange',()=>{provider.foreground=!document.hidden;if(document.hidden)window.dispatchEvent(new CustomEvent('wb-native-background',{detail:{pickerOwned:false}}));});
