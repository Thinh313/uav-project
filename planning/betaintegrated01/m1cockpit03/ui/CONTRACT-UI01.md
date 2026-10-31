# COCKPIT03 glass UI contract, agreed with native Builder

At1280×800 CSS pixels: header0..64; telemetry700..800, firstmetric andRtRlogo
left24. Nativebar96,630..1184,694 visiblePreflight(CONNECT/CLOSE) andFly; pads
100,370..340,610 and940,370..1180,610 onlyFly. WebView remainsbehindnativeoverlays.
Leftnav16..80, four64highrows centeredY382 (centers286/350/414/478). Rightisland
1200..1264 is also centeredY382. Panels andmapcontrols never enter nativezones.
The stage remains a clearly labelled syntheticreference around configuredHome,
not an aerialimage/reallocalmap. No camera/video/photo/payloadclaim.

Design tokens: RtRwhite#f6f7f5, charcoal#101715, muted#c4ceca, daylightink#14211b,
smallgold#e2be54, warning#f1b183. StrongBarlowVI alias uses exactM0intake Barlow
medium/semibold/bold, Vietnamese cmapchecked. Glassblursurface +thinsharededge,
not separateopaquebutton tiles. Navislandsdetached; coremetadataonlyinheader.

Trustednativeassetdocument, no network, eval or importedlegacydispatch. Bridge:
`AerisWorkspace.post(JSON.stringify({version:1,id:'ui-'+viewEpoch+'-'+counter,
viewEpoch,type,payload}))`. Types LOAD/SAVE_DRAFT/NAVIGATE/STATE/REVIEWS only.
StrictmonotonicUIcounter; nativeboundedworker8. Callback
`window.AerisCockpit.receive(object)` schema version1,id,viewEpoch,ok,type,data,error.
BOOT/LOAD unsolicitedonce establishesrandompositiveActivityepoch. PUSH/STATE
read-only updates requirecurrentepoch andincreasingnative nowElapsedNs. Request
responsesmustmatchcurrentpendingid/type/epoch; noautomaticretry. NativechosenView
is sole navigation authority. Dirtyunsaveddraftblocks UI NAV untilsavedsuccess;
Java independentlyblocks editing/navigation whilearmed/granted.

Data: chosenView,viewEpoch,workspace{draft,draftSHA256,reviews,authorityRestorable:false},
native,nowElapsedNs,nativeObservedElapsedNs,noMedia:true. Telemetryuses actualnative
flight.positionMs/heartbeatMs andguestnow, pluslocalarrivalage, never synthetic
numbers. Unknown/stale>1500ms values andpositions displayunknown. Numeric0valid.
Reviewstatuspendingexternalverification remainspending; no completion/coverage
inferred fromgroundcounter. Restartloadsrecords/draftonly, neverauthority.

Stableaccessible navIDs nav-survey/preflight/fly/review andlabels Khảo sát/Trước
bay/Bay/Hồ sơ. Draft IDs draft-name/type/save andlabels Tên khảo sát/Loại hình
khảo sát/Lưu khảo sát. Theme labeltoggles Chuyển sang giao diện sáng/tối with
sun/moon icon. Nativebutton selectors control01-connect/consent/guided/arm/
confirm-home/takeoff/loiter/hold/land/close, ownedbyJava.
