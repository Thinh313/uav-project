#!/bin/sh
set -eu
/instrument/clockprobe &
if [ "${AERIS_INSTRUMENT:-0}" = "1" ]; then
 export AERIS_DIRECT_TRACE=1
 export AERIS_AP_TRACE=/evidence/ap-timing.bin
fi
exec "$@"
