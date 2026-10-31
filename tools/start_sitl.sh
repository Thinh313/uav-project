#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
# Fixed task-owned name. Never remove or reconfigure an existing container implicitly.
if docker container inspect aeris-sitl >/dev/null 2>&1; then
  echo 'aeris-sitl already exists; inspect or stop that task-owned simulator explicitly.' >&2
  exit 1
fi
profile=${AERIS_SITL_PROFILE:-normal}
case "$profile" in
 normal) defaults=/aeris/copter.parm,/aeris/aeris.parm; speedup=5 ;;
 failsafe) defaults=/aeris/copter.parm,/aeris/aeris.parm,/aeris/failsafe.parm; speedup=2 ;;
 *) echo 'Unknown simulator profile' >&2; exit 1 ;;
esac
docker run --rm -d --name aeris-sitl --platform linux/amd64 --network bridge \
  --cpus 2 --memory 512m --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:5760:5760 -v "$PWD/runtime/sitl:/aeris:ro" \
  -v "$PWD/runtime/sitl/state:/state" -w /state \
  ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55 \
  /aeris/arducopter -w --model quad --home 10.854,106.807,10,0 \
  --defaults "$defaults" --speedup "$speedup"
