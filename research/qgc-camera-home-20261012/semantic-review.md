# Semantic review · QGC03 / single agent

Six claims from five pinned public captures; A-tier means official source, not measured device capability. Context around appendStopTakingPhotos proves sequential206(distance0, flag0) then2001(camera0, reserved NaN); scanner requires this adjacency. AP_Mission_Commands confirms206 flag1 calls take_picture independently of distance and2001(camera0) stops capture on available backends. AP_Mission stores only camera ID for2001; bounded reserved null→zero is explicitly recorded in adapter, not generally allowed for other commands.

Actual QGC03 corpus confirms numeric reserved0→null on initial test, camera flags stable with proper stop-pair, Home10→7 and duplicate doJumpId labels. Later null-reserved derivative saves differ only in Home under strict semantic comparison; repeated QGC save stable. These observations are evidence, not refinery fact promotions. Home terrain setter is a plausible source explanation;7m is not an approved operational datum. No generic guarantee across versions/devices.

DataFlash CMD records are a mission inventory dump at startup/arm, NOT per-command execution timestamps. CAM records show simulator trigger events; no physical images. Flight completion/readback/journals and simulated CAM data are distinct evidence scopes.
