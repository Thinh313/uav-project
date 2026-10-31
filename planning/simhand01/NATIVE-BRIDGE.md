# SIM-HANDOFF01 development bridge

APK package `vn.rtr.aeris.simhand01`, default `http://127.0.0.1:8896/phone`. USB reverse8896 only. Optional explicit `initialPath` allowlist `/phone`, `/observer`, `/` supports owned emulator visual QA; no arbitrary URLs. HTTP localhost8896 is the only allowed WebView origin. No flight driver, ARM or authority persistence exists in Java.

`JSON.parse(window.SimNative.environment())` returns `{format:'aeris-simhand01-native',version:1,platform:'ANDROID',instance,session,foreground,package,authorityRestorable:false}`.

`window.SimNative.request(JSON.stringify({version:1,id:instance+':'+monotonicPositiveSequence,instance,session,action,args}))` accepts exactly six envelope fields. One active operation, no queue; foreground/session/origin and replay fences. Reply callback `window.simNativeReply(resultObject)` receives `{version,id,instance,session,action,ok,result|error}`. Android invokes this callback with a parsed object, not a string.

Actions:

- `export-session`: args `{body,bodySha256}`. Body is UTF8JSON<=32MiB, version1, format beginning `aeris-simhand01`, authorityRestorablefalse. Opens ACTION_CREATE_DOCUMENT; readback bytes/SHA must match. Returns `SAF_READBACK_VERIFIED`, bytes/hash/platform, authorityRestoredfalse.
- `import-session`: args `{}`. Opens ACTION_OPEN_DOCUMENT, JSON<=32MiB. Returns body/hash with status `PICK_READ_VERIFIED_UNTRUSTED_REQUIRES_HOST_VERIFY`. UI must POST the parsed package to `/api/verify-package` and display historical results only. Native readback does not prove semantic integrity or restore authority.
- `load-workspace`: args `{}`. Returns own-package CAS snapshot `{status,head,body,bodySha256,platform,authorityRestored:false}`.
- `save-workspace`: args `{body,bodySha256,expectedHead}`. JSON<=2MiB, same simulation namespace/version/authority constraint. At most16 immutable generations/8MiB total; no automatic evidence deletion. Explicit save only. Never restore control rights from these bytes.

`sim-native-background` event fires on Android pause, including SAF picker ownership. UI must revoke control on this event, blur, visibility loss and pointer cancellation. Returning from a picker never silently grants control. All context/authority decisions remain server-side; native bridge has no flight action.

Actual phone testing stays NOT_CHECKED until the user selects a connected physical USB serial. No physical-root operation is provided.
