# SIMDROP77 — mất cảm biến khi giữ cần tiến

16/10/2026. **Chẩn đoán hoàn tất; gate an toàn mất cảm biến KHÔNG ĐẠT.**4/4lượt đủ điều kiện bằng chứng chạm mặt bao vật cản ảo khi cảm biến ngừng gửi nhưng RC vẫn tiến. Tổng6lượt bay thực:4qualified,2driverclosureFAIL retained. Cả6raw đều xác minh hành vi chạm ảo;2lượt lỗi không được đổi thành flight/driverPASS. Một agent SPEC/BUILD/VERIFY; second decoder không là assessor độc lập.

Dùng internal quad ArduCopter4.7.1/dbe79216, binary/image cũ đã pin, requested speedup1, localhost5897. Đây không là Hera hoặc SIM32 external physics; không suy ra realtime1×, contact-force fidelity, radio/HID/SDK hay sản phẩm đã an toàn. No forcearm/automatic retry/reconnect, không source/candidate/trust/SOT/ENDURE edit hoặc software signature.

## Bốn lượt qualified / đối chứng

A=BASELINE(AVOID_ENABLE0); B=ENABLED(2), margin2m, stopbehavior1, backup0. Plane north12m, provisional sphere0.3m. Order AB/BA/BA/AB. Explicit GUIDED return-to-origin giữa ca có raw, không reset pose ngầm.

| Run / replicate | Order | Minimum surface gap khi sensor hợp lệ,m | Vận tốc tiến lớn nhất trong3s cuối,m/s | Cửa sổ sensor-loss đến bound,s guest | Outcome |
|---|---|---:|---:|---:|---|
| run01 / rep01 | BASELINE→ENABLED | 1.693 | 0.102 | 4.901 | UNSAFE_VIRTUAL_CONTACT |
| run02 / rep02 | ENABLED→BASELINE | 1.615 | 0.120 | 4.550 | UNSAFE_VIRTUAL_CONTACT |
| run03 / rep03 | ENABLED→BASELINE | 1.663 | 0.115 | 4.550 | UNSAFE_VIRTUAL_CONTACT |
| run06 / rep04 | BASELINE→ENABLED | 1.691 | 0.105 | 5.001 | UNSAFE_VIRTUAL_CONTACT |

Cả4baseline centre đều vượt12.3m; cả4valid-sensor control phanh/giữ gap≥1.2m theo fixture. Range minimumgap=1.615–1.693m; tailmaxspeed=0.102–0.120m/s. Fixture thresholds không là tolerances Hera hoặc xác nhận claim10m/creep.

Ở loss case, valid-sensor approach ổn định trước cut; queued sensor TX đã drain. Sau committedcut không có sensor TX; RC2=1400/RC4=1500 còn nguyên, AP RC echo và armedLoiter được giữ; không command đổi mode/AVOID/neutral trước endpoint. APproximity output hết hạn, drone tiến và vượt virtual-plane bound. Coldraw verifies heldTX andecho, typedconfig, clock/CRC/hashchain and no hidden intervention. Experimenter neutralization, sensor restore và LAND/disarm chỉ sau endpoint; không coi đó là AP failstop.

Cửa sổ quan sát đến centrebound là4.550–5.001s guest. **Không đồng nhất số này với thời điểm chạm đầu tiên.** Bảng sampling contact timing trong campaign-summary.json đặt tiếp xúc sphere đầu trong bracket khoảng3.999–4.500s guest, theo từng run. Đây là bracket telemetry50ms tương đối APboot reference atcut, không exactimpact hoặc one-waylatency. Các clocks host/guest không merge/scale.

Virtual plane không có phản lực trong internal model. Min gap âm nghĩa mặt bao ảo vượt plane, không chứng minh hư hỏng/collision response Hera. Kết luận chỉ là cấu hình thử chưa bảo đảm dừng an toàn khi proximity mất nhưng input tiến tiếp tục.

## AC / chất lượng bằng chứng

| Requirement | Verdict |
|---|---|
| R77-01 pins/preflight/ownership | PASS scoped; exact binary, config/typedreadback/GPS/EKF/Home, normalarm and manifests |
| R77-02 repeat/control order | PASS functional4replicates; PARTIAL original exact-source matrix: collector revisions3original+1RXdrain, deferred matched-source/performance claim |
| R77-03 held-input loss | PASS evidence4qualified; all6raw also verify, including2driverFAIL |
| R77-04 classification | PASS diagnostic classification; **SAFETY FAIL4/4qualified,6/6observed** |
| R77-05 intervention/restore/LAND/closure | PASS4qualified and scoped repaired closure;2earlier driverclosureFAIL remain. Long-run collector reliability NOT_CHECKED |
| R77-06 raw/adversarial | PASS scoped independent CRC/parser +semantic/config/clock guards; false-safe mutations refused |
| R77-07 resources/preservation/handoff | PASS endpoint checks; no continuous presence or ENDURE acceptance claim |

Policy mock32/32; lifecycle8/8; negativebites7/7; cause-disambiguationmock3/3; RXdrainmock5/5. Counts are separate scopes, not software maturity %. Qualified raw contains49,062APframes and25,128TXframes. All6observed raw contain75,362APframes. Every admitted MAVLink RXbyte retained, CRC/fullchain and TXintent/write-return checked. This is not1200HzSIM32 model-frame oracle. Hashes are local integrity, not signatures or authentication. Syntax/AST checked17source files; no fullbuild/typecheck/lint claim.

## Driver closure failures and repair

run04/05 both observed LAND/disarm, retained complete raw and cleanly stopped/removed container, but observer receive duringclose threw LOST_OR_STALE_RECEIPT. Shared error can mean deadobserver ordering or age/clock failure; historical precise cause remainsNOT_PROVEN. Readonly replay independently verifies their behavior; they stayunqualified and are not counted among4complete replicates.

Final reservedrun06 uses new client-v2/RxDrain plus driver-v3 import, after5mocktests. It pauses newadmission, waits all admitted RXwork, retains errors/partialtail rejection, then closes observer/socket and fsyncs. RawRX_CUTOFF confirms admitted work drained and noRX/TXaftercutoff. Exactsend/read/axes/tick segment and driverbody exceptimport match old; collector bookkeeping nevertheless differs. Both sourceversions/archives retained, originalfiles unchanged; no source-identical or matched performance claim. Prospective closure addendum raised rep04attemptbound2→3 within total6cap; no automatic retry/seventhstart. Campaignbudget is now exhausted.

## Bảo toàn / dung lượng

43,880protected paths exactSHA before/after,0missing/changed; all6operational pins and archivedsource files also match. Frozen source/candidate and ENDURE/history kept, no soak restart or24hPASS inference. Point checks do not prove continuous original-path presence.

All6ownedcontainers stopped/removed. Min observed free duringrun=23.715GiB; final=24.529GiB, above20GiBfloor. Gate22GiB/stopreserve20.5GiB retained. Newlogical artifact/state≈19.11MiB before reports of256MiBbudget. Samples do not certify hostglobaldisk continuity. Dockerimageprune aftereachrun, no volume/unrelatedcontainer pruning. No installs/builds/pulls/whole-project/tmp copies, no scratch or Nextoutputs, no evidence/user data deletion; nothing temporary toremove. Retain ownstate/sourcearchives deliberately.

## Bước tiếp phù hợp

Implement **isolated** sensor-capability-loss/command-authority contract by mock/fault first, then SITL: unavailable must not mean pathclear; intervention policy must be versioned and actual stopping observed, not inferred from ACK. It must distinguish AERIS-owned control from physical radio, and require explicit authority revalidation aftersensor recovery. See SIMDROP77-SAFETY-FOLLOWUP.md, proposal only. No production mitigation deployed here. Hera dynamics/sensors/FOV/noise/HID, multiobstacles/wind/payload, native/Fly and SIM32pacing remain separateNOT_CHECKED gates.

Main receipts: campaign-summary.json, cold-run01/02/03/06.json, run04/05-closure-incident.json, bites.json, drain-mock.json, closure-fix-qualification.json, allraw/sourcearchives/closure receipts, final-verification.json and artifact-manifest.json. Original strict summary.py remains, summary-v2 discloses mixedcollector revisions. Newcode only under pilot/simdrop77; all source facts/SOT frozen.
