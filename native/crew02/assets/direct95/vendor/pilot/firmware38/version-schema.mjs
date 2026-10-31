export const VERSION_SCHEMA={
  "id": 148,
  "crc": 178,
  "min": 60,
  "max": 78,
  "fields": [
    {
      "name": "capabilities",
      "type": "uint64_t",
      "array": 0,
      "offset": 0,
      "extension": false
    },
    {
      "name": "flight_sw_version",
      "type": "uint32_t",
      "array": 0,
      "offset": 16,
      "extension": false
    },
    {
      "name": "middleware_sw_version",
      "type": "uint32_t",
      "array": 0,
      "offset": 20,
      "extension": false
    },
    {
      "name": "os_sw_version",
      "type": "uint32_t",
      "array": 0,
      "offset": 24,
      "extension": false
    },
    {
      "name": "board_version",
      "type": "uint32_t",
      "array": 0,
      "offset": 28,
      "extension": false
    },
    {
      "name": "flight_custom_version",
      "type": "uint8_t",
      "array": 8,
      "offset": 36,
      "extension": false
    },
    {
      "name": "middleware_custom_version",
      "type": "uint8_t",
      "array": 8,
      "offset": 44,
      "extension": false
    },
    {
      "name": "os_custom_version",
      "type": "uint8_t",
      "array": 8,
      "offset": 52,
      "extension": false
    },
    {
      "name": "vendor_id",
      "type": "uint16_t",
      "array": 0,
      "offset": 32,
      "extension": false
    },
    {
      "name": "product_id",
      "type": "uint16_t",
      "array": 0,
      "offset": 34,
      "extension": false
    },
    {
      "name": "uid",
      "type": "uint64_t",
      "array": 0,
      "offset": 8,
      "extension": false
    },
    {
      "name": "uid2",
      "type": "uint8_t",
      "array": 18,
      "offset": 60,
      "extension": true
    }
  ]
};
