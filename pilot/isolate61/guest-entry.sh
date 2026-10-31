#!/bin/sh
set -eu
/instrument/clockprobe &
clock_pid=$!
trap 'kill "$clock_pid" 2>/dev/null || true; exit 0' TERM INT
export AERIS_DIRECT_TRACE=1
case "$AERIS_TRACE_MODE" in
 bind) export AERIS_AP_TRACE=/evidence/ap-timing.bin ;;
 tmpfs) export AERIS_AP_TRACE=/ap-trace/ap-timing.bin ;;
 *) exit 41 ;;
esac
"$@" &
ap_pid=$!
printf '%s\n' "$ap_pid" > /state/ap.pid
python3 -B /diagnostics/guest-observer.py /state/ap.pid /probe &
observer_pid=$!
set +e
wait "$ap_pid"
ap_code=$?
printf '%s\n' "$ap_code" > /state/ap-exit-code
wait "$observer_pid"
observer_code=$?
printf '%s\n' "$observer_code" > /state/observer-exit-code
# Writer is reaped, observer sealed. Keep volatile trace available for verified export.
while :; do sleep 1 & wait $!; done
