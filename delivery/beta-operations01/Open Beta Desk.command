#!/bin/zsh
set -eu
BASE="$(cd -- "$(dirname -- "$0")/../.." && pwd)"
cd "$BASE"
exec node "$BASE/pilot/betaops01/server.mjs"
