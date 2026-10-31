#!/bin/zsh
set -eu
cd "$(dirname "$0")/../.."
exec python3 -B planning/simhand01/launcher.py stop
