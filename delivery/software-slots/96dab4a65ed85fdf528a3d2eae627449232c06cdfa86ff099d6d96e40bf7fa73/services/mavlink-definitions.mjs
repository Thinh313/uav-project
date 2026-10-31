// Generated from reference/mavlink XML; regenerate with tools/generate_mavlink.py
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
        "offset": 0
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "autopilot",
        "type": "uint8_t",
        "array": 0,
        "offset": 5
      },
      {
        "name": "base_mode",
        "type": "uint8_t",
        "array": 0,
        "offset": 6
      },
      {
        "name": "system_status",
        "type": "uint8_t",
        "array": 0,
        "offset": 7
      },
      {
        "name": "mavlink_version",
        "type": "uint8_t",
        "array": 0,
        "offset": 8
      }
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
        "offset": 0
      },
      {
        "name": "lat",
        "type": "int32_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "lon",
        "type": "int32_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "alt",
        "type": "int32_t",
        "array": 0,
        "offset": 12
      },
      {
        "name": "relative_alt",
        "type": "int32_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "vx",
        "type": "int16_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "vy",
        "type": "int16_t",
        "array": 0,
        "offset": 22
      },
      {
        "name": "vz",
        "type": "int16_t",
        "array": 0,
        "offset": 24
      },
      {
        "name": "hdg",
        "type": "uint16_t",
        "array": 0,
        "offset": 26
      }
    ]
  },
  "148": {
    "name": "AUTOPILOT_VERSION",
    "crc": 178,
    "min": 60,
    "max": 78,
    "fields": [
      {
        "name": "capabilities",
        "type": "uint64_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "uid",
        "type": "uint64_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "flight_sw_version",
        "type": "uint32_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "middleware_sw_version",
        "type": "uint32_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "os_sw_version",
        "type": "uint32_t",
        "array": 0,
        "offset": 24
      },
      {
        "name": "board_version",
        "type": "uint32_t",
        "array": 0,
        "offset": 28
      },
      {
        "name": "vendor_id",
        "type": "uint16_t",
        "array": 0,
        "offset": 32
      },
      {
        "name": "product_id",
        "type": "uint16_t",
        "array": 0,
        "offset": 34
      },
      {
        "name": "flight_custom_version",
        "type": "uint8_t",
        "array": 8,
        "offset": 36
      },
      {
        "name": "middleware_custom_version",
        "type": "uint8_t",
        "array": 8,
        "offset": 44
      },
      {
        "name": "os_custom_version",
        "type": "uint8_t",
        "array": 8,
        "offset": 52
      },
      {
        "name": "uid2",
        "type": "uint8_t",
        "array": 18,
        "offset": 60
      }
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
        "offset": 0
      },
      {
        "name": "onboard_control_sensors_enabled",
        "type": "uint32_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "onboard_control_sensors_health",
        "type": "uint32_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "load",
        "type": "uint16_t",
        "array": 0,
        "offset": 12
      },
      {
        "name": "voltage_battery",
        "type": "uint16_t",
        "array": 0,
        "offset": 14
      },
      {
        "name": "current_battery",
        "type": "int16_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "drop_rate_comm",
        "type": "uint16_t",
        "array": 0,
        "offset": 18
      },
      {
        "name": "errors_comm",
        "type": "uint16_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "errors_count1",
        "type": "uint16_t",
        "array": 0,
        "offset": 22
      },
      {
        "name": "errors_count2",
        "type": "uint16_t",
        "array": 0,
        "offset": 24
      },
      {
        "name": "errors_count3",
        "type": "uint16_t",
        "array": 0,
        "offset": 26
      },
      {
        "name": "errors_count4",
        "type": "uint16_t",
        "array": 0,
        "offset": 28
      },
      {
        "name": "battery_remaining",
        "type": "int8_t",
        "array": 0,
        "offset": 30
      },
      {
        "name": "onboard_control_sensors_present_extended",
        "type": "uint32_t",
        "array": 0,
        "offset": 31
      },
      {
        "name": "onboard_control_sensors_enabled_extended",
        "type": "uint32_t",
        "array": 0,
        "offset": 35
      },
      {
        "name": "onboard_control_sensors_health_extended",
        "type": "uint32_t",
        "array": 0,
        "offset": 39
      }
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
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "param_id",
        "type": "char",
        "array": 16,
        "offset": 4
      }
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
        "offset": 0
      },
      {
        "name": "param_count",
        "type": "uint16_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "param_index",
        "type": "uint16_t",
        "array": 0,
        "offset": 6
      },
      {
        "name": "param_id",
        "type": "char",
        "array": 16,
        "offset": 8
      },
      {
        "name": "param_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 24
      }
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
        "offset": 0
      },
      {
        "name": "lat",
        "type": "int32_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "lon",
        "type": "int32_t",
        "array": 0,
        "offset": 12
      },
      {
        "name": "alt",
        "type": "int32_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "eph",
        "type": "uint16_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "epv",
        "type": "uint16_t",
        "array": 0,
        "offset": 22
      },
      {
        "name": "vel",
        "type": "uint16_t",
        "array": 0,
        "offset": 24
      },
      {
        "name": "cog",
        "type": "uint16_t",
        "array": 0,
        "offset": 26
      },
      {
        "name": "fix_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 28
      },
      {
        "name": "satellites_visible",
        "type": "uint8_t",
        "array": 0,
        "offset": 29
      },
      {
        "name": "alt_ellipsoid",
        "type": "int32_t",
        "array": 0,
        "offset": 30
      },
      {
        "name": "h_acc",
        "type": "uint32_t",
        "array": 0,
        "offset": 34
      },
      {
        "name": "v_acc",
        "type": "uint32_t",
        "array": 0,
        "offset": 38
      },
      {
        "name": "vel_acc",
        "type": "uint32_t",
        "array": 0,
        "offset": 42
      },
      {
        "name": "hdg_acc",
        "type": "uint32_t",
        "array": 0,
        "offset": 46
      },
      {
        "name": "yaw",
        "type": "uint16_t",
        "array": 0,
        "offset": 50
      }
    ]
  },
  "30": {
    "name": "ATTITUDE",
    "crc": 39,
    "min": 28,
    "max": 28,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "roll",
        "type": "float",
        "array": 0,
        "offset": 4
      },
      {
        "name": "pitch",
        "type": "float",
        "array": 0,
        "offset": 8
      },
      {
        "name": "yaw",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "rollspeed",
        "type": "float",
        "array": 0,
        "offset": 16
      },
      {
        "name": "pitchspeed",
        "type": "float",
        "array": 0,
        "offset": 20
      },
      {
        "name": "yawspeed",
        "type": "float",
        "array": 0,
        "offset": 24
      }
    ]
  },
  "40": {
    "name": "MISSION_REQUEST",
    "crc": 230,
    "min": 4,
    "max": 5,
    "fields": [
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 4
      }
    ]
  },
  "41": {
    "name": "MISSION_SET_CURRENT",
    "crc": 28,
    "min": 4,
    "max": 4,
    "fields": [
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      }
    ]
  },
  "42": {
    "name": "MISSION_CURRENT",
    "crc": 28,
    "min": 2,
    "max": 18,
    "fields": [
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "total",
        "type": "uint16_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "mission_state",
        "type": "uint8_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "mission_mode",
        "type": "uint8_t",
        "array": 0,
        "offset": 5
      },
      {
        "name": "mission_id",
        "type": "uint32_t",
        "array": 0,
        "offset": 6
      },
      {
        "name": "fence_id",
        "type": "uint32_t",
        "array": 0,
        "offset": 10
      },
      {
        "name": "rally_points_id",
        "type": "uint32_t",
        "array": 0,
        "offset": 14
      }
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
        "offset": 0
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 1
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      }
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
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "opaque_id",
        "type": "uint32_t",
        "array": 0,
        "offset": 5
      }
    ]
  },
  "45": {
    "name": "MISSION_CLEAR_ALL",
    "crc": 232,
    "min": 2,
    "max": 3,
    "fields": [
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 1
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      }
    ]
  },
  "46": {
    "name": "MISSION_ITEM_REACHED",
    "crc": 11,
    "min": 2,
    "max": 2,
    "fields": [
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "offset": 0
      }
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
        "offset": 0
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 1
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "opaque_id",
        "type": "uint32_t",
        "array": 0,
        "offset": 4
      }
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
        "offset": 0
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 4
      }
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
        "offset": 0
      },
      {
        "name": "param2",
        "type": "float",
        "array": 0,
        "offset": 4
      },
      {
        "name": "param3",
        "type": "float",
        "array": 0,
        "offset": 8
      },
      {
        "name": "param4",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "x",
        "type": "int32_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "y",
        "type": "int32_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "z",
        "type": "float",
        "array": 0,
        "offset": 24
      },
      {
        "name": "seq",
        "type": "uint16_t",
        "array": 0,
        "offset": 28
      },
      {
        "name": "command",
        "type": "uint16_t",
        "array": 0,
        "offset": 30
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 32
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 33
      },
      {
        "name": "frame",
        "type": "uint8_t",
        "array": 0,
        "offset": 34
      },
      {
        "name": "current",
        "type": "uint8_t",
        "array": 0,
        "offset": 35
      },
      {
        "name": "autocontinue",
        "type": "uint8_t",
        "array": 0,
        "offset": 36
      },
      {
        "name": "mission_type",
        "type": "uint8_t",
        "array": 0,
        "offset": 37
      }
    ]
  },
  "74": {
    "name": "VFR_HUD",
    "crc": 20,
    "min": 20,
    "max": 20,
    "fields": [
      {
        "name": "airspeed",
        "type": "float",
        "array": 0,
        "offset": 0
      },
      {
        "name": "groundspeed",
        "type": "float",
        "array": 0,
        "offset": 4
      },
      {
        "name": "alt",
        "type": "float",
        "array": 0,
        "offset": 8
      },
      {
        "name": "climb",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "heading",
        "type": "int16_t",
        "array": 0,
        "offset": 16
      },
      {
        "name": "throttle",
        "type": "uint16_t",
        "array": 0,
        "offset": 18
      }
    ]
  },
  "76": {
    "name": "COMMAND_LONG",
    "crc": 152,
    "min": 33,
    "max": 33,
    "fields": [
      {
        "name": "param1",
        "type": "float",
        "array": 0,
        "offset": 0
      },
      {
        "name": "param2",
        "type": "float",
        "array": 0,
        "offset": 4
      },
      {
        "name": "param3",
        "type": "float",
        "array": 0,
        "offset": 8
      },
      {
        "name": "param4",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "param5",
        "type": "float",
        "array": 0,
        "offset": 16
      },
      {
        "name": "param6",
        "type": "float",
        "array": 0,
        "offset": 20
      },
      {
        "name": "param7",
        "type": "float",
        "array": 0,
        "offset": 24
      },
      {
        "name": "command",
        "type": "uint16_t",
        "array": 0,
        "offset": 28
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 30
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 31
      },
      {
        "name": "confirmation",
        "type": "uint8_t",
        "array": 0,
        "offset": 32
      }
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
        "offset": 0
      },
      {
        "name": "result",
        "type": "uint8_t",
        "array": 0,
        "offset": 2
      },
      {
        "name": "progress",
        "type": "uint8_t",
        "array": 0,
        "offset": 3
      },
      {
        "name": "result_param2",
        "type": "int32_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "offset": 9
      }
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
        "offset": 0
      },
      {
        "name": "longitude",
        "type": "int32_t",
        "array": 0,
        "offset": 4
      },
      {
        "name": "altitude",
        "type": "int32_t",
        "array": 0,
        "offset": 8
      },
      {
        "name": "x",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "y",
        "type": "float",
        "array": 0,
        "offset": 16
      },
      {
        "name": "z",
        "type": "float",
        "array": 0,
        "offset": 20
      },
      {
        "name": "q",
        "type": "float",
        "array": 4,
        "offset": 24
      },
      {
        "name": "approach_x",
        "type": "float",
        "array": 0,
        "offset": 40
      },
      {
        "name": "approach_y",
        "type": "float",
        "array": 0,
        "offset": 44
      },
      {
        "name": "approach_z",
        "type": "float",
        "array": 0,
        "offset": 48
      },
      {
        "name": "time_usec",
        "type": "uint64_t",
        "array": 0,
        "offset": 52
      }
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
        "offset": 0
      },
      {
        "name": "landed_state",
        "type": "uint8_t",
        "array": 0,
        "offset": 1
      }
    ]
  },
  "253": {
    "name": "STATUSTEXT",
    "crc": 83,
    "min": 51,
    "max": 54,
    "fields": [
      {
        "name": "severity",
        "type": "uint8_t",
        "array": 0,
        "offset": 0
      },
      {
        "name": "text",
        "type": "char",
        "array": 50,
        "offset": 1
      },
      {
        "name": "id",
        "type": "uint16_t",
        "array": 0,
        "offset": 51
      },
      {
        "name": "chunk_seq",
        "type": "uint8_t",
        "array": 0,
        "offset": 53
      }
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
        "offset": 0
      },
      {
        "name": "pos_horiz_variance",
        "type": "float",
        "array": 0,
        "offset": 4
      },
      {
        "name": "pos_vert_variance",
        "type": "float",
        "array": 0,
        "offset": 8
      },
      {
        "name": "compass_variance",
        "type": "float",
        "array": 0,
        "offset": 12
      },
      {
        "name": "terrain_alt_variance",
        "type": "float",
        "array": 0,
        "offset": 16
      },
      {
        "name": "flags",
        "type": "uint16_t",
        "array": 0,
        "offset": 20
      },
      {
        "name": "airspeed_variance",
        "type": "float",
        "array": 0,
        "offset": 22
      }
    ]
  }
};
