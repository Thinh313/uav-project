# P2 CREW02 – hai phiên operator và nhiều payload

Ngày 20/10/2026. Contractor: root; Builder và QA là hai agent riêng. Skill: personal Vibecode Kit6.3. Scope được chủ việc ủy quyền; development signing/ADB chỉ emulator-5582 được tái dùng. Không production signing, thiết bị thật, SDK hay ENDURE campaign mới.

## Outcome và baseline

Một phi công trên cockpit Android và một operator payload trên companion chạy ở tiến trình host độc lập, cùng điều khiển một máy bay SITL và nhiều camera/gimbal tổng hợp qua một native gateway. Hai phiên có danh tính được kiểm bằng crypto, state/selection/liveness riêng, bàn giao theo consent và không tự lấy lại quyền sau lỗi/restart. P1 đã chứng minh bay+payload nhưng hai actor ở cùng runtime và tự chọn actor, chưa có peer authentication. AUTH73/KEY74/DUAL67 là mock/contract, không phải chứng cứ identity thật. Phase One/Hera thật và release thương mại giữ gate P5/P6.

Giá trị đo: task completion của hai runtime, route đúng, quyền/expiry đúng, không retry/lệnh trái phép, không cần restart để thao tác hợp lệ; ghi latency/bounds thực tế. Direct LLM baseline không áp dụng transport xác định. Không suy thành hơn DJI hoặc chứng nhận an toàn.

## Kiến trúc chốt (ADR P2)

- Namespace mới native/crew02 (vn.rtr.aeris.crew02), evidence/crew02*, planning/crew02, delivery/COMPLETION-CREW02.*. Chỉ copy có chọn lọc source/assets cần dùng từ P1, ghi provenance. Không đổi native/operator01 hay bất kỳ baseline/P1/evidence cũ. Contractor viết spec/harness/report, Builder viết production.
- Một Android native gateway duy nhất sở hữu ArduPilot socket, RX, wire sequence, WAL/fsync và last-wire policy. Không thêm GCS hay router bay thứ hai. Node B là tiến trình độc lập, key/boot/session/storage/selected payload riêng, cockpit UI localhost. Host UI không nhận private key. No peer-to-autopilot wire bypass.
- Hai trust boundary: pilot A lấy từ native app context, không nhận actor/sid tùy ý từ JS; payload B lấy từ TLS peer cert đã admin pin. B không được aircraft scope, không gọi bridge A qua HTTP. Disable toàn bộ đường legacy tự chọn actor/sid và auto-heartbeat cả hai.
- Standard mTLS, guest SSLServerSocket bind127.0.0.1:5942, needClientAuth=true, TLS1.2/1.3 only, task-owned adb forward loopback5942→5942. Node UI riêng loopback8850 nếu port trống, Host/Origin/CSRF strict. Không LAN, plaintext fallback, trust-all, rejectUnauthorized:false.
- Android P256 key tạo trong AndroidKeyStore, SHA256, subject CN=localhost,O=RtR Engineering, certificate validity rõ; kiểm selfsignature/cert/hostname thực. Public cert/SPKI xuất được, private key không xuất. Ghi actual security level, emulator không attestation.
- B dùng test EC cert/privatekey riêng từ OpenSSL hiện có, private0700/0600 ngoài evidence/APK/export/VCS. Admin out-of-band manifest pin exactcert/SPKI→principal/role/scopes/realm/aircraft/trustepoch trước listen. NoTOFU/selfenrollment. Node giữ default hostname validation và thêm SPKI check; pin Android public cert. Validity kiểm wallclock, authority lease kiểm Android monotonic. Thay trust/epoch/revoke phải vô hiệu hóa cả livechannel/ticket.
- Framing4byteBE length: request1..16384, compact response≤32768; max2 activeworkers, zero unbounded queue. Handshake≤5s; frame absolute deadline≤3s từ byte đầu, không sliding slow-drip. StrictUTF8, flat bounded JSON schema, reject duplicate/unknown keys, trailing tokens, nonfinite/unsafe integer, invalid types. Crypto/parsing/network offmain and outside RX lock. Không canonicalJSON crypto: request rawbytes SHA là binding, TLS chứng minh possession/integrity, logs không là signed nonrepudiation.
- HELLO/clientboot + fresh serverchallenge/boot/realm/aircraft/trustepoch/channelid; JOIN explicit echo. Auth alone grants nothing. Mọi mutation bind nativeprincipal, server/clientboot, session, trustepoch, AP generation, seq strictly increasing, expected revision, op/resource/body digest. No caller actor/sid override; one inflight action per channel. Response loss =>UNKNOWN/read-only reconcile, no retry/resume.
- Independent scopes aircraft (A only), camera:<front|center|rear>, gimbal:<front|center>. Claim/release/propose/recipient explicitaccept use CAS current revision; transfer freezes scope old wire, pending oldintent UNKNOWN; no inherited pending action. Selection/video switching is local presentation only. Any bundle operation must atomicall-or-revoke, never partial silentgrant.
- Own-runtime heartbeat500ms, native monotonic presence expiry3000ms; no proxy heartbeat. AP freshness1500ms/hardloss3000ms retained. B partition/death revokes B scopes only while A AUTO can continue. A presence/foreground loss closes common GCS transport/stops heartbeat so B cannot mask pilot loss. Common AP/transportloss/reboot closes all authorities/UNKNOWN. Reconnect/newboot requires fresh join/consent, never restore authority from files.
- Keep WireGate95 AUTO_REQUESTED→AUTO_OBSERVED deadline1500ms and original flight safety semantics. Preserve native1001 generation-wide component154 fence, GCS255/190 manager identity. Do not reconfigure1001 to show operator handover or device2 samegeneration. Two manager device proofs may use separate generations; multiple cameras must work concurrently in one generation. ACK never execution or operator identity.
- Durable intent before wire and after-WAL recheck current principal/session/epoch/scope/CAS/generation/foreground/freshness. Lock order transport serialization then bounded Crew state; never Crew lock waiting transport. Invalidation before send must produce no wire. Bind principal/keyfingerprint/channel/session/request digest to native raw wire record. No automatic retry or evidence deletion. Quota full =>fail closed, preserve existing records.

## Mandatory AC (all required for P2 READY)

| AC | Hành vi cần chứng minh | Evidence và phép kiểm độc lập |
|---|---|---|
| C01 | Hai runtime thật, Android A + Node B, boot/session/key/selection riêng | PID/process/APK/source pins, actual UI screenshots, distinct peer identity/channel; không hai card local |
| C02 | mTLS peer auth/hostname/pin/validity hoạt động thật | actual negotiated TLS/cipher/fingerprints, valid session; wrong client key/unknown cert/wrong serverpin/plaintext refused before admission; no secrets exported |
| C03 | Strict framing/session/replay/revision/generation protection | held-out malformed/duplicate/UTF8/oversize/drip/staleboot/seq/CAS/wronggeneration cases; zero unauthorized wire |
| C04 | Aircraft A only; camera/gimbal scopes independent and correct | B aircraft rejected; independent camera/gimbal owner; selection/feed changes no grants; post-WAL revoke inject no wire |
| C05 | Handover needs current recipient consent, freezes old owner | two-runtime proposal/accept; oldowner command and conflict/CAS denied; no pending/authority inheritance |
| C06 | Multiple payload routing and real command semantics | one generation front100 + center102/rear101 capture/zoom/focus; gimbal154/device1 or2 explicit; independent raw decoder of values/units/targets/sequence; synthetic fixture, actualImages0 |
| C07 | Nominal Android–SITL mission with both crew active | preflight/upload/readback/AUTO observed/airborne payload; safe ground+disarm+review; native-only GCS and raw TX/RX/WAL proof |
| C08 | B partition/death while A active | B grants revoked ≤3s plus bounded timer tolerance≤250ms, pending UNKNOWN; A mission continues; B reconnect auth fresh but no authority; old queued requests cannot transmit |
| C09 | A loss/common AP loss/reboot cannot be hidden by B | mock loss/reboot + real SITL pilot/link-loss scenario; all grants closed/UNKNOWN, native heartbeat stops and AP failsafe observed; no auto reconnect/claim/retry |
| C10 | Restart/persistence/export honesty | process restart and emulator coldboot, records chain/hash retained; fresh boots and no grants/pending replay; prior apps' protected private bytes exact; independent raw export receiver |
| C11 | UI usable/clear and bounded | visible own identity, owner and pending consent per selectedscope, UNKNOWN/source age, no mock image counted real; glass visual retained; no overlap on1280×800 and companion viewport; no stale1001 enabled illusion; quotas don't auto delete |
| C12 | Preservation/resources/reproducible delivery | full legacy+P1 SHA before/after, disk≥20GiB, no new downloads, owned-runtime managed closure, source/APK/devcert/fixture pins, QA disposition no P0/P1 open |

Raw evidence and independent decoder control assertions; ACK, UI text, endpoint logs, cryptographic auth and actual execution are distinct. QA prepares held-out vectors before Builder sees their values. Structural/AI review is not human flight/customer acceptance.

## Budget, stop và sequencing

1. Contractor full preservation before source writes. Builder mock/unit/cross-language crypto+framing then QA source/held-out. No runtime start by agents.
2. Contractor verifies source/pins/budget before bounded development build and runtime. Existing SDK/AVD only. Admission≥26GiB, all phases retain20GiB; runtime guard20.5GiB, stop planned on ground where possible, no further work belowfloor.
3. New aggregate budget≤2GiB; APK≤20MiB each, <=3 causal build iterations before reassess; new evidence≤768MiB; raw streams bounded32MiB/run, <=3 planned SITL windows≤900s each. Android2048MiB/2CPU and AP2CPU/512MiB; Node128MiB. Existing images only. No automatic HTTP/command/run retry. Failures retained and next attempt needs causal repair and budget check.
4. Root owns runtime launch/stop, QA read-only/host held-out tests. Builder may run bounded mock/toolchain compilation inside new namespace; before APK BUILD must notify root source ready. No simulator/AVD/ADB startup by agents.
5. Complete all AC and independent receiver/QA, fingerprint source/evidence/report; stop owned processes, remove only own build caches/unsigned APK after signed payload equivalence, docker image prune-f (no volumes/containers). Do not erase valid intermediates or failed evidence. Hardware/P5/P6 remain explicit gap.

## Delivery

Builder Completion links implemented scope, code/build/test pins, failures and limits. QA separate report with held-out/actual evidence disposition. Contractor Completion/Verify has outcome,12AC coverage, scenario results, technical health, value evidence, limits and READY/NOT READY. Only READY after all mandatory AC pass. Target ambition remains competitive product, not claim of surpassing DJI from this lab milestone.

Official reference context (APIs, not tested capability): AndroidKeyStore https://developer.android.com/privacy-and-security/keystore ; KeyGenParameterSpec https://developer.android.com/reference/android/security/keystore/KeyGenParameterSpec ; NodeTLS https://nodejs.org/docs/latest-v24.x/api/tls.html .
