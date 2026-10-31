export const REFERENCE={
  "format": "aeris-firmware-reference38",
  "version": 1,
  "sourceVersion": "ArduCopter 4.7.1 source reference",
  "flightSwVersion": 67568127,
  "sourcePins": {
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/version.h": "4c2c92e9bdc08021aa08785b61eac9d1fddec71a32b9bf495497715a742d5d71",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/Parameters.cpp": "4a4248b8395b16dc17551819206add0dc38c1badab585099c3b5374288458fe0",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/Parameters.h": "ced7e879058e687167b3a3bda6ceda5b2f46f279abc59bf22802171ebf6cd1b2",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/defines.h": "916d2aca9b3407aa6af2b47fd508a153228d257b28be840162c843e20a8ef151",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/Copter.h": "b05855994742ef2d00ce7a43e146dca656a47fa6f4d9a06a62c0104533f335ae",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/events.cpp": "217070ca162fcc2e2206f32b90b0d0c66de7e71c3644bd0c7e857bbb43f8743d",
    "runtime/sim32-instrument01-build/ardupilot/ArduCopter/ekf_check.cpp": "b5de5ccd801c77e43bc430d1be8a4a122520e54214c4ca78072a9d19911c1544",
    "runtime/sim32-instrument01-build/ardupilot/libraries/GCS_MAVLink/GCS_Common.cpp": "a940c630d50ff2bf2339ebff21fae998445ae8c52cb74091ed6b40cc1142a48e",
    "runtime/sim32-instrument01-build/ardupilot/libraries/GCS_MAVLink/GCS_Param.cpp": "668b245bf81cb9b3545b3751a08106a9086172cb7f0b477ae892b1e1ce3a1b83",
    "runtime/sim32-instrument01-build/ardupilot/libraries/GCS_MAVLink/GCS_MAVLink.cpp": "9819f92302f16b4d740933608cdba5dde49536a857ea92090a850708c0eee339",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AC_Fence/AC_Fence.cpp": "9fa580a04c7f0ef1b4885892100450ac75fef1e88ef924d6486313bb2989ecd1",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AC_Fence/AC_Fence.h": "cafef13186db1af1c19c64b3501765f356748dd6389a3e2bcbcd3e9e4ca198a7",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AP_Common/Location.h": "efd4d2cdc68b3f7e1d072fd011e06be6d118c7fac710ebb27df77dc15dad42cd",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AP_BattMonitor/AP_BattMonitor_Params.cpp": "c674aab5ff5631b1c19e9e556a23d7386cb2f89e57b807d2a70060c6096f0563",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AP_BattMonitor/AP_BattMonitor_Params.h": "99c0feafe78c81bd2cdff6513f9514c39218983c17727f6a549542cea07cb3be",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AP_BattMonitor/AP_BattMonitor_Backend.cpp": "7bdd36075399a1b610d0fa2deb7f163ddb96400128fb1110d2a15af19818ac0e",
    "runtime/sim32-instrument01-build/ardupilot/libraries/AP_Param/AP_Param.h": "dc14bcd0742df6a26355593268a27b22a09d1d0df9c4f1a765ac7942ac7da4e5",
    "runtime/sim32-instrument01-build/ardupilot/libraries/RC_Channel/RC_Channels_VarInfo.h": "8ebebfb28ad7c971500d8cbfb9ddf5c8296d4b318d5a4b205586d40540125e34",
    "reference/mavlink/standard.xml": "64af1ee5538344782abf8b35cf199a6cd48aa06eeb6bd41c7ae31f740a06a7f3",
    "reference/mavlink/common.xml": "4d28a24ec264591318181fb3e275fa56c3fcc748af83cb9e16540ac5af1f8755"
  },
  "sourceBundleSha256": "a1a2352c2fe6d50d3b73d6d9ab0bf8ca3dec2bc397f1902d3761e7b7e8f85b0c",
  "legacyParameterEncoding": "PINNED_AP_C_CAST_FROM_SOURCE",
  "parameters": {
    "FENCE_ENABLE": {
      "type": 2,
      "unit": "bool",
      "min": 0,
      "max": 1
    },
    "FENCE_TYPE": {
      "type": 2,
      "unit": "bitmask",
      "min": 0,
      "max": 15
    },
    "FENCE_ACTION": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 5
    },
    "FENCE_OPTIONS": {
      "type": 4,
      "unit": "bitmask",
      "min": 0,
      "max": 7
    },
    "FENCE_AUTOENABLE": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 3
    },
    "FENCE_ALT_MIN": {
      "type": 9,
      "unit": "m",
      "min": -500,
      "max": 10000
    },
    "FENCE_ALT_MAX": {
      "type": 9,
      "unit": "m",
      "min": -500,
      "max": 10000
    },
    "FENCE_ALT_MIN_TP": {
      "type": 2,
      "unit": "AP_LOCATION_FRAME",
      "min": 0,
      "max": 3
    },
    "FENCE_ALT_MAX_TP": {
      "type": 2,
      "unit": "AP_LOCATION_FRAME",
      "min": 0,
      "max": 3
    },
    "FENCE_MARGIN": {
      "type": 9,
      "unit": "m",
      "min": 0,
      "max": 50
    },
    "FENCE_MARGIN_XY": {
      "type": 9,
      "unit": "m",
      "min": 0,
      "max": 50
    },
    "FS_GCS_ENABLE": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 7
    },
    "FS_GCS_TIMEOUT": {
      "type": 9,
      "unit": "s",
      "min": 0,
      "max": 60
    },
    "FS_THR_ENABLE": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 7
    },
    "RC_FS_TIMEOUT": {
      "type": 9,
      "unit": "s",
      "min": 0,
      "max": 60
    },
    "FS_OPTIONS": {
      "type": 6,
      "unit": "bitmask",
      "min": 0,
      "max": 63
    },
    "FS_EKF_ACTION": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 3
    },
    "BATT_MONITOR": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 32
    },
    "BATT_CAPACITY": {
      "type": 6,
      "unit": "mAh",
      "min": 0,
      "max": 200000
    },
    "BATT_LOW_TYPE": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 1
    },
    "BATT_OPTIONS": {
      "type": 6,
      "unit": "bitmask",
      "min": 0,
      "max": 511
    },
    "BATT_LOW_VOLT": {
      "type": 9,
      "unit": "V",
      "min": 0,
      "max": 100
    },
    "BATT_CRT_VOLT": {
      "type": 9,
      "unit": "V",
      "min": 0,
      "max": 100
    },
    "BATT_LOW_MAH": {
      "type": 9,
      "unit": "mAh",
      "min": 0,
      "max": 200000
    },
    "BATT_CRT_MAH": {
      "type": 9,
      "unit": "mAh",
      "min": 0,
      "max": 200000
    },
    "BATT_LOW_TIMER": {
      "type": 2,
      "unit": "s",
      "min": 0,
      "max": 127
    },
    "BATT_FS_LOW_ACT": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 7
    },
    "BATT_FS_CRT_ACT": {
      "type": 2,
      "unit": "enum",
      "min": 0,
      "max": 7
    }
  },
  "boundsScope": "engineering mock interpretation, not all firmware metadata ranges",
  "runningFirmwareAssociation": "NOT_CHECKED"
};
