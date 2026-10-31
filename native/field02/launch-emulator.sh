#!/bin/zsh
set -euo pipefail
cd "${0:A:h:h:h}"
export ANDROID_AVD_HOME="$PWD/.local/field02/avd"
export ANDROID_SDK_ROOT="$PWD/.local/native86-android/sdk"
exec "$ANDROID_SDK_ROOT/emulator/emulator" -avd aeris-field02 -port 5582 -no-snapshot -no-boot-anim -no-audio -gpu host -no-metrics
