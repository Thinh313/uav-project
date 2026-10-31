from pathlib import Path
R=Path(__file__).resolve().parents[2];D=R/'pilot/missionbeta01'
def edit(p,a,b):
 s=p.read_text();assert s.count(a)==1,(str(p),a[:70],s.count(a));p.write_text(s.replace(a,b))
p=D/'link.mjs'
edit(p,"this.stage='DISARMED';}","this.stage='DISARMED';this.expectedOperatorMode=null;this.operatorReturned=false;}")
edit(p,"['AUTO','ARMED_HOME_REVIEW'].includes(this.stage)","['AUTO','ARMED_HOME_REVIEW','HOLD','RETURNING'].includes(this.stage)")
edit(p,"m.fields.custom_mode!==3&&(m.fields.base_mode&128)","m.fields.custom_mode!==3&&m.fields.custom_mode!==this.expectedOperatorMode&&(m.fields.base_mode&128)")
anchor=' completion(){'
methods=""" async readResumePolicy(){const sent=this.now();this.send(20,this.target({param_id:'MIS_RESTART',param_index:-1}));await this.until(()=>this.extra.MIS_RESTART?.at>=sent,1800);const p=this.extra.MIS_RESTART;if(p.param_type!==2||p.param_value!==0)throw Error('MIS_RESTART_TYPED_ZERO_REQUIRED');this.record('RESUME_POLICY_OBSERVED',{paramId:'MIS_RESTART',type:p.param_type,value:p.param_value,at:p.at});}
 async control(action,d){this.confirm(d);this.fresh();if(!this.autoSeen||this.snapshot().armed!==true||this.failure)throw Error('ACTIVE_AIRBORNE_AUTO_REQUIRED');if(!['pause','resume','rtl'].includes(action))throw Error('CONTROL_ACTION');if(action==='pause'&&this.stage!=='AUTO'||action==='resume'&&this.stage!=='HOLD'||action==='rtl'&&!['AUTO','HOLD'].includes(this.stage))throw Error('CONTROL_STAGE');if(action==='resume')await this.readResumePolicy();const name={pause:'hold',resume:'auto',rtl:'rtl'}[action],mode={pause:5,resume:3,rtl:6}[action];this.expectedOperatorMode=mode;this.record('MODE_CONTROL_INTENT',{action,mode,session:this.sessionId,boot:this.boot,missionSha256:this.plan.missionSha256});try{await this.command(name);this.fresh();if(this.snapshot().modeId!==mode)throw Error('MODE_NOT_OBSERVED');this.stage={pause:'HOLD',resume:'AUTO',rtl:'RETURNING'}[action];if(action==='rtl')this.operatorReturned=true;this.record('MODE_CONTROL_OBSERVED',{action,mode,armed:this.snapshot().armed,ackAloneNotExecution:true,session:this.sessionId,boot:this.boot});return this.view63();}catch(e){this.failure??='MODE_CONTROL_UNKNOWN:'+e.message;this.socket?.destroy();throw e;}}
 safeReturn(){const c=this.completion();return this.operatorReturned&&!this.failure&&c.groundDisarmed&&c.nearHome&&this.freshness(0,1500)&&this.freshness(33,1500)&&this.freshness(245,1500);}
"""
edit(p,anchor,methods+anchor)
p=D/'actual-transport.mjs';edit(p,"from'../beta06g17/flight/qualified/link.mjs'","from'./link.mjs'")
p=D/'mock-transport.mjs'
edit(p,"  source=source.replace(/from", "  source=source.replace(\"from'./link.mjs'\",'from '+JSON.stringify(new URL('./link.mjs',import.meta.url).href));\n  source=source.replace(\"WP_SPD:9}\",\"WP_SPD:9,MIS_RESTART:2}\");\n  source=source.replace(\"if(f.command===176&&f.param2===3)this.fly();\",\"if(f.command===176&&f.param2===3&&!this.flying){this.flying=true;this.fly();}if(f.command===176&&f.param2===6)this.returnHome();\");\n  source=source.replace(\"if(!this.writable)return;this.packet(42\",\"while(this.writable&&this.mode===5)await new Promise(r=>setTimeout(r,20));if(!this.writable||this.mode===6)return;this.packet(42\");\n  source=source.replace(\" destroy(){\",\" async returnHome(){await new Promise(r=>setTimeout(r,150));if(!this.writable)return;this.position={lat:this.home.lat,lon:this.home.lon,height:0};this.armed=false;this.telemetry();}\\n destroy(){\");\n  source=source.replace(/from")
p=D/'session.mjs'
edit(p,"else if(action==='close'){need(active.link.completion().complete,'OBSERVED_GROUND_DISARM_NAV_REQUIRED');return end(active.mode==='sitl'?'SITL_NOMINAL':'MOCK_NOMINAL',true);}","else if(['pause','resume','rtl'].includes(action)){authorityRequired(q);result=await active.link.control(action,confirm());}\n  else if(action==='close'){const complete=active.link.completion().complete;need(complete||active.link.safeReturn(),'OBSERVED_GROUND_DISARM_NAV_REQUIRED');return end(complete?(active.mode==='sitl'?'SITL_NOMINAL':'MOCK_NOMINAL'):'OPERATOR_RTL_INCOMPLETE',complete);}")
p=D/'client-fence.mjs'
edit(p,"close:owned&&f?.completion?.complete===true","pause:owned&&!!f?.authority&&live?.stage==='AUTO',resume:owned&&!!f?.authority&&live?.stage==='HOLD',rtl:owned&&!!f?.authority&&['AUTO','HOLD'].includes(live?.stage),close:owned&&(f?.completion?.complete===true||live?.operatorReturnSafe===true)")
edit(p,"AUTO:'AUTO'","AUTO:'AUTO',HOLD:'Giữ vị trí',RETURNING:'Đang quay về'")
p=D/'link.mjs';edit(p,"stage:this.stage,homeReview:","stage:this.stage,operatorReturnSafe:this.operatorReturned&&!this.failure&&s.armed===false&&this.freshness(245,1500)&&this.samples[245]?.fields.landed_state===1&&!!s.position&&Math.hypot((s.position.lat-HOME.lat)*111319,(s.position.lon-HOME.lon)*109300)<5,homeReview:")
p=D/'beta-client.mjs'
edit(p,'<button id="b-close">Đóng vào review</button>','<button id="b-close">Đóng vào review</button></div><div class="beta-grid"><button id="b-pause">Giữ vị trí</button><button id="b-resume">Tiếp tục nhiệm vụ</button><button id="b-rtl">Quay về Home</button>')
edit(p,"bind('#b-close',async()=>","for(const a of['pause','resume','rtl'])bind('#b-'+a,()=>flight(a));\n  bind('#b-close',async()=>")
edit(p,"['connect','preflight','grant','upload','arm','auto','close']","['connect','preflight','grant','upload','arm','auto','pause','resume','rtl','close']")
p=D/'media-panel.mjs'
s=p.read_text().replace('length===3','length===6').replace('length!==3','length!==6').replace('length<3','length<6').replace("'/3'","'/6'").replace('3 cửa sổ','6 cửa sổ').replace('3 báo cáo','6 báo cáo').replace('THREE_WINDOWS_REQUIRED','SIX_WINDOWS_REQUIRED');p.write_text(s)
p=D/'auto-video.mjs';edit(p,"reports.length===3,'THREE_RAW_WINDOWS'","reports.length===6,'SIX_RAW_WINDOWS'")
edit(p,"{autoCommand=t;start=t;}","{autoCommand??=t;start??=t;}")
p=D/'package.mjs';p.write_text(p.read_text().replace('aeris-beta05-diagnostic-package','aeris-missionbeta01-diagnostic-package'))
# Successor analyzer binds the new package receiver, preserving prior algorithm semantics.
p=R/'pilot/coach01/core.mjs';s=p.read_text().replace("from '../betaworkbench05/package.mjs'","from './package.mjs'")
# Relative imports differ only for workbench sibling; preserve all existing root/app imports.
s=s.replace("from '../workbench", "from '../workbench").replace("COACH01_REFERENCE_V2","MISSIONBETA01_REFERENCE_V1");(D/'analysis.mjs').write_text(s)
