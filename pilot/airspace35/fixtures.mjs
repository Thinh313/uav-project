import {seal} from './core/airspace.mjs';
export const ORIGIN=[106.807,10.854],DATE='2026-10-14T02:00:00.000Z';
export const iso=t=>new Date(t).toISOString();
export function xy(x,y,origin=ORIGIN){const rad=Math.PI/180,R=6371008.8;return[origin[0]+x/(R*Math.cos(origin[1]*rad)*rad),origin[1]+y/(R*rad)]}
export const rect=(x0,y0,x1,y1)=>({type:'Polygon',coordinates:[[[x0,y0],[x1,y0],[x1,y1],[x0,y1],[x0,y0]].map(p=>xy(...p))]});
export async function dataset(now=DATE,zones=[]){const t=Date.parse(now);return seal({format:'aeris-airspace35',version:1,source:{id:'SYNTHETIC_LOCAL_35',revision:'fixture-1',origin:'SYNTHETIC',capturedAt:now,validity:{start:iso(t-1000),end:iso(t+86400000)}},coverage:rect(-900,-900,900,900),zones})}
export function zone(kind='PROHIBITED',geometry=rect(-10,-10,10,10),frame='REL_HOME',now=DATE){return{id:'zone35',kind,geometry,altitude:{frame,datumId:frame==='AMSL'?'SYNTHETIC_MSL35':frame==='REL_HOME'?'SYNTHETIC_HOME35':'TERRAIN_UNAVAILABLE',minM:0,maxM:120},validity:{start:now,end:iso(Date.parse(now)+3600000)}}}
export function route(now=DATE){const t=Date.parse(now)+1000,points=[[-200,0],[-100,0],[100,0],[200,0],[200,0]],layers=['departure','survey','return','landing'];return{format:'aeris-route35',version:1,origin:ORIGIN,missionSha256:'a'.repeat(64),segments:layers.map((layer,i)=>({layer,from:xy(...points[i]),to:xy(...points[i+1]),start:iso(t+i*10000),end:iso(t+(i+1)*10000),altitude:{frame:'REL_HOME',datumId:'SYNTHETIC_HOME35',fromM:50,toM:50},horizontalUncertaintyM:0,verticalUncertaintyM:0,timeUncertaintyMs:0}))}}
export const context=(now=DATE)=>({now,home:{id:'mock-home35',origin:'SYNTHETIC',observedAt:now,amslM:10,uncertaintyM:1,datumId:'SYNTHETIC_MSL35',relativeFrameId:'SYNTHETIC_HOME35'},permissions:[]});
