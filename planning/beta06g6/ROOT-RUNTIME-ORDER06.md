# Root runtime ordering clarification, G6

22/10/2026. This additive runbook corrects final shutdown wording in frozen BUILDER-NATIVE-HANDOVER06.md without changing its21-file freeze, code, clocks, source/candidate or prior evidence.

Coldboot13 still requires host2 alive and the in-memory pre-stop proof from emulator12, exactly as TIP/ADR. After final cold13 review/native store persistence checks, keep emulator13 alive long enough for the existing stop-host fresh native observation. Stop any source/viewer, inspect zero run/authority/lease and fresh UI; issue stop-host2 with sourceAndViewerStoppedAndInspected:true while13 still running. Verify clean host2 closure. Then issue stop-emulator13 WITHOUT the source-stop flag (cleanup path only, no new persistence boot), wait clean android-closure13/helper exit, then EOF controller. Never stop13 and wait for closure before asking stop-host2 to read its native observation; stopped UI cannot remain fresh. No third host, timeout reset, raised threshold or new effect is introduced.

This correction governs actual Root choreography and must be checked at the independent prelaunch gate. It is not a claim that arbitrary stopped-UI observations or unmanaged restart are supported.
