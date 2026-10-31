# NATIVE31 / signed NATIVE30 development handoff

`dist/aeris-native30-development.apk` is a separately signed development APK derived from N30. Package `vn.rtr.aeris.shell30`, version31 / `0.3.1-native30-development`, declared min API26 / target33. These declarations are not runtime compatibility results. Debuggable, zero requested permissions, no flight or radio output. Dedicated certificate, not a release or candidate signature.

`build.py` reads the old module without changing it. Receipt `evidence/native31/build02.json` identifies original and compiled Java/assets. Derived Activity enables local WebView QA debugging and dispatches a focus event on resume; it does not restore preflight or mock-run authority. Engineering labels replace unsigned labels. DraftStore uses the N30 fixed `File.getUsableSpace` code unchanged. Android retest of that fix is still NOT_CHECKED.

The user chose to retain current disk capacity and receive the APK/host checks. No emulator was launched. The first image extraction crossed20GiB; it is recorded rather than presented as a successful storage gate. SDK/image/AVD/build/host-test scratch was removed. Do not rerun the old N30 runtime script: it would overwrite the preserved failure evidence.

Future runtime admission requires at least28GiB host free space, a full uncompressed-footprint budget and continuous headroom observation. Only an explicitly owned emulator may be targeted. Required retests: actual ART31 journal checks and three SIGKILL boundaries; installed Activity/bridge; app-private saved invalid and valid drafts after force-stop/reboot; fresh compile/Home/datum before mock Fly; ACK versus progress, landing and review history; background/resume, window/keyboard, SAF export/import. None is established by signing or host regressions.

Development private key/password remain separately in `.local/native31`, permissions600 in a700 directory. Public certificate is included; private material is not part of the handoff. Frozen software release/trust/ENDURE paths are not used by the signing helper.
