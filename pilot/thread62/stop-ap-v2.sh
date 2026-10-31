#!/bin/sh
set -eu
pid=$(cat /state/ap.pid)
case "$pid" in ''|*[!0-9]*) exit 43 ;; esac
forced=false
if [ ! -f /state/ap-exit-code ]; then
 kill -TERM "$pid"
 n=0
 while [ ! -f /state/ap-exit-code ] && [ "$n" -lt 20 ]; do n=$((n+1)); sleep .05; done
 if [ ! -f /state/ap-exit-code ]; then kill -KILL "$pid"; forced=true; fi
fi
n=0
while [ ! -f /state/observer-exit-code ]; do n=$((n+1)); [ "$n" -lt 100 ] || exit 44; sleep .05; done
printf '{"forcedApChildKill":%s,"afterBackendClosed":true,"notFlightCompletion":true}\n' "$forced" > /state/stop-policy-v2.json
[ "$(cat /state/observer-exit-code)" = "0" ]
