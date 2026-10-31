# FIELD02 repair01 authority/UI Builder closure

22/10/2026. Source/mock work is complete; **FIELD02 live acceptance remains NOT READY**. This closure is read-only, starts no emulator/AP and changes no product source or prior evidence.

Final source SHA is recorded in `evidence/field02/repair01/authority-ui-builder-closure01.json`. App `bf244aae…811f1`, gateway `e1555184…b8dd2`, fault helper `7eb19c64…537e`, UI CSS `2265bf33…ada8` and media CSS `35680f8e…943` remain unchanged from Builder freeze. UI module is now `7cefabffa5fd04a5da71306ea4907d6a5016a2e13fdc55bc8a95927f848ceaba`: only the explicitly authorized unused `onState:()=>{}` callback was removed. Reinserting that exact callback reproduces the prior UI SHA. All7 native-source hashes remain exact; APK unchanged.

Evidence supports11/11 Builder mock cases, independent QA10/10 authority and4/4 app-fault groups, plus20/20 approximate mock-PNG contrast samples≥4.96:1. These prove the scoped policy/WAL/source behavior, not live ArduPilot revocation or Android pixel/display qualification. Earlier raster harness failures and old NOT_READY evidence remain retained.

Repair Android launch02 ended with `GUARD_PROTECT20GIB`; observed minimum host free space was **421,421,056 bytes**, below the required floor. Host app07 closed with `RESOURCE_STOP_PROTECT20GIB` and `payloadEvidenceFailure:null`. This is a resource stop, not acceptance or evidence that the20GiB floor held. The source of the host-space collapse is not established by Builder.

The last UI connection request created `m93498c6ac9f741b39d44` with **mode MOCK**. Seven prior SITL requests remain; no new repair01 AP request/start occurred. The extra2 cumulative slots were prepared and mock-tested but unused. Emulator launch budget2/2 is exhausted; no further start is authorized by this work.

Actual active-lease AP reboot with observed before/after rights, and the affected Android restart/persistence/SAF regression were **NOT RUN**. Android DAY fresh/error pixel evidence is not claimed by Builder. Root must retain these gaps and all video results separately rather than infer success from mock receipts, a restarted viewer or a MOCK connection.

Own Swift cache/binary were already removed; all receipts, fixtures and historical files are retained. No source/candidate/ENDURE changes, no native build/signing, no Xiaomi/Hera or production qualification.
