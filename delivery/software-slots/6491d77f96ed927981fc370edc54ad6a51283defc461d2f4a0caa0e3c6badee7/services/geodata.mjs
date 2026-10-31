import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {GEO_PINS,validateGrid} from '../app/core/geodata.mjs';
const hash=x=>createHash('sha256').update(x).digest('hex');
export function loadServerGeo(){const root=new URL('../app/data/',import.meta.url),manifestText=readFileSync(new URL('manifest.json',root));if(hash(manifestText)!==GEO_PINS.manifestSha256)throw Error('Geodata manifest drift');const manifest=JSON.parse(manifestText),assets={};for(const [name,pin]of Object.entries(GEO_PINS.assets)){const raw=readFileSync(new URL(name,root));if(raw.length!==pin.bytes||hash(raw)!==pin.sha256)throw Error(`Geodata drift: ${name}`);assets[name]=JSON.parse(raw);}validateGrid(assets['dsm.json']);return {manifest,grid:assets['dsm.json'],basemap:assets['basemap.json'],verified:true};}
