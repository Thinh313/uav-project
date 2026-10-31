import {EventEmitter} from 'node:events';import {randomUUID} from 'node:crypto';import {readFile} from 'node:fs/promises';import {compileSurvey,SITL_WORLD} from '../../app/core/compiler.mjs';import {fixtureProfileSnapshot} from './configuration.mjs';
const suite=JSON.parse(await readFile(new URL('../../app/fixtures/bench06/suite.json',import.meta.url)));
export class JournalFixture extends EventEmitter {
 constructor(){super();this.sessionId=randomUUID();this.vehicle={system:1,component:1};this.events=[];this.logicalMs=0;this.clock=()=>this.logicalMs;this.epoch=Date.now();this.samples={};this.mission={compiled:compileSurvey(suite.cases.find(c=>c.id==='narrow').request,SITL_WORLD),readback:null};this.hb();}
 profileSnapshot(){return fixtureProfileSnapshot(this);}snapshot(){return {firmware:'4.7.1',sessionId:this.sessionId};}observedHome(){return {lat:10.854,lon:106.807,amsl:10};}
 hb({mode=4,armed=false,landed=1}={}){this.samples[0]={at:this.logicalMs,fields:{base_mode:armed?128:0,custom_mode:mode}};this.samples[245]={at:this.logicalMs,fields:{landed_state:landed}};}
 event(type,detail={}){const e={type,time:new Date(this.epoch+this.logicalMs).toISOString(),sessionId:this.sessionId,detail};this.events.push(e);this.events=this.events.slice(-100);this.emit('event',e);}
 open(){this.event('mission-upload-request');this.mission.readback=structuredClone(this.mission.compiled.items);this.event('mission-readback',{matches:true});}
 observe(seconds=1){this.logicalMs+=seconds*1000;this.hb({armed:true,mode:3,landed:2});this.event('journal-observation',{source:'synthetic-replay',logicalMs:this.logicalMs});}
 terminal(){this.event('mission-item-reached',{seq:this.mission.compiled.items.length-1});this.hb({mode:6,armed:false,landed:1});this.event('mission-execution-ended',{state:'completed'});}
 disconnect(){this.event('before-disconnect',{reason:'operator'});}
}
