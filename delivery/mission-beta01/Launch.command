#!/bin/zsh
set -eu
cd "${0:A:h}/../.."
exec python3 -B delivery/mission-beta01/launch.py "$@"
