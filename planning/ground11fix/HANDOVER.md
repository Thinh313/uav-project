# Ground11 missing-import repair: source/mock only

The proposal qa-ground-soak.py is derived from frozen G11 with one added `os` import. Every function AST, threshold, clock/renewal/context predicate and authority decision is unchanged. It is not integrated into G11 or any future campaign.

Effective test PASS4 under direct /usr/bin/python3 -B: original collect reproduces NameError before journal/writer; corrected collect reaches the injected journal refusal and writes its finally report; corrected collect completes a synthetic75-second clock interval with151 actual sample decisions, real journal-chain parsing and two real publisher/viewer renewal validations. Full report JSON serialization is bounded and checked. Test imports the exact frozen g11_native_writer first, then both modules reuse that object. Fake UI/clock/pause are explicit; only test evidence directory and report sink are patched. No wall-time wait, runtime/network/Android/AP/ADB/listener/dependency or operational ledger/claim was used. No scratch copy was needed or removed; synthetic journal and reports are retained as mock evidence.

The original failure preceded try/finally, so its actual G11 ground report was absent; controller journal retains the refusal. Prior clock tests imported collect and checked its provider default/static sites without invoking report construction. This regression addresses that coverage gap. Other refusal paths are not newly certified, and mock75s is not actual UI/clock/Android/SITL/reboot/persistence acceptance. Root retains G11 closure and final disposition; no G12 wiring or launch is authorized here.

Original SHA: ec97843a81f052ca425b063b058d2092f348084e64c2383fa1db57011ecedda6

Proposal SHA: 4e12c4888e5b75dbc72f322adf54278f36f373af433a0b2013ef94916eda77be

Frozen writer SHA: c3520ae10128adebd3f3bad0727a160960eca5fb8a4284eaab38621565153e9c

Receipt builder-effective01.json SHA: 9134ddf356c26104ba0b8c56107c0818440abfd605531b2e93a5f96e81472b5f
