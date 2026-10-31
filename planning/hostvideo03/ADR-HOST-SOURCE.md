# ADR: receive-only Android video experiment

Status: accepted for isolated engineering implementation by explicit user request22/10/2026. No production or hardware release.

FIELD02 repair01 encoded synthetic camera frames and decoded received video inside the same Android WebView. Its final7.95FPS/573msP95 is a retained failure, with source/output/credit pressure but no proven sole cause. Camera deployments normally deliver an alreadyencodedstream to the controller; this task isolates that intended receiver responsibility.

Use existing laptopChrome publisher and frozen FIELD02 relay/viewer unchanged. New media-only inspection server/receiver lives in pilot/hostvideo03; the unchanged developmentAPK loads it at the fixedloopbackorigin. Do not modify the previous cockpit, candidate, ENDURE, field02 source or native files. No new nativecodec/ffmpeg/dependency download is necessary. A dedicatedpage first proves transport/decode performance; cockpitintegration remains subsequent work.

Tradeoff: source now runs on a different CPU/browser, so changedperformance is a topology result, not a causallycontrolledalgorithm comparison. Clockcalibration between bothbrowsers and Node remains mandatory, using upperbounds. Hostsourcevisibility has separateevidence; Androidcoveragechecks only itscanvas. Transitive frozenclient includes a dormant encodeprobe export; executedreceiverpath nevercalls it or constructsVideoEncoder. This is codepath separation, not a new securityboundary preventing arbitrary publisher access.

Reject alternatives for this scope: newAPK/signature, replacing codecs, loweringresolution/FPS/clockaccuracy, playing prerecordedframes, or changing frozenviewer bootstrap to improve scores. These would mix causalvariables or exceed the explicitrequest.

Pass thresholds and boundedresource/launchbudgets are in TIP.md. Any failedmandatorygate staysNOT_READY. Even fullmediaexperimentPASS cannot close FIELD02's separate APactivelease/reboot or cockpit/SAF regressiongaps. No runtimeAI; LLMbaseline and claimedcommercialsuperiority do not apply.
