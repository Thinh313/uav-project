// Only immutable, hash-pinned geographic data is installed. Never store API responses/tokens.
import {verifyGeoBundle,GEO_PINS} from './geodata.mjs';
const key='aeris-offline-geo-v1';
export async function installOffline(storage,bundle){const geo=await verifyGeoBundle(bundle);storage.setItem(key,JSON.stringify(bundle));return geo;}
export async function restoreOffline(storage){const raw=storage.getItem(key);if(!raw)return null;if(raw.length>600000)throw Error('Gói offline vượt giới hạn.');return verifyGeoBundle(JSON.parse(raw));}
export function offlineStatus(storage){return {installed:!!storage.getItem(key),geoId:GEO_PINS.id};}
