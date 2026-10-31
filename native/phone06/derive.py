from overlay import replace_once as one

def derive(t):
 def edit(p,fn):
  f=t/p;f.write_text(fn(f.read_text()))
 def basic(s):return s.replace('NATIVE97','PHONE06').replace('NATIVE98','PHONE06')
 edit('src/Profile95.java',lambda s:s.replace('new double[]{6,16,16}','new double[]{6,0,0}'))
 edit('src/CrewGateway02.java',lambda s:one(one(s,'boolean mutation=id==44||','boolean mutation=id==69||id==44||'),' public void flightBoundary(', ' public void requirePhonePilot06()throws Exception{long at=now();active(local,at);crew.scope(local,\"aircraft\",at);if(!local.id.equals(aircraftOwner))throw new IOException(\"PHONE_PILOT_OWNER_REQUIRED\");} public void flightBoundary('))
 edit('src/DirectTransport95.java',lambda s:s.replace('"10.0.2.2",5937','"127.0.0.1",5960').replace('10.0.2.2:5937','127.0.0.1:5960'))
 edit('assets/direct95/socket.mjs',lambda s:s.replace('options.port!==5937','options.port!==5960'))
 edit('assets/direct95/controller.mjs',lambda s:s.replace('l.port=5937','l.port=5960').replace('OWNED_EMULATOR_CONTEXT_REQUIRED','EXPLICIT_PHONE_USB_SIMULATION_ADMISSION_REQUIRED'))
 edit('assets/direct95/vendor/pilot/auto63/link-v5.mjs',lambda s:s.replace('p.expected.FS_OPTIONS=16','p.expected.FS_OPTIONS=0'))
 edit('assets/direct95/vendor/app/core/vehicle-profile.mjs',lambda s:s.replace("name:'FS_OPTIONS',expected:16","name:'FS_OPTIONS',expected:0"))
 for p in ['assets/index.html','assets/sitl.html']:
  edit(p,lambda s:s.replace('initial-scale=1','initial-scale=1,viewport-fit=cover').replace('</head>','<link rel="stylesheet" href="phone06.css"></head>').replace('</body>','<script type="module" src="phone06.mjs"></script></body>').replace('CREW02 · Diễn tập','PHONE06 · SIMULATION'))
 edit('src/ResourcePolicy.java',lambda s:one(s,'Arrays.asList(','Arrays.asList("/phone06.mjs","/phone06.css","/touch06.mjs",'))
 edit('src/CrewTrust02.java',trust)
 edit('src/CrewGateway02.java',crew_saf)
 edit('src/ShellActivity.java',shell)
 edit('src/WireGate95.java',gate)
 edit('src/DirectTransport95.java',transport)
 # Explicit approved takeover remains observed and fresh; it can never satisfy AUTO completion.
 edit('assets/direct95/vendor/pilot/auto63/link-v5.mjs',lambda s:s.replace("if(m.id===0&&this.autoSeen&&m.fields.custom_mode!==3", "if(m.id===0&&this.autoSeen&&!this.phoneTakeover06&&m.fields.custom_mode!==3").replace("['AUTO','ARMED_HOME_REVIEW'].includes(this.stage)","['AUTO','ARMED_HOME_REVIEW','ASSISTED_PHONE06'].includes(this.stage)").replace('complete:!!(this.autoSeen&&!this.failure','complete:!!(this.autoSeen&&!this.phoneTakeover06&&!this.failure'))

def shell(s):
 s=one(s,'private RawSaf96 raw96;','private PhoneObserver06 observer06;private PhoneSaf06 phoneSaf06;private PhoneAdmission06 admission06;private RawSaf96 raw96;')
 s=s.replace('&&"ranchu".equals(Build.HARDWARE)','')
 s=one(s,'direct95.trace03=liveStage03;','direct95.trace03=liveStage03;admission06=new PhoneAdmission06(()->SystemClock.elapsedRealtime());direct95.admission06=admission06;observer06=new PhoneObserver06(new PhoneObserver06.Source(){public PhoneObserver06.Prefix prefix()throws Exception{return direct95.observerPrefix06();}public String capability()throws Exception{return direct95.observerCapability06();}public long now(){return SystemClock.elapsedRealtime();}});')
 s=one(s,'if(action.equals("state"))return direct95.state();','if(action.equals("state"))return direct95.state();if(action.equals("admit06")){if(!foreground||owned95==null||direct95.isOpen())throw new IOException("PHONE_OFFLINE_EXPLICIT_USB_LAUNCH_REQUIRED");return Data97.json(admission06.verify(StrictJson02.parse(owned95.toString().getBytes(StandardCharsets.UTF_8)),BuildInfo90.SOURCE_ID));}if(action.equals("manual06")){if(!foreground||owned95==null)throw new IOException("PHONE_FOREGROUND_SIMULATION_REQUIRED");return direct95.manual06(StrictJson02.parse(body.getBytes(StandardCharsets.UTF_8)));}if(action.equals("observer-start06"))return Data97.json(observer06.start());if(action.equals("observer-stop06")){observer06.close();return "{\\\"ok\\\":true}";}if(action.equals("profile06"))return direct95.readManualProfile06();')
 s=one(s,'EXPLICIT_OWNED_EMULATOR_LAUNCH_REQUIRED','EXPLICIT_OWNED_PHONE_SIMULATION_LAUNCH_REQUIRED')
 s=one(s,'bound95=meta;return direct95.open','meta.put("phoneAdmission06",admission06.snapshot());admission06.require(owned95.getString("run"),false);bound95=meta;return direct95.open')
 s=one(s,'web.addJavascriptInterface(new Bridge(),"Native82Bridge");','direct95.phoneOwner06=()->crew02.requirePhonePilot06();phoneSaf06=new PhoneSaf06(this,crew02,direct95,io,(id,body)->reply(id,body),()->foreground);web.addJavascriptInterface(new Bridge(),"Native82Bridge");')
 s=one(s,'if(action.startsWith("crew02:")){','if(action.equals("direct95:identity-export06")||action.equals("direct95:trust-import06")){try{phoneSaf06.request(id,action.substring(9));}catch(Exception e){reply(id,error(e.getMessage()));}return;}if(action.startsWith("crew02:")){')
 s=one(s,'super.onActivityResult(request,result,data);','super.onActivityResult(request,result,data);if(request==9606||request==9607){phoneSaf06.result(request,result,data);return;}')
 s=one(s,'if(crew02!=null)crew02.destroy();','observer06.destroy();direct95.destroy06();if(crew02!=null)crew02.destroy();')
 s=one(s,'foreground=true;if(diag90!=null)','foreground=true;if(phoneSaf06!=null)phoneSaf06.resume();if(diag90!=null)')
 s=one(s,'(saf91.busy()||raw96.busy())','(saf91.busy()||raw96.busy()||phoneSaf06.busy())')
 s=one(s,'foreground=false;if(crew02!=null)', 'foreground=false;observer06.close();admission06.clear();if(crew02!=null)')
 return s

def trust(s):
 start=s.index('validate(nativeCert);Map<String,Object>m=StrictJson02.parse(b);',s.index('public synchronized Map<String,Object>load()'))
 end=s.index('String h=CrewAudit02.sha(b);',start)
 validation=s[start:end]
 method='public synchronized void validateImport06(byte[]b)throws Exception{if(store==null||nativeCert==null)throw new IOException("CREW_EXPLICIT_KEY_INIT_REQUIRED");'+validation+'}'
 s=one(s,' public synchronized void current()', ' public java.nio.file.Path publicRoot06(){return root.toPath();} '+method+' public synchronized void current()')
 return s

def crew_saf(s):
 method='public String importPublicTrust06(byte[]bytes)throws Exception{requireForeground();if(transport.isOpen()||server!=null)throw new IOException("PHONE_TRUST_OFFLINE_ONLY");Map<String,Object>result=PhoneTrust06.install(trust.publicRoot06(),bytes,b->trust.validateImport06(b));synchronized(transport){record("PUBLIC_TRUST_IMPORT",result);}return json(result);} '
 return one(s,' public String local(', ' '+method+' public String local(')

def gate(s):
 s=one(s,'private boolean autoObserved01=false;', 'public final ManualPolicy06 manual06=new ManualPolicy06();private byte[]phonePayload06=null;private int phoneId06=-1;private String phoneKind06=null,phoneLease06=null;private int phoneTarget06=-1;private boolean autoObserved01=false;')
 s=one(s,'if(autoSent&&!autoObserved01', 'if(autoSent&&!manual06.takenOver()&&!autoObserved01')
 s=one(s,'if(autoSent){if(!autoObserved01)', 'manual06.observe(mode,armed,t);if(autoSent&&!manual06.takenOver()){if(!autoObserved01)')
 s=s.replace('if(Profile95.P.containsKey(name))','if(Profile95.P.containsKey(name)||ManualProfile06.P.containsKey(name))').replace('if(!Profile95.P.containsKey(name)||','if(!Profile95.P.containsKey(name)&&!ManualProfile06.P.containsKey(name)||')
 s=one(s,'if(!Arrays.asList(20,76,44,73,43,51,47).contains(id))', 'if(id==69||phoneId06==id&&phonePayload06!=null){phoneApprove06(id,p,t);return;}if(!Arrays.asList(20,76,44,73,43,51,47).contains(id))')
 s=one(s,'if(c==176&&p2!=3&&p2!=4)', 'if(c==176&&p2==3&&manual06.takenOver())fail("PHONE_NO_AUTO_RESUME");if(c==176&&p2!=3&&p2!=4)')
 s=one(s,'if(broken||!autoSent||!autoObserved01', 'if(broken||manual06.takenOver()||!autoSent||!autoObserved01')
 methods='''
 public void preparePhone06(int id,byte[]payload,String kind,String lease,int target)throws IOException{if(phonePayload06!=null)throw new IOException("PHONE_ONE_PREPARED_INTENT");phoneId06=id;phonePayload06=payload.clone();phoneKind06=kind;phoneLease06=lease;phoneTarget06=target;}
 public void manualProfile06(long n)throws IOException{tick(n);if(!crewHealthy02(n)||!version)throw new IOException("PHONE_MANUAL_FIRMWARE_OR_FRESHNESS");for(Map.Entry<String,double[]>e:ManualProfile06.P.entrySet()){int[]v=parameters.get(e.getKey());double[]q=e.getValue();if(v==null||n-parameterAt.get(e.getKey())>10000||v[0]!=(int)q[0]||Float.intBitsToFloat(v[1])<q[1]||Float.intBitsToFloat(v[1])>q[2])throw new IOException("PHONE_MANUAL_TYPED_PROFILE:"+e.getKey());}for(String name:new String[]{"FS_OPTIONS","FS_GCS_ENABLE","MAV_GCS_SYSID","FS_GCS_TIMEOUT"}){double[]q=Profile95.P.get(name);int[]v=sealed.get(name);if(v==null||v[0]!=(int)q[0]||Float.intBitsToFloat(v[1])<q[1]||Float.intBitsToFloat(v[1])>q[2])throw new IOException("PHONE_FAILSAFE_SEALED_PROFILE_REQUIRED:"+name);}}
 private void phoneApprove06(int id,byte[]p,long n)throws IOException{byte[]expected=phonePayload06;String kind=phoneKind06,lease=phoneLease06;int target=phoneTarget06;phonePayload06=null;phoneId06=-1;if(expected==null||!Arrays.equals(expected,p))fail("PHONE_UNPREPARED_CONTROL");if(id==69||target==5)manualProfile06(n);else if(!crewHealthy02(n)||!version)fail("PHONE_SAFE_MODE_FRESHNESS");if(id==69){if(kind.equals("neutral"))manual06.approveNeutral(n,crewHealthy02(n));else manual06.approveWire(phoneGeneration06,lease,n,crewHealthy02(n));}else if(id==76&&kind.equals("mode"))manual06.requestMode(target,n);else fail("PHONE_PREPARED_KIND");}
 public boolean phoneNeutral06(){return "neutral".equals(phoneKind06);}public String phoneGeneration06="";
'''
 s=one(s,' public boolean grantActive(',methods+' public boolean grantActive(')
 return s

def transport(s):
 s=one(s,'StageTrace03 trace03;', 'PhoneAdmission06 admission06;CrewCheck02 phoneOwner06;private java.util.concurrent.ScheduledFuture<?>expiry06;private final java.util.concurrent.ScheduledThreadPoolExecutor manualTimer06=new java.util.concurrent.ScheduledThreadPoolExecutor(1);StageTrace03 trace03;')
 s=one(s,'this.sink=sink;}', 'this.sink=sink;manualTimer06.setRemoveOnCancelPolicy(true);manualTimer06.scheduleAtFixedRate(()->sweepManual06(),50,50,java.util.concurrent.TimeUnit.MILLISECONDS);}')
 s=one(s,'gate=unified.flight;', 'gate=unified.flight;gate.phoneGeneration06=generation;')
 s=one(s,'if(crewGuard02!=null)crewGuard02.flightBoundary(wire,clock.now());unified.flightApprove', 'int id06=(wire[7]&255)|((wire[8]&255)<<8)|((wire[9]&255)<<16);int cmd06=id06==76?(wire[38]&255)|((wire[39]&255)<<8):0;if(id06==69||id06==44||id06==73||id06==76&&(cmd06==176||cmd06==400))admission06.require(run,id06==69&&!gate.phoneNeutral06());if(crewGuard02!=null)crewGuard02.flightBoundary(wire,clock.now());unified.flightApprove')
 s=one(s,'guard.run();approval[0]', 'admission06.require(run,false);guard.run();approval[0]')
 s=one(s,'gate.grant(clock.now());','admission06.require(run,false);gate.grant(clock.now());')
 s=one(s,'open=false;if(socket!=null)', 'open=false;manualTimer06.shutdownNow();if(gate!=null)gate.manual06.revoke(reason);if(admission06!=null)admission06.clear();if(socket!=null)')
 # Existing NativeSend98 is the sole sequence / WAL / fsync / write path.
 from pathlib import Path
 methods=(Path(__file__).parent/'fragments/transport06.inc').read_text()
 s=one(s,' public synchronized String grant(',methods+' public synchronized String grant(')
 return s
