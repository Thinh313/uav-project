# Accurate English-only OCR bounded check

22/10/2026. QA-only source `qa-ocr-en.swift` and new `.local/cockpitvideo04/qa-ocr-en` compiled using the existing task Swift cache. No prior binary/helper or app source changed; no ADB/UI/runtime was invoked. Binary SHA256 `f6afde57ea85553430f634ed6aba249ac14b03b37e50c4dad7c38b969778f0c3`.

The helper uses Vision `.accurate`, English-only `en-US`, no language correction. Optional pixel crop accepts `IMAGE X Y WIDTH HEIGHT`; output bounding boxes are translated back to absolute screenshot coordinates.

Existing stored image `android-mock-actions-visible01.png` SHA256 `32a51bdaa88bdd1acbb6fd0d1430d1f1700b0e8eb8cf7436545abba0937481a2` was tested with right-console crop `(700,70,530,650)` and full image, each under a strict3s subprocess timeout.

- Default sandbox runs returned fatal `Foundation._GenericObjCError.nilError` without OCR rows in695ms/308ms. Preserved `qa-ocr-en-check01.json`; quick exit is not successful OCR.
- Approved readonly unsandboxed comparison on the same binary/image hit the3s timeout for both crop and full image (about3005ms each), and the owned subprocess was killed. Preserved `qa-ocr-en-check02.json`. This does not establish the root cause of the different sandbox behavior or prove eventual OCR accuracy.

**Disposition: MANUAL_ONLY for the live Home/parameter confirmation window.** Accurate English OCR has not demonstrated reliable≤3s latency here. Do not substitute an unbounded retry or garbled fast-English result for semantic control identification. Root should use its fresh screenshot, explicit visible control coordinates and immediate readonly AUTO-gate check; preserve >1800ms threshold and actual user gesture. Re-evaluate OCR separately outside an active flight/gate if later authorized.

Existing qa helpers still point to their original binary and remain unchanged. Keep this failure evidence. Remove the new qa-ocr-en binary and task Swift cache with the other owned OCR artifacts at final cleanup; no further OCR/model warm-up loop is authorized by this preparation.
