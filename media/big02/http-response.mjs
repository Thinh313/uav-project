/** JSON object encoding versus exact downloaded bytes. Content-Type does not alter byte payloads. */
export function responseBytes(value,type='application/json'){return value instanceof Uint8Array?Buffer.from(value):type==='application/json'?Buffer.from(JSON.stringify(value)):Buffer.from(value);}
