"""Generate a proposed, non-executing campaign contract and readable HTML from local sources."""
from pathlib import Path
import json,hashlib,subprocess,datetime,re,html
R=Path(__file__).resolve().parents[2];P=R/'planning/beta-campaign01';E=R/'evidence/beta-campaign01';D=R/'delivery'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sourceNames=['docs/PROJECT-STATUS-2026-10-26.md','planning/product-standard01/BASELINE.md','delivery/COMPLETION-MISSIONBETA01.md','delivery/COMPLETION-BETA-VIDEO03.md','delivery/COMPLETION-CREW02.md','delivery/COMPLETION-SIM-STABILITY03.md','evidence/simstability03/qualification-final01.json','evidence/codebase-scan-20261026/scan01.json','snapshots/simstability03/overlay.json']
inputs=[{'path':n,'sha256':sha(R/n),'bytes':(R/n).stat().st_size,'provenance':'RETAINED_LOCAL_REPORT_NOT_RERUN'}for n in sourceNames]
sources=[
 ('S01','DJI Matrice400 product announcement','https://www.dji.com/matrice-400','Publisher claims: terrain-follow, POI/SmartTrack and automated routes; no AERIS comparative test. Official search result inspected; full product-page access varied by locale.'),
 ('S02','ArduPilot simulation architecture','https://ardupilot.org/dev/docs/simulation-2.html','FDM consumes firmware outputs and returns simulated sensor/vehicle state; supports choice of closed-loop architecture.'),
 ('S03','ArduPilot JSON interface','https://ardupilot.org/dev/docs/sitl-with-JSON.html','External physics interface; no fidelity or real-time guarantee implied.'),
 ('S04','MAVLink mission protocol','https://mavlink.io/en/services/mission.html','Plan transfer, ACK/error and bounded reliable protocol semantics; application readback/execution gates remain separate.'),
 ('S05','MAVLink camera v2','https://mavlink.io/en/services/camera.html','Camera discovery and capture messages; actual files/coordinates still need source evidence.'),
 ('S06','MAVLink gimbal v2','https://mavlink.io/en/services/gimbal_v2.html','Manager/device identity and addressing, control configuration; no vendor SDK support inferred.'),
 ('S07','MAVLink command protocol','https://mavlink.io/en/services/command.html','Reliable delivery and ACK; application uncertainty/idempotency must be classified.'),
 ('S08','Android touch target guidance','https://developer.android.com/guide/topics/ui/accessibility/views/apps-views','48dp touch target and purpose labels; reference guidance, not entire cockpit certification.'),
 ('S09','W3C contrast minimum','https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html','4.5:1 normal text /3:1 large text; guidance used for presentation QA, no full conformity claim.'),
 ('S10','Android ANR documentation','https://developer.android.com/topic/performance/issues/anr','Main-thread responsiveness reference; actual deadlines/metrics are profile-dependent engineering targets.')]
milestoneRows=[
 ('M0','Release baseline',[ ],[1,2],'Chief Architect + integration owner','Khóa product line, cấu hình, dependency, corpus, budget và current defects','Dependency closure/pins/license/preflight install plan hợp lệ; missing-path disposition rõ; không đổi frozen'),
 ('M1','Flight runtime bền vững',['M0'],[3,5],'Flight/simulation owner','Manual/assisted và session/recorder/restart đúng','Recorder không tràn trong30min; closed timer bất biến; full frames/fsync; actual link/AP reboot và neutral takeover đạt'),
 ('M2','Mission workbench',['M1'],[3,5],'Mission/geo owner','Lập và thực hiện polygon/corridor/inspection/search trong cùng cockpit','KML/QGC semantic oracle + geo/Home/upload/readback; AUTO/Hold/resume/RTL/review đạt'),
 ('M3','Payload, video và crew',['M1'],[4,6],'Payload/media owner','Hai operator,4 peer payload và file ảnh geotag','Same-release task đồng thời video/capture/flight; đúng route/lease, lost-link/reboot, geotag và SAF receiver'),
 ('M4','Simulator và cockpit',['M1'],[4,6],'Simulation/UX owner','Diễn tập bằng3D/audio/môi trường và UX có thể dùng','FID2/corpus/ground-truth; media stale/audio capture; all-screen visual/input and formative human gate'),
 ('M5','Qualification release',['M2','M3','M4'],[4,6],'Independent QA + release owner','Một bộ APK/host vượt campaign tích hợp','Toàn MUST pass, same release/config,18 polygon/corridor nominals + các nhóm khác, faults, perf,24h, receiver/persistence,0P0/P1'),
 ('M6','Handoff và bench kit',['M5'],[2,3],'Release/receiver owner + RtR bench lead','Nhóm khác tự cài và chuẩn bị nối HeraHub','Independent install/run/review, configuration matrix, known limits, provider contracts và bench/HIL intake hoàn chỉnh')]
milestones=[{'id':a,'title':b,'dependsOn':c,'estimatedPersonDays':d,'ownerRole':e,'userOutcome':f,'exitGate':g,'state':'NOT_STARTED'}for a,b,c,d,e,f,g in milestoneRows]
reqRows=[
 ('R01','M0','Release/dependency closure','Selected source/config/fonts/definitions có đủ SHA/type/license; missing paths được xử lý trong isolated intake; clean install closure kiểm được',['F42','F43']),
 ('R02','M0','Supported profile và pairing','Chốt API/ABI/OS/WebView/GPU/codec/AP/model; loopback mặc định, LAN pairing có cert/nonce/auth/expiry; WebView origin/bridge allowlist; không cleartext control ra LAN hoặc tự chọn thiết bị',['F41','F43']),
 ('R03','M1','Recorder và clock closure','Đủ RX/INTENT/SENT/CRC/chain/CLOSE hoặc explicit failure; không overwrite/unread/tràn; elapsed đóng đúng1lần; 30min kiểm capacity thật',['F31','F44','F45']),
 ('R04','M1','Authority/session/input','Wrong boot/target/operator/sequence/stale bị chặn; neutral claim/release; native focus/deadman; HB1500ms/lease200ms; không tự restore',['F01','F02','F10']),
 ('R05','M1','Manual/assisted flight','Actual APK takeoff/manual pitch+yaw/Hold/POI/orbit/RTL/LAND với ACK+observed state+ground truth; không force-arm hoặc UI animation thay execution',['F03','F14']),
 ('R06','M1','Mất link và AP reboot thật','Injection chứng minh socket/byte loss hoặc actual boot/PID đổi; pending UNKNOWN, revoke; reconnect cần discover/preflight/consent mới; failsafe quan sát theo typed config',['F04','F10','F40']),
 ('R07','M2','Mission model và KML/QGC','Một semantic model; positive/negative held-out corpus; camera commands/frames/altitude/speed giữ nghĩa; unsupported complex/fence/rally từ chối rõ',['F12','F34']),
 ('R08','M2','Geo/Home/terrain','WGS84/ENU/NED/Home/relative/AMSL/AGL/geoid/time/source/no-data kiểm độc lập; không ngầm chuyển datum; readback nằm tolerance theo encoding/projection',['F13','F16']),
 ('R09','M2','AUTO/Hold/resume/refly intent','Plan→compile→upload/readback→Home review→AUTO→reached→ground/disarm→review; Hold/resume/RTL consent và MIS_RESTART typed; refly phần thiếu là plan mới được duyệt',['F03','F04','F17']),
 ('R10','M2','Airspace/geofence/return','Nguồn vùng trời synthetic có tuổi/coverage; fenceAP upload/readback/breach; preview return/alternate/reserve; UNKNOWN không thành permission',['F06','F07','F08','F09','F11']),
 ('R11','M3','Payload capability/4 peer routing','4 peer có ID riêng; capability-driven UI; manager/device mapping đúng; foreign/late/ambiguous ACK không mở quyền; unsupported command từ chối',['F18','F20']),
 ('R12','M3','Hai operator độc lập','Hai authenticated clients/processes/session histories; flight và per-payload authority riêng; consent handoff/contention/partition/revoke; feed switch không chuyển quyền',['F05','F37']),
 ('R13','M3','Video xuyên mission','Ghi từng chặng clock/seq, toàn khoảngAUTO và min-binFPS/maxgap; cold-start/codec/queue/error; source idle paused; không deduce photon từ canvas',['F19','F22','F44']),
 ('R14','M3','Camera file/exposure/geotag','Sim camera tạo image file, exposure/index/sourceSHA/UTC-or-bracket/pose/datum; EXIF chỉ khi đúng nghĩa, sidecar đầy đủ; unknown time/geo đánh uncertainty; hardware-photo count0',['F21']),
 ('R15','M2','Mapping readiness/quality','Stable lens/focus/mount/shutter/time sync, planned vs achieved footprint, GSD/overlap/blur; fixed không đồng nghĩa mọi gimbal sai; simulated coverage không là accuracy thật',['F12','F15','F28']),
 ('R16','M4','Physics fidelity/envelope','Phiên bảnmass/inertia/CG/rotor/lag/drag/battery/wind/contact/sensor; frame/time oracle và held-out seeds; FID2 required; Hera constants vẫn assumptions trước calibration',['F45']),
 ('R17','M4','Obstacles/contact/motor/payload swing','Avoidance sensor đi quaAP, contact riêng; dropout khi vẫn giữ cần; pitch+yaw,1/2/3motorfault, pendulum/headwind có expected bounded behavior/loss outcome; không giả all faults controllable',['F27','F45']),
 ('R18','M4','3D/audio source-truth','Pose/camera/sensor bám cùng run/clock, scene stale freeze, rotor/audio muted đúng; licensed PBR assets; actual audio capture và FPS target; weather visual/physics tách rõ',['F46']),
 ('R19','M4','Training/instructor/debrief','Manual+assisted+AUTO bài thực tế; instructor faults tách authority; input/clock/events timeline và report, scripted vs human rõ; không tổng điểm kỹ năng bay thật chưa validated',['F33','F47']),
 ('R20','M4','Cockpit UI/input quality','Token/grid/rail alignment, đủcontrast/touch targets, 2themes/sunmoon, allscreens/popup/IME/insets/error, safe takeover; simulated HID contract và actual Android touch',['F02','F48']),
 ('R21','M5','Workspace/review/restart','Durable workspace+review, cold Android/host restart; no authority restore; receipt/data/plan/raw identities giữ nguyên; không success từ last historical pose',['F31','F40']),
 ('R22','M5','Dataset/SAF/receiver','Large file export/checkpoint/resume/receipt; thiếu/hỏng/sai receiver/replay từ chối; independently reconstruct từ original; metadata-only phải ghi external raw not embedded',['F32','F33','F34']),
 ('R23','M5','Quota/archive/resources','Admission20/floor10+reserve256/forecast15; no autodrop/delete; ENOSPC/EIO/fsync/pending/reserve export; control ưu tiên dưới overload; cap queues/RAM/RSS/guest',['F35','F44']),
 ('R24','M5','Performance và endurance','Same-final-release metrics, cold/nominal/fault,1x/frame/fsync, 30min→2h→8h→24h uninterrupted active-loop on admitted target; no time stitching/no replay substitution',['F44']),
 ('R25','M5','Beta install/update/security','APK cert/hash/SBOM/licenses + host prerequisite/package verifier; no privatekeys; schema upgrade failure giữ original; MITM/replay/origin/simulator boundary/cold migration checked',['F41','F42']),
 ('R26','M6','Receiver/user acceptance','Nhóm nhận độc lập install/pair/plan/fly/fault/review/export không developer shell rescue;5formative users/5tasks,≥90%completion,0criticalerrors; NOT_CHECKED nếu thiếu human',['F38','F48']),
 ('R27','M6','Hardware-ready adapter kit','Versioned MCU/HID/radio/AP/payload contract, diagnostics/calibration & bench/HIL scripts; exact model/firmware unknown registry/owner; không hardware capability claim',['F02','F20','F43']),
 ('R28','M6','Release truth and limits','Toàn MUST cùng release/config,0P0/P1, knownunsupported visible; feature/data/simulator/replay/actual sources tách; no DJI superiority/NDAA/endurance/realflight claim thiếu proof',['F30','F43'])]
requirements=[{'id':a,'milestone':b,'title':c,'acceptance':d,'featureIDs':f,'priority':'MUST','state':'NOT_CHECKED_NEW_CAMPAIGN','oracleRequired':True}for a,b,c,d,f in reqRows]
metricRows=[
 ('K01','Control safety','0accepted wrong/stale/foreign intent; HB1500ms/lease200ms giữ nguyên','raw TX+native intent+authority journal; clock age brackets','R04'),
 ('K02','Physics pacing','speedup1/cap500ms/fsync-before-sensor; aggregate RTF≥1.000 nominal; đầy đủ frame','independent WAL+AP required-stage correlation+host/guest uncertainty; insufficient clock→INCONCLUSIVE','R24'),
 ('K03','Renderer','RAF p95≤33.4ms,p99≤100ms foreground1280×800 full-quality cùngSITL/media','per-frame render trace; GPU/present/thermal captured separately; no photon claim','R18'),
 ('K04','RGB video','720p30; everyfull5sbin≥24FPS; p95upper≤300ms; conservative maxgap≤250ms toànAUTO','all frame source/encode/network/decode/canvas IDs; independent parser full interval','R13'),
 ('K05','Cold start','firstvalidRGBframe≤1500ms after explicit start on primaryprofile','at least3 cold starts with source/decoder startup clock brackets','R13'),
 ('K06','UI responsiveness','localtouchfeedbackp95≤100ms;0ANR/crash mandatorycorpus','actual Android native input→visible feedback; ACK separately','R20'),
 ('K07','Touch/contrast','touch≥48dp; textnormal≥4.5:1,largetext≥3:1; glove56–64dp trial','layout measurements +adaptive scene backgrounds + human task observation','R20'),
 ('K08','Storage','entry20GiB/floor10GiB+256MiB/forecast15s; explicit raw/video/copy/export budgets','live host/guest observer and lossless-size estimate with reserve; no evidence deletion','R23'),
 ('K09','User tasks','5formativeusers×5tasks;≥90%taskcompletion;0unintendedcriticalaction','script/time/errors/recovery logs; not statistical DJI superiority certification','R26'),
 ('K10','Endurance','30min→2h→8h→24h actual closedloop, uninterrupted singleinterval at final release','raw clocks/power/sleep/owner/source/GPU/media/queue/storage; restart/death→FAIL','R24'),
 ('K11','Geometry/control','Calm reference cross-trackRMSE≤1m,max≤3m,altitudeRMSE≤0.5m; otherprofileslocktolerancebeforetest','groundtruth trajectory vsacceptedpath; separateAPestimate/noisemodel','R08'),
 ('K12','Exposure/geotag','Simulatedfileindex/route/SHA100%match;position≤1m,altitude≤0.5m,timebracketuncertainty≤50ms primaryprofile','independent image/sidecar/exposure groundtruth reconstruction; not realcameraaccuracy','R14'),
 ('K13','Model analytical fixtures','Staticforce/acceleration/charge≤1%error;pendulumfrequency≤5%;exactbyteoldmodelwhereunchanged','analytical/unit fixtures+timestep/contact/noise tolerances frozenbeforetest; calibrationseparate','R16')]
metrics=[{'id':a,'name':b,'target':c,'method':d,'requirement':f,'provenance':'AERIS_ENGINEERING_PROPOSAL_UNLESS_CITED_UI_GUIDANCE','state':'NOT_MEASURED_NEW_CAMPAIGN'}for a,b,c,d,f in metricRows]
# Corpus designs are explicit, not executable tests or measured PASS counts.
cases=[]
def case(i,title,kind,refs,method,expected,repeats=1):cases.append({'id':i,'title':title,'layer':kind,'requirements':refs.split(','),'method':method,'expected':expected,'repeats':repeats,'state':'PLANNED_NOT_EXECUTED','releaseScope':'SAME_FINAL_RELEASE'})
nominals=[
 ('N01','Manual hold/takeover','R04,R05,R16','Actual Android touch neutral→pitch/yaw→release→LAND; empty/loaded profile','Observed guided/loiter transitions and ground/disarm, no stale lease'),
 ('N02','Assisted POI/orbit','R05,R08','Actual Android radius/speed/height request, AP execution then takeover','Geometry/envelope oracle; consent and state observed'),
 ('N03','Inspection waypoint/oblique','R07,R09,R11,R14','Waypoint/camera actions +inspection target withknowngeometry','Readback/exposure/sourcefile and pose agree; unsupported action blocked'),
 ('N04','Polygon flat','R07,R08,R09,R13,R14,R15','Held-out validKML, video/payload concurrently','FullAUTO→LAND/review/receiver and geometric oracle',3),
 ('N05','Polygon terrain','R07,R08,R09,R13,R14,R15','Pinned syntheticDEM and declaredAGL→APaltitude conversion','Terrain/clearance/semantic consistency, fulltask',3),
 ('N06','Polygon boundary','R07,R08,R09,R13,R14,R15','Nearcoverageedge with valid source and no hidden nodata','Fullvalidmission; invalidadjacent fixtures rejected',3),
 ('N07','Corridor straight','R07,R08,R09,R13,R14','KML linebuffer/overlap/camera plan shared model','Readback/achievedsimcoverage/fullmission',3),
 ('N08','Corridor bends','R07,R08,R09,R13,R14','Tight-but-supported bends, gimbal/camera actions','Bounds/sequence/no cornercut outside accepted envelope',3),
 ('N09','Corridor altitude modes','R07,R08,R09,R13,R14','Supportedmixedrelative/AMSL source with explicit conversions','Independentdatum oracle or explicit refusal ifunsupported',3),
 ('N10','Night search grid','R09,R13,R16,R18','Dark scene+syntheticthermal, seededwind/noise','Sources/age/rightroute/capture and fulltask; no realnightclaim'),
 ('N11','Lowenergy return/alternate','R05,R10,R16','Simulatedbattery/load/headwind and approvedfailsafeprofile','Return/land policy observed or explicit unsupported/unsafe refusal'),
 ('N12','Fourpayload/twooperators','R11,R12,R13,R14','A flies;B separately controls selectedgimbal,captures, switchesRGB/IR','Correct4peer IDs/noauthoritytransfer fromfeed/noforeign capture'),
 ('N13','Review/SAF/coldreceiver','R21,R22,R25','Selectrun export, closeapp/host, import on fresh workspace/receiver','Byte/data/plan/source completeness correct;0restored authority'),
 ('N14','Instructor exercise and debrief','R04,R19,R21','Record manual input/clock/ownership with instructor-triggered fault; cold replay same exercise','Debrief actions/trajectory/uncertainty reproducible; human/scripted distinct, no unvalidated pilot score')]
for t in nominals:case(t[0],t[1],'ANDROID_AP_E2E',t[2],t[3],t[4],t[5] if len(t)>5 else 1)
faults=[
 ('F01','Socket cut whileforwardheld','R04,R06,R18','Ownedfaultproxy closes actual dataFD; confirm byteflow cessation','Revoke/UNKNOWN/failsafe perprofile; stale rendering/audio stop'),
 ('F02','AP reboot airborne','R04,R06,R21','Actual ownedAP process/boot restart witholdsession frames replayed','Bootidentity changes, oldlease/approval blocked; no auto resume'),
 ('F03','Host crash','R03,R06,R21','Kill exactownedhost after precommittedfault receipt','No claimed flight completion; durableprefix/unknown recovered'),
 ('F04','Android background/force-stop','R04,R21','ActualHOME/background thenprocessdeath','Input deadman/revoke; restart has no authority'),
 ('F05','Delay/loss/reorder/dup','R04,R06,R13','Seedednetworkprofile within/outside activeenvelope','Insideprofile meetsgates; outside failsclosed without lowerguards'),
 ('F06','Wrongcamera/gimbal target','R11,R12','Realframingwrongsys/component/device, lateACK injection','0foreign accepted writes; cannotattribute ambiguousACK'),
 ('F07','Dual-operator split/lategrant','R04,R12','SeparateprocessB partition; simultaneousrequest/lategrant','Singleownerperresource; no splitbrain or autoplay'),
 ('F08','Payload reboot/hotplug','R11,R12,R14','Restartpeer/discovery sameoldidentifier newboot','Invalidateoldcapability/lease/capturepending, rediscoverexplicitly'),
 ('F09','Video stale/sourceclockjump','R13,R14,R18','Stopsource whiletransportalive; clockjump/wrongframeUID','Agevisible, nofreshlabel; noincorrectexposuregeotag'),
 ('F10','Writer shortwrite/EIO/fsyncfail','R03,R21,R23','Fault filesystemadapter; actualboundedtempvolume ifadmitted','No publishbeforesync; preservepending/failure; no falseCLOSE'),
 ('F11','Quota/ENOSPC/exportreserve','R21,R22,R23','Smalltask-ownedquota, nohostdiskfill','Admission/cleanupconsent and packagecompleteness correct'),
 ('F12','Missing/tampered/wrongreceiver package','R22,R25','Mutateclosedpackage/corruptchunk/replayoldreceipt','Coldverifier rejects; cannotpublishpartial'),
 ('F13','Home/datum/DEM/geoid invalid','R07,R08,R10','No-data/wrongdatum/staleHome/profilewrongtype corpus','Plan/preflight fails withreason, no hidden conversion'),
 ('F14','GPS/EKF loss','R06,R10,R16','APinputsensorfeed fault withrecordedgroundtruth','Firmwareprofilebehavior observed; UIuncertainty correct'),
 ('F15','Obstacle sensor disappears withstickheld','R04,R10,R17','Groundtruthobstacle plusactualdistancefeed→dropout','Sensorloss handling pertypedconfig, contact stillreal ifcollision'),
 ('F16','Upgrade/schema interrupt','R21,R25','Newbeta testworkspace upgrade interrupted beforecommit','Originalrecords preserved, no authorityrestore/implicitrollback'),
 ('F17','Origin/auth/replay/MITM','R02,R04,R25','Expiredpairingtoken, foreignorigin, copiedsession/certwrong','Unauthorized observe/control denied; noflightdispatch')]
for t in faults:case(t[0],t[1],'MOCK_REPLAY_THEN_SCOPED_ACTUAL_AP_ANDROID',t[2],t[3],t[4])
physics=[
 ('P01','Pitch+yaw coupling','Attitude combinations/timestep/differential oracle; no UIposefeedback'),
 ('P02','Empty vsloaded/CGshift','Declaredmass/inertia/CG profiles; acceleration/settling/energy vsoracle'),
 ('P03','Wind/gust/headwind','Seededwind withhold/return; distinguishsimulationprediction/Heraunknown'),
 ('P04','Suspendedpayload','Pendulum/tension/CG/wind/contact; timestep/conservation oracle'),
 ('P05','Motor1/2/3 faults','Knownrotorforces; distinguishcontrollableframe vs loss ofcontrol'),
 ('P06','Obstaclebraking/contact','SensorFOV/range/delay separate fromphysicalcontact; no universal10m rule'),
 ('P07','Battery/altitude/temperature','Versionedbattery/thrust/air-density model assumptions; no Hera45minclaim'),
 ('P08','Night/rain sensor/render','Light/visualrain separate from noise/link/drag assumptionandcalibration'),
 ('P09','Frames/units/geoaxis','ENU/NED/FRD/quaternion/timestamp/timebase knowntrajectory'),
 ('P10','Exact reference replay','SamePWM throughoriginalmodel; exactwhereimplementationunchanged, numericalchange requires declared tolerance pretest')]
for i,title,method in physics:case(i,title,'MODEL_ORACLE_THEN_AP_PROFILE','R16,R17,R18',method,'Within declared envelope oracle; outcomes including loss/contact remain honestly reported')
for i,title,refs,method,expected in [
 ('Q01','Fresh install and companion','R01,R02,R25,R26','Freshqualifiedtarget, packageprerequisitesandpairing','No developerhomedir/shell rescue; exactAPK/cert andexplicitSIM'),
 ('Q02','Allscreens/theme/popup/insets','R20,R26','Plan/preflight/Fly/payload/review/error/IME/fontscale','No overlap/cutoff criticalcontrol;touch/contrast;bothrails aligned'),
 ('Q03','Cold/video/fullworkload','R13,R18,R24','3coldstarts;allAUTOframes;fullquality scene +payload','Allselectedmetrics includingp99/maxgap/min5sFPS computed independently'),
 ('Q04','30min/2h/8h/24h','R03,R23,R24','Newbetacampaign, continuousactual-loop withpower/storageobserver','No intervalstitch;frames/clock/pins/lease/journal/resource preservation'),
 ('Q05','Receiver corrupted/restart','R21,R22,R26','Coldprocessreceiver andactualSAFdestination','Payload byteverified, completeness independent of reportedSUCCESS'),
 ('Q06','Human pilot/payload tasks','R20,R26','5participants,5tasks, counterbalancedworkflow wherebaselineavailable','≥90%taskcompletion,0unintendedcriticalaction;time/errors/workloadrecorded'),
 ('Q07','Release truth and Hera bench intake','R01,R02,R27,R28','Recipient reviews supportedmatrix, versions, unknown owners, bench/HIL contracts and unsupported capability UI','No physical-device, AI, actualmedia, NDAA or field claim inferred from simulator; all MUST/results/release refs consistent')]:case(i,title,'QUALIFICATION',refs,method,expected)
featureNames={}
for line in (R/'planning/product-standard01/BASELINE.md').read_text().splitlines():
 if line.startswith('| F'):
  values=[s.strip()for s in line.split('|')[1:-1]];featureNames[values[0]]=values[1]
post={'F17','F23','F24','F25','F26','F29','F36','F39'};contract={'F02','F09','F15','F20','F21','F27','F38','F41','F42','F43'}
mapping=[]
for i,title in featureNames.items():
 refs=[r['id']for r in requirements if i in r['featureIDs']]
 if not refs:refs=['R28']
 mapping.append({'featureID':i,'title':title,'scope':'POST_BETA_EXTENSION'if i in post else'BETA_SIM_CONTRACT_WITH_SEPARATE_HARDWARE_OR_PRODUCTION_GATE'if i in contract else'BETA_SIM_MUST_WITH_DECLARED_LIMITS','requirementIDs':refs,'qualification':'NOT_CHECKED_NEW_CAMPAIGN','note':'Feature group is broader than one beta requirement; its real-hardware/advanced parts are not qualified by simulated peers.'})
tasks=[]
taskRows=[
 ('T01','M0',[],'Mapretain/adapt/retire; pinselectedsourceincluding9overlayfiles; dependencyandmissingfileintake','sourceclosure +modulemap'),
 ('T02','M0',['T01'],'Freezetargetprofiles/metrics/corpus/spaceandruntimebudgets;ownerPID/serial/pairing','supportedmatrix+runcontract'),
 ('T03','M1',['T02'],'Reprorecorderfull/closedclock/navigationfirstfaultinmock','regressionfixtures+traces'),
 ('T04','M1',['T03'],'Implementversionedsegmentedrecorder/capacityadmissionandwriterclosure','losslessjournal/capacityoracle'),
 ('T05','M1',['T04'],'Unifynativeflightstate/neutral/manual/assisted takeover','flightauthoritycorpus'),
 ('T06','M1',['T05'],'Actualsocketcut/APboot/30minmanualloopacceptance','boundedactualraw+closure'),
 ('T07','M2',['T06'],'Sharedmissionmodel/KML/QGCsemantic+geooracles','heldoutcorpus'),
 ('T08','M2',['T07'],'Workbenchoffline/map/terrain/readiness/airspacefence','operatorpreview+sourcecoverage'),
 ('T09','M2',['T08'],'Upload/readback/AUTO/Hold/resume/RTL/review integration','polygon/corridor/inspection nominal'),
 ('T10','M3',['T06'],'4payloadpeers/discovery/managerbinding/explicitcapability','protocolrouteadversarialcorpus'),
 ('T11','M3',['T10'],'2independentoperators/auth/consenthandover/partition','perresourceauthorityproof'),
 ('T12','M3',['T10'],'Hostsimcamera→encoder→Androiddecoder,stageclock andtrace seal','fullintervalvideooracle'),
 ('T13','M3',['T11','T12'],'Exposure→simulatedfile→geotag→review→receiver','camera-sourceintegritypackage'),
 ('T14','M4',['T06'],'Referencephysics/sensor/contact/load/wind/motor/swingcorpus','FID2envelope+assumptions'),
 ('T15','M4',['T14'],'PBRscene/audio/camera/weathertruth/performancemodes','actualrender/audioevidence'),
 ('T16','M4',['T09','T13','T15'],'Unifieddesign tokens/allstates/screens/Androidinput/IME','visualandgeometryQA'),
 ('T17','M4',['T15','T16'],'Instructor exercises/debrief and formativetaskpilot','scenario/replay/usabilityreport'),
 ('T18','M5',['T09','T13','T17'],'Freeze onecandidate andrun allnominal/fault cohorts','same-releasequalification'),
 ('T19','M5',['T18'],'Runbounded30min/2h/8h/24hperformanceandresource suite','coldraw/power/sourceobserverreceipts'),
 ('T20','M5',['T19'],'Install/update/schema/SAF/receiver/securityandpreservation','releasegate+independentverification'),
 ('T21','M6',['T20'],'Independentreceiver install/demo/tasks/troubleshooting','recipientacceptance'),
 ('T22','M6',['T21'],'Publishinternalhandoff,bench/HILcontracts/unknownregistry','BETA_SIMdecisionandhardwareintake')]
for a,b,c,d,e in taskRows:tasks.append({'id':a,'milestone':b,'dependsOn':c,'work':d,'deliverable':e,'state':'NOT_STARTED','requiresTIPBeforeImplementation':True,'executionBudgetMustBeDeclared':True})
risks=[
 ('V01','Recorder/rawstorage','Tracecapacityorfree-spaceforecastinsufficient','M0/M1','Preflightcapacitygate;losslesssegments;externalstorage/qualifiedcompression;noautomaticdelete'),
 ('V02','CompetingUI/transportowners','Twoownerspaint/dispatchsameevent','M1/M4','Singleowners/domainseams;capturecontextbeforemutation'),
 ('V03','ACK/time/targetambiguity','LateACK/clockuncertainty/bootreused','M1/M3','Fencedcontext+observedstate+rawfiles;UNKNOWNandexplicitreconcile'),
 ('V04','HostAP/media contention','Heartbeat/videojitterrisesunderconcurrency','M1/M3/M5','Perstagetraces/threadqueues;separatedbudgets;sameprofiledifferential'),
 ('V05','Falsefidelityclaims','VisualqualitymistakenforHeracalibration','M4','FIDlevels/provenance/envelope;Rtrcalibrationdata/humanlater'),
 ('V06','Hardware/humanunavailable','Cannotverifyactualdevice/SDK/operator','M6','FinishBETA_SIM;BETA_DEVICE/HERAremainNOT_CHECKED'),
 ('V07','Repeatedblindliveruns','Samefailurewithoutnewinformation','ALL','After2same-signaturestopswitchreplay/instrumentation;finiteTIPbudget'),
 ('V08','Beta scope creep','Newfleet/AI/engine changereplacesqualification','ALL','FreezeMUST;postbetafeaturemap;noaddedabstractionwithoutmeasuredbenefit')]
customer=[
 {'id':'C01','need':'Stream phone/tablet/PC smoother; failing stage unknown','requirements':['R13','R18','R24']},
 {'id':'C02','need':'Photo geotag at drone/camera exposure, not object coordinate','requirements':['R14','R22']},
 {'id':'C03','need':'RGB/thermal and interchangeable payloads','requirements':['R11','R12','R13']},
 {'id':'C04','need':'Night/longrange simulation and honest link/energy limits','requirements':['R06','R10','R16','R18']},
 {'id':'C05','need':'Mapping readiness, stable camera/lens and KML/corridor quality','requirements':['R07','R08','R15']},
 {'id':'C06','need':'Research Partner PhaseOne/dualoperator/multiplepayloads;45min andNDAA arehardwareclaims','requirements':['R11','R12','R27','R28']},
 {'id':'C07','need':'Pitch+yaw/obstaclecontact/suspendedload/wind/batteryaltitude/motorfault/HID','requirements':['R04','R16','R17','R19','R27']}]
q={'format':'aeris-beta-campaign-plan','version':1,'createdLocalDate':'2026-10-26','timezone':'Asia/Ho_Chi_Minh','status':'PLAN_NOT_EXECUTED','sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip(),'authority':'Assistant-authored architectural proposal; user requested comprehensive plan, no runtime/flight/production action from this file','releaseGoal':'BETA_SIM complete within explicit support matrix, plus hardware-ready adapter/bench kit; physical-device/real-flight gates separate','readinessNow':'ENGINEERING_ALPHA_INTEGRATED_BETA_NOT_READY','releaseIdentityFields':['commit','apkSHA256','certificateSHA256','hostManifestSHA256','APBinarySHA256','APParametersSHA256','modelSHA256','terrainSourceSHA256','payloadTopologySHA256','schemaVersion','AndroidOS','WebViewVersion','codecProbe','configurationID','corpusSHA256'],'milestones':milestones,'requirements':requirements,'metrics':metrics,'featureMapping':mapping,'customerTraceability':customer,'cases':cases,'taskGraph':tasks,'risks':[{'id':a,'risk':b,'trigger':c,'ownerMilestone':d,'mitigation':e}for a,b,c,d,e in risks],'supportedConfigurations':[{'id':'CFG01','role':'Required reference Android–SITL','Android':'API33 ARM64 emulator,4vCPU/2GiB,1280x800landscape baseline; exactOS/WebView/GPU/codec pinned inM0','host':'CurrentmacOSARM/cachedPython3.14/Node/Docker baseline;version&RAM&CPU&power measuredbeforefreeze','aircraft':'ArduCopter4.7.1 exactartifact+parameterprofile,referencequad, externalphysics; instrumentationnewartifactifneeded','status':'TARGET_NOT_QUALIFIED_NEW_CAMPAIGN'},{'id':'CFG02','role':'IndependentoperatorB','target':'Separateauthenticatedclient/process/identity, browser/native configurationexplicit; nottwo cardsinoneActivity','status':'TARGET_TO_FREEZE_M0'},{'id':'CFG03','role':'Android phone/physical','target':'Xiaomimodel/Android/HyperOS/WebView/GPU stillunknown; minSdk26/target33 in existing manifests notcompatibilityproof','status':'NOT_CHECKED_PHYSICAL_TARGET'},{'id':'CFG04','role':'HeraHub/realpayload','target':'Model/OS/MCU/radio/AP/frame/camera/gimbalSDKrequired; noassumedasbuilttruth','status':'HARDWARE_GATE_SEPARATE'}],'executionPolicy':{'planLaunchesRuntime':False,'preserveFrozenSourceCandidateENDURE':True,'buildAPOrAPKNow':False,'productionSigning':False,'physicalFlightCommands':False,'networkControlDefault':'LOOPBACK_ONLY; authenticatedexplicitpairingbeforeLAN','diskAdmissionGiB':20,'diskRuntimeFloorGiB':10,'reserveMiB':256,'forecastSeconds':15,'physicsSpeedup':1,'pacingCapMs':500,'fsyncBeforeSensor':True,'frameDropForPerformance':False,'automaticEvidenceDeletion':False,'campaignEvidenceRoot':'evidence/beta-campaign01/runtime-<release-id>','runtimeBudgets':'EachTIPpredeclareslaunchcount/walltime/files/bytes/callretries;runcontrollerenforces;noarbitraryunboundedreruns','oldENDURE':'READ_ONLY; noresume/relaunchorintervalstitchfromthisplan'},'resourceSizing':{'observedWalBytes':215851544,'observedReceiveWallSeconds':97.277290959,'extrapolatedWalGiBPerHour':7.439544104894161,'extrapolatedWalGiBPer24h':178.54905851745986,'scope':'Singlemanualcaptureextrapolation,WALonly;APtrace/video/copies/exportadditional;compressionunmeasured','longRunGate':'Preflightreservedbudget+power/sleepobserver onadequatehost/storage;24hnotallowedbyelapsedmetadataalone'},'scheduling':{'totalEstimatedPersonDays':[21,33],'calendarHypothesisWeeks':[4,6],'teamAssumption':'2corebuilders+1QA;partialparallelM2/M3/M4;hardware/humanwaitunbounded','confidence':'LOW_BEFORE_M0;reforecastusingactualthroughput;notcommitment','criticalPath':'M0→M1→M2/M3/M4integrated→M5→M6'},'releaseGate':{'requiredRequirementIDs':[r['id']for r in requirements],'allMandatoryPassSameReleaseConfiguration':True,'openP0P1Allowed':0,'requiredNotCheckedAllowed':0,'pastPassingModulesAutoQualifyNewBinary':False,'rawIndependentReceiverRequired':True,'humanUsabilityRequiredForFinalBetaHandoff':True,'physicalBETADEVICEClaimWithoutDevice':False,'claimedDJISuperiorityWithoutMatchedBenchmark':False},'sources':[{'id':a,'title':b,'url':c,'use':d,'retrievedLocalDate':'2026-10-26','provenance':'OFFICIAL_DOCUMENT_OR_PUBLISHER_CLAIM_NOT_AERIS_TEST'}for a,b,c,d in sources],'localInputs':inputs}
(P/'campaign.json').open('x').write(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':q['status'],'milestones':len(milestones),'requirements':len(requirements),'metrics':len(metrics),'featureGroups':len(mapping),'cases':len(cases),'taskPackages':len(tasks)},indent=2))
