// Derived from pinned official XML; see schema-generation.json.
export const DEFINITIONS={
  "0": {
    "name": "HEARTBEAT",
    "crc": 50,
    "min": 9,
    "max": 9,
    "fields": [
      {
        "name": "custom_mode",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "autopilot",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 5
      },
      {
        "name": "base_mode",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 6
      },
      {
        "name": "system_status",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 7
      },
      {
        "name": "mavlink_version",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      }
    ],
    "xmlOrder": [
      "type",
      "autopilot",
      "base_mode",
      "custom_mode",
      "system_status",
      "mavlink_version"
    ]
  },
  "33": {
    "name": "GLOBAL_POSITION_INT",
    "crc": 104,
    "min": 28,
    "max": 28,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "lat",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "lon",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "alt",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "relative_alt",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "vx",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cm/s",
        "invalid": null,
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "vy",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cm/s",
        "invalid": null,
        "multiplier": null,
        "offset": 22
      },
      {
        "name": "vz",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cm/s",
        "invalid": null,
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "hdg",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "cdeg",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 26
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "lat",
      "lon",
      "alt",
      "relative_alt",
      "vx",
      "vy",
      "vz",
      "hdg"
    ]
  },
  "1": {
    "name": "SYS_STATUS",
    "crc": 124,
    "min": 31,
    "max": 43,
    "fields": [
      {
        "name": "onboard_control_sensors_present",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "onboard_control_sensors_enabled",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "onboard_control_sensors_health",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "load",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "d%",
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "voltage_battery",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "mV",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 14
      },
      {
        "name": "current_battery",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cA",
        "invalid": "-1",
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "drop_rate_comm",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "c%",
        "invalid": null,
        "multiplier": null,
        "offset": 18
      },
      {
        "name": "errors_comm",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "errors_count1",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 22
      },
      {
        "name": "errors_count2",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "errors_count3",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 26
      },
      {
        "name": "errors_count4",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 28
      },
      {
        "name": "battery_remaining",
        "type": "int8_t",
        "array": 0,
        "extension": false,
        "unit": "%",
        "invalid": "-1",
        "multiplier": null,
        "offset": 30
      },
      {
        "name": "onboard_control_sensors_present_extended",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 31
      },
      {
        "name": "onboard_control_sensors_enabled_extended",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 35
      },
      {
        "name": "onboard_control_sensors_health_extended",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 39
      }
    ],
    "xmlOrder": [
      "onboard_control_sensors_present",
      "onboard_control_sensors_enabled",
      "onboard_control_sensors_health",
      "load",
      "voltage_battery",
      "current_battery",
      "battery_remaining",
      "drop_rate_comm",
      "errors_comm",
      "errors_count1",
      "errors_count2",
      "errors_count3",
      "errors_count4",
      "onboard_control_sensors_present_extended",
      "onboard_control_sensors_enabled_extended",
      "onboard_control_sensors_health_extended"
    ]
  },
  "20": {
    "name": "PARAM_REQUEST_READ",
    "crc": 214,
    "min": 20,
    "max": 20,
    "fields": [
      {
        "name": "param_index",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": "-1",
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 3
      },
      {
        "name": "param_id",
        "type": "char",
        "array": 16,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "param_id",
      "param_index"
    ]
  },
  "22": {
    "name": "PARAM_VALUE",
    "crc": 220,
    "min": 25,
    "max": 25,
    "fields": [
      {
        "name": "param_value",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "param_count",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "param_index",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 6
      },
      {
        "name": "param_id",
        "type": "char",
        "array": 16,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "param_type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 24
      }
    ],
    "xmlOrder": [
      "param_id",
      "param_value",
      "param_type",
      "param_count",
      "param_index"
    ]
  },
  "24": {
    "name": "GPS_RAW_INT",
    "crc": 24,
    "min": 30,
    "max": 52,
    "fields": [
      {
        "name": "time_usec",
        "type": "uint64_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "lat",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "lon",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "alt",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "eph",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": "UINT16_MAX",
        "multiplier": "1E-2",
        "offset": 20
      },
      {
        "name": "epv",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": "UINT16_MAX",
        "multiplier": "1E-2",
        "offset": 22
      },
      {
        "name": "vel",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "cm/s",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "cog",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "cdeg",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 26
      },
      {
        "name": "fix_type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 28
      },
      {
        "name": "satellites_visible",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": "UINT8_MAX",
        "multiplier": null,
        "offset": 29
      },
      {
        "name": "alt_ellipsoid",
        "type": "int32_t",
        "array": 0,
        "extension": true,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 30
      },
      {
        "name": "h_acc",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 34
      },
      {
        "name": "v_acc",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 38
      },
      {
        "name": "vel_acc",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": "mm/s",
        "invalid": null,
        "multiplier": null,
        "offset": 42
      },
      {
        "name": "hdg_acc",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": "degE5",
        "invalid": null,
        "multiplier": null,
        "offset": 46
      },
      {
        "name": "yaw",
        "type": "uint16_t",
        "array": 0,
        "extension": true,
        "unit": "cdeg",
        "invalid": "0",
        "multiplier": null,
        "offset": 50
      }
    ],
    "xmlOrder": [
      "time_usec",
      "fix_type",
      "lat",
      "lon",
      "alt",
      "eph",
      "epv",
      "vel",
      "cog",
      "satellites_visible",
      "alt_ellipsoid",
      "h_acc",
      "v_acc",
      "vel_acc",
      "hdg_acc",
      "yaw"
    ]
  },
  "43": {
    "name": "MISSION_REQUEST_LIST",
    "crc": 132,
    "min": 2,
    "max": 3,
    "fields": [
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 1
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "mission_type"
    ]
  },
  "44": {
    "name": "MISSION_COUNT",
    "crc": 221,
    "min": 4,
    "max": 9,
    "fields": [
      {
        "name": "count",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 3
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "opaque_id",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": "0",
        "multiplier": null,
        "offset": 5
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "count",
      "mission_type",
      "opaque_id"
    ]
  },
  "47": {
    "name": "MISSION_ACK",
    "crc": 153,
    "min": 3,
    "max": 8,
    "fields": [
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 1
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 3
      },
      {
        "name": "opaque_id",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": "0",
        "multiplier": null,
        "offset": 4
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "type",
      "mission_type",
      "opaque_id"
    ]
  },
  "51": {
    "name": "MISSION_REQUEST_INT",
    "crc": 196,
    "min": 4,
    "max": 5,
    "fields": [
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 3
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "seq",
      "mission_type"
    ]
  },
  "65": {
    "name": "RC_CHANNELS",
    "crc": 118,
    "min": 42,
    "max": 42,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "chan1_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "chan2_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 6
      },
      {
        "name": "chan3_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "chan4_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 10
      },
      {
        "name": "chan5_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "chan6_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 14
      },
      {
        "name": "chan7_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "chan8_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 18
      },
      {
        "name": "chan9_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "chan10_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 22
      },
      {
        "name": "chan11_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "chan12_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 26
      },
      {
        "name": "chan13_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 28
      },
      {
        "name": "chan14_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 30
      },
      {
        "name": "chan15_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 32
      },
      {
        "name": "chan16_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 34
      },
      {
        "name": "chan17_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 36
      },
      {
        "name": "chan18_raw",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "invalid": "UINT16_MAX",
        "multiplier": null,
        "offset": 38
      },
      {
        "name": "chancount",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 40
      },
      {
        "name": "rssi",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": "UINT8_MAX",
        "multiplier": null,
        "offset": 41
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "chancount",
      "chan1_raw",
      "chan2_raw",
      "chan3_raw",
      "chan4_raw",
      "chan5_raw",
      "chan6_raw",
      "chan7_raw",
      "chan8_raw",
      "chan9_raw",
      "chan10_raw",
      "chan11_raw",
      "chan12_raw",
      "chan13_raw",
      "chan14_raw",
      "chan15_raw",
      "chan16_raw",
      "chan17_raw",
      "chan18_raw",
      "rssi"
    ]
  },
  "73": {
    "name": "MISSION_ITEM_INT",
    "crc": 38,
    "min": 37,
    "max": 38,
    "fields": [
      {
        "name": "param1",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "param2",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "param3",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "param4",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "x",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "y",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "z",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 28
      },
      {
        "name": "command",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 30
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 32
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 33
      },
      {
        "name": "frame",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 34
      },
      {
        "name": "current",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 35
      },
      {
        "name": "autocontinue",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 36
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 37
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "seq",
      "frame",
      "command",
      "current",
      "autocontinue",
      "param1",
      "param2",
      "param3",
      "param4",
      "x",
      "y",
      "z",
      "mission_type"
    ]
  },
  "77": {
    "name": "COMMAND_ACK",
    "crc": 143,
    "min": 3,
    "max": 10,
    "fields": [
      {
        "name": "command",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "result",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 2
      },
      {
        "name": "progress",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": "%",
        "invalid": "UINT8_MAX",
        "multiplier": null,
        "offset": 3
      },
      {
        "name": "result_param2",
        "type": "int32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 9
      }
    ],
    "xmlOrder": [
      "command",
      "result",
      "progress",
      "result_param2",
      "target_system",
      "target_component"
    ]
  },
  "147": {
    "name": "BATTERY_STATUS",
    "crc": 154,
    "min": 36,
    "max": 54,
    "fields": [
      {
        "name": "current_consumed",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mAh",
        "invalid": "-1",
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "energy_consumed",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "hJ",
        "invalid": "-1",
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "temperature",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cdegC",
        "invalid": "INT16_MAX",
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "voltages",
        "type": "uint16_t",
        "array": 10,
        "extension": false,
        "unit": "mV",
        "invalid": "[UINT16_MAX]",
        "multiplier": null,
        "offset": 10
      },
      {
        "name": "current_battery",
        "type": "int16_t",
        "array": 0,
        "extension": false,
        "unit": "cA",
        "invalid": "-1",
        "multiplier": null,
        "offset": 30
      },
      {
        "name": "id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 32
      },
      {
        "name": "battery_function",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 33
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 34
      },
      {
        "name": "battery_remaining",
        "type": "int8_t",
        "array": 0,
        "extension": false,
        "unit": "%",
        "invalid": "-1",
        "multiplier": null,
        "offset": 35
      },
      {
        "name": "time_remaining",
        "type": "int32_t",
        "array": 0,
        "extension": true,
        "unit": "s",
        "invalid": "0",
        "multiplier": null,
        "offset": 36
      },
      {
        "name": "charge_state",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 40
      },
      {
        "name": "voltages_ext",
        "type": "uint16_t",
        "array": 4,
        "extension": true,
        "unit": "mV",
        "invalid": "[0]",
        "multiplier": null,
        "offset": 41
      },
      {
        "name": "mode",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 49
      },
      {
        "name": "fault_bitmask",
        "type": "uint32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 50
      }
    ],
    "xmlOrder": [
      "id",
      "battery_function",
      "type",
      "temperature",
      "voltages",
      "current_battery",
      "current_consumed",
      "energy_consumed",
      "battery_remaining",
      "time_remaining",
      "charge_state",
      "voltages_ext",
      "mode",
      "fault_bitmask"
    ]
  },
  "162": {
    "name": "FENCE_STATUS",
    "crc": 189,
    "min": 8,
    "max": 9,
    "fields": [
      {
        "name": "breach_time",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "breach_count",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "breach_status",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 6
      },
      {
        "name": "breach_type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 7
      },
      {
        "name": "breach_mitigation",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      }
    ],
    "xmlOrder": [
      "breach_status",
      "breach_count",
      "breach_type",
      "breach_time",
      "breach_mitigation"
    ]
  },
  "242": {
    "name": "HOME_POSITION",
    "crc": 104,
    "min": 52,
    "max": 60,
    "fields": [
      {
        "name": "latitude",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "longitude",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "altitude",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "x",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "y",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "z",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "q",
        "type": "float",
        "array": 4,
        "extension": false,
        "unit": null,
        "invalid": "[NaN]",
        "multiplier": null,
        "offset": 24
      },
      {
        "name": "approach_x",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 40
      },
      {
        "name": "approach_y",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 44
      },
      {
        "name": "approach_z",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "m",
        "invalid": null,
        "multiplier": null,
        "offset": 48
      },
      {
        "name": "time_usec",
        "type": "uint64_t",
        "array": 0,
        "extension": true,
        "unit": "us",
        "invalid": null,
        "multiplier": null,
        "offset": 52
      }
    ],
    "xmlOrder": [
      "latitude",
      "longitude",
      "altitude",
      "x",
      "y",
      "z",
      "q",
      "approach_x",
      "approach_y",
      "approach_z",
      "time_usec"
    ]
  },
  "245": {
    "name": "EXTENDED_SYS_STATE",
    "crc": 130,
    "min": 2,
    "max": 2,
    "fields": [
      {
        "name": "vtol_state",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "landed_state",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 1
      }
    ],
    "xmlOrder": [
      "vtol_state",
      "landed_state"
    ]
  },
  "193": {
    "name": "EKF_STATUS_REPORT",
    "crc": 71,
    "min": 22,
    "max": 26,
    "fields": [
      {
        "name": "velocity_variance",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 0
      },
      {
        "name": "pos_horiz_variance",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 4
      },
      {
        "name": "pos_vert_variance",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 8
      },
      {
        "name": "compass_variance",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 12
      },
      {
        "name": "terrain_alt_variance",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 16
      },
      {
        "name": "flags",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 20
      },
      {
        "name": "airspeed_variance",
        "type": "float",
        "array": 0,
        "extension": true,
        "unit": null,
        "invalid": null,
        "multiplier": null,
        "offset": 22
      }
    ],
    "xmlOrder": [
      "flags",
      "velocity_variance",
      "pos_horiz_variance",
      "pos_vert_variance",
      "compass_variance",
      "terrain_alt_variance",
      "airspeed_variance"
    ]
  }
};
