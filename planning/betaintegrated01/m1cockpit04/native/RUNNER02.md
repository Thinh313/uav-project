# Selected native revision02

This addendum supersedes revision01 capacity and case ordering; unchanged Android API/selectors/private paths remain documented in RUNNER.md. Historical APK01/source archive and prior partial evidence remain intact.

- Selected APK: `native/betaintegrated01/cockpit04/dist/aeris-cockpit04-development-02.apk`, SHA256 `3273c9cb3fec67f2b1598761eaf4b02bde27097babeea162d3482fd925c3fd45`.
- Source SHA256: `818ce113664ca7433ca9cd98eaa70b64f1187f71bb99084263bcb3c8d3ab748f`; receipt `evidence/betaintegrated01-m1cockpit04/native/build-02.json`.
- Native Owner03 algorithm exact except one capacity constructor argument128→160MiB. Stream reader allraw cap160MiB. Segment1MiB, max256, row32KiB and all CRC/SHA/latest-ground conditions unchanged. Shared NativeSegments implementation unchanged. Source identity explicitly says `OWNER03_ALGORITHM_CAPACITY160_SHADOW`.
- Package `vn.rtr.aeris.cockpit04/.CockpitActivity`; expected bundle01/run-profile02/typed-profile01 and all UI, Config2000, touch20Hz,200ms lease,500ms loop,200ms RX-apply and preflight/Home guards unchanged.
- Root selected ONE combined case: actual preflight/manual/UP→BRAKE/release/newneutral lease, continuous assisted BRAKE hold with real native20Hz neutral sampler for >=1802s, then intentional link cut, passive failsafe/ground proof and restart without authority. This is not held-forward loss and not continuous manual stick deflection.
- Native AVD growth512MiB now reserves160MiB native +352MiB system. One bounded host native export <=168MiB, inside cumulative192MiB cap; no whole history export or full second untar.
- Actual30m remains NOT_RUN until Root power, disk/admission, clocks, allraw replay, intended-fault and recovery oracles pass. Build/mock counts and lifetime2000 do not prove runtime duration. Root alone owns ADB/AP/Android launches.
