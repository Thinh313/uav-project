// Host companion bridge, never included in an Android APK or claimed as ART.
let fieldBootstrap01;const bootstrap01=()=>fieldBootstrap01??=(fetch('/api/bootstrap').then(r=>r.json()));
window.Native82Bridge={environment86:()=>JSON.stringify({source:'mock',hardware:'FIELD01_HOST_NOT_ANDROID',sdk:null,webview:'HOST_BROWSER',hasHostToken:false}),reportUI86:()=>{},request:(id,action,expected,body)=>bootstrap01().then(b=>fetch('/api/native82',{method:'POST',headers:{'Content-Type':'application/json','X-Field-CSRF':b.csrf},body:JSON.stringify({action,expected,body})})).then(r=>r.json()).then(r=>window.native82Result(id,JSON.stringify(r.result??r))).catch(e=>window.native82Result(id,JSON.stringify({ok:false,error:e.message})))};
window.fieldBootstrap01=bootstrap01;

for(const name of ['error','unhandledrejection'])window.addEventListener(name,()=>{if(document.body?.dataset.fieldLoading==='true')document.body.dataset.fieldMessage='Không thể nạp workspace. Tải lại để kiểm tra nguồn dữ liệu.';});
