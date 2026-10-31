// Selected pinned official XML derivative. See generate.py and reference/protocol22.
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
        "offset": 0
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "autopilot",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 5
      },
      {
        "name": "base_mode",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 6
      },
      {
        "name": "system_status",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 7
      },
      {
        "name": "mavlink_version",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
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
        "extension": false,
        "unit": null,
        "offset": 0
      },
      {
        "name": "param2",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "param3",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 8
      },
      {
        "name": "param4",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 12
      },
      {
        "name": "param5",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 16
      },
      {
        "name": "param6",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 20
      },
      {
        "name": "param7",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 24
      },
      {
        "name": "command",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 28
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 30
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 31
      },
      {
        "name": "confirmation",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 32
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "command",
      "confirmation",
      "param1",
      "param2",
      "param3",
      "param4",
      "param5",
      "param6",
      "param7"
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
        "offset": 0
      },
      {
        "name": "result",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 2
      },
      {
        "name": "progress",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": "%",
        "offset": 3
      },
      {
        "name": "result_param2",
        "type": "int32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 4
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 8
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
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
  "259": {
    "name": "CAMERA_INFORMATION",
    "crc": 92,
    "min": 235,
    "max": 237,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "firmware_version",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "focal_length",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "offset": 8
      },
      {
        "name": "sensor_size_h",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "offset": 12
      },
      {
        "name": "sensor_size_v",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "offset": 16
      },
      {
        "name": "flags",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 20
      },
      {
        "name": "resolution_h",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 24
      },
      {
        "name": "resolution_v",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 26
      },
      {
        "name": "cam_definition_version",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 28
      },
      {
        "name": "vendor_name",
        "type": "uint8_t",
        "array": 32,
        "extension": false,
        "unit": null,
        "offset": 30
      },
      {
        "name": "model_name",
        "type": "uint8_t",
        "array": 32,
        "extension": false,
        "unit": null,
        "offset": 62
      },
      {
        "name": "lens_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 94
      },
      {
        "name": "cam_definition_uri",
        "type": "char",
        "array": 140,
        "extension": false,
        "unit": null,
        "offset": 95
      },
      {
        "name": "gimbal_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 235
      },
      {
        "name": "camera_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 236
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "vendor_name",
      "model_name",
      "firmware_version",
      "focal_length",
      "sensor_size_h",
      "sensor_size_v",
      "resolution_h",
      "resolution_v",
      "lens_id",
      "flags",
      "cam_definition_version",
      "cam_definition_uri",
      "gimbal_device_id",
      "camera_device_id"
    ]
  },
  "260": {
    "name": "CAMERA_SETTINGS",
    "crc": 146,
    "min": 5,
    "max": 14,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "mode_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "zoomLevel",
        "type": "float",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 5
      },
      {
        "name": "focusLevel",
        "type": "float",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 9
      },
      {
        "name": "camera_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 13
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "mode_id",
      "zoomLevel",
      "focusLevel",
      "camera_device_id"
    ]
  },
  "262": {
    "name": "CAMERA_CAPTURE_STATUS",
    "crc": 12,
    "min": 18,
    "max": 23,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "image_interval",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "s",
        "offset": 4
      },
      {
        "name": "recording_time_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 8
      },
      {
        "name": "available_capacity",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "MiB",
        "offset": 12
      },
      {
        "name": "image_status",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 16
      },
      {
        "name": "video_status",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 17
      },
      {
        "name": "image_count",
        "type": "int32_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 18
      },
      {
        "name": "camera_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 22
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "image_status",
      "video_status",
      "image_interval",
      "recording_time_ms",
      "available_capacity",
      "image_count",
      "camera_device_id"
    ]
  },
  "263": {
    "name": "CAMERA_IMAGE_CAPTURED",
    "crc": 133,
    "min": 255,
    "max": 255,
    "fields": [
      {
        "name": "time_utc",
        "type": "uint64_t",
        "array": 0,
        "extension": false,
        "unit": "us",
        "offset": 0
      },
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 8
      },
      {
        "name": "lat",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "offset": 12
      },
      {
        "name": "lon",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "degE7",
        "offset": 16
      },
      {
        "name": "alt",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "offset": 20
      },
      {
        "name": "relative_alt",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": "mm",
        "offset": 24
      },
      {
        "name": "q",
        "type": "float",
        "array": 4,
        "extension": false,
        "unit": null,
        "offset": 28
      },
      {
        "name": "image_index",
        "type": "int32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 44
      },
      {
        "name": "camera_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 48
      },
      {
        "name": "capture_result",
        "type": "int8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 49
      },
      {
        "name": "file_url",
        "type": "char",
        "array": 205,
        "extension": false,
        "unit": null,
        "offset": 50
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "time_utc",
      "camera_id",
      "lat",
      "lon",
      "alt",
      "relative_alt",
      "q",
      "image_index",
      "capture_result",
      "file_url"
    ]
  },
  "269": {
    "name": "VIDEO_STREAM_INFORMATION",
    "crc": 109,
    "min": 213,
    "max": 217,
    "fields": [
      {
        "name": "framerate",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "Hz",
        "offset": 0
      },
      {
        "name": "bitrate",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "bits/s",
        "offset": 4
      },
      {
        "name": "flags",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 8
      },
      {
        "name": "resolution_h",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 10
      },
      {
        "name": "resolution_v",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 12
      },
      {
        "name": "rotation",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "deg",
        "offset": 14
      },
      {
        "name": "hfov",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "deg",
        "offset": 16
      },
      {
        "name": "stream_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 18
      },
      {
        "name": "count",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 19
      },
      {
        "name": "type",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 20
      },
      {
        "name": "name",
        "type": "char",
        "array": 32,
        "extension": false,
        "unit": null,
        "offset": 21
      },
      {
        "name": "uri",
        "type": "char",
        "array": 160,
        "extension": false,
        "unit": null,
        "offset": 53
      },
      {
        "name": "encoding",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 213
      },
      {
        "name": "camera_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 214
      },
      {
        "name": "vfov",
        "type": "uint16_t",
        "array": 0,
        "extension": true,
        "unit": "cdeg",
        "offset": 215
      }
    ],
    "xmlOrder": [
      "stream_id",
      "count",
      "type",
      "flags",
      "framerate",
      "resolution_h",
      "resolution_v",
      "bitrate",
      "rotation",
      "hfov",
      "name",
      "uri",
      "encoding",
      "camera_device_id",
      "vfov"
    ]
  },
  "270": {
    "name": "VIDEO_STREAM_STATUS",
    "crc": 59,
    "min": 19,
    "max": 22,
    "fields": [
      {
        "name": "framerate",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "Hz",
        "offset": 0
      },
      {
        "name": "bitrate",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "bits/s",
        "offset": 4
      },
      {
        "name": "flags",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 8
      },
      {
        "name": "resolution_h",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 10
      },
      {
        "name": "resolution_v",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "pix",
        "offset": 12
      },
      {
        "name": "rotation",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "deg",
        "offset": 14
      },
      {
        "name": "hfov",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": "deg",
        "offset": 16
      },
      {
        "name": "stream_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 18
      },
      {
        "name": "camera_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 19
      },
      {
        "name": "vfov",
        "type": "uint16_t",
        "array": 0,
        "extension": true,
        "unit": "cdeg",
        "offset": 20
      }
    ],
    "xmlOrder": [
      "stream_id",
      "flags",
      "framerate",
      "resolution_h",
      "resolution_v",
      "bitrate",
      "rotation",
      "hfov",
      "camera_device_id",
      "vfov"
    ]
  },
  "280": {
    "name": "GIMBAL_MANAGER_INFORMATION",
    "crc": 70,
    "min": 33,
    "max": 33,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "cap_flags",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "roll_min",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 8
      },
      {
        "name": "roll_max",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 12
      },
      {
        "name": "pitch_min",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 16
      },
      {
        "name": "pitch_max",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 20
      },
      {
        "name": "yaw_min",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 24
      },
      {
        "name": "yaw_max",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 28
      },
      {
        "name": "gimbal_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 32
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "cap_flags",
      "gimbal_device_id",
      "roll_min",
      "roll_max",
      "pitch_min",
      "pitch_max",
      "yaw_min",
      "yaw_max"
    ]
  },
  "281": {
    "name": "GIMBAL_MANAGER_STATUS",
    "crc": 48,
    "min": 13,
    "max": 13,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "flags",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "gimbal_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 8
      },
      {
        "name": "primary_control_sysid",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 9
      },
      {
        "name": "primary_control_compid",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 10
      },
      {
        "name": "secondary_control_sysid",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 11
      },
      {
        "name": "secondary_control_compid",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 12
      }
    ],
    "xmlOrder": [
      "time_boot_ms",
      "flags",
      "gimbal_device_id",
      "primary_control_sysid",
      "primary_control_compid",
      "secondary_control_sysid",
      "secondary_control_compid"
    ]
  },
  "285": {
    "name": "GIMBAL_DEVICE_ATTITUDE_STATUS",
    "crc": 137,
    "min": 40,
    "max": 49,
    "fields": [
      {
        "name": "time_boot_ms",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": "ms",
        "offset": 0
      },
      {
        "name": "q",
        "type": "float",
        "array": 4,
        "extension": false,
        "unit": null,
        "offset": 4
      },
      {
        "name": "angular_velocity_x",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad/s",
        "offset": 20
      },
      {
        "name": "angular_velocity_y",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad/s",
        "offset": 24
      },
      {
        "name": "angular_velocity_z",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad/s",
        "offset": 28
      },
      {
        "name": "failure_flags",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 32
      },
      {
        "name": "flags",
        "type": "uint16_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 36
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 38
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 39
      },
      {
        "name": "delta_yaw",
        "type": "float",
        "array": 0,
        "extension": true,
        "unit": "rad",
        "offset": 40
      },
      {
        "name": "delta_yaw_velocity",
        "type": "float",
        "array": 0,
        "extension": true,
        "unit": "rad/s",
        "offset": 44
      },
      {
        "name": "gimbal_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": true,
        "unit": null,
        "offset": 48
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "time_boot_ms",
      "flags",
      "q",
      "angular_velocity_x",
      "angular_velocity_y",
      "angular_velocity_z",
      "failure_flags",
      "delta_yaw",
      "delta_yaw_velocity",
      "gimbal_device_id"
    ]
  },
  "287": {
    "name": "GIMBAL_MANAGER_SET_PITCHYAW",
    "crc": 1,
    "min": 23,
    "max": 23,
    "fields": [
      {
        "name": "flags",
        "type": "uint32_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 0
      },
      {
        "name": "pitch",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 4
      },
      {
        "name": "yaw",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad",
        "offset": 8
      },
      {
        "name": "pitch_rate",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad/s",
        "offset": 12
      },
      {
        "name": "yaw_rate",
        "type": "float",
        "array": 0,
        "extension": false,
        "unit": "rad/s",
        "offset": 16
      },
      {
        "name": "target_system",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 20
      },
      {
        "name": "target_component",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 21
      },
      {
        "name": "gimbal_device_id",
        "type": "uint8_t",
        "array": 0,
        "extension": false,
        "unit": null,
        "offset": 22
      }
    ],
    "xmlOrder": [
      "target_system",
      "target_component",
      "flags",
      "gimbal_device_id",
      "pitch",
      "yaw",
      "pitch_rate",
      "yaw_rate"
    ]
  }
};
