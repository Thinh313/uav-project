#!/bin/sh
set -eu
pid=$(cat /state/ap.pid)
case "$pid" in ''|*[!0-9]*) exit 43 ;; esac
if [ ! -f /state/ap-exit-code ]; then kill -TERM "$pid"; fi
n=0
while [ ! -f /state/observer-exit-code ]; do
 n=$((n+1)); [ "$n" -lt 100 ] || exit 44
 sleep .05
done
[ "$(cat /state/observer-exit-code)" = "0" ]
