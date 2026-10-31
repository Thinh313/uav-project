// Procedural engineering sound, not measured Hera acoustics or SPL.
export function targets(rpm,distance){return {frequencies:rpm.map(x=>Math.max(20,Math.min(1200,x*2/60))),gain:Math.min(.18,Math.max(...rpm,0)/6500*.18)/(1+Math.max(0,distance)**2/100)}}
export class EngineSound{
 constructor(){this.enabled=false;this.context=null;this.motors=[]}
 async enable(){if(!this.context){const c=this.context=new AudioContext();this.master=c.createGain();this.master.gain.value=0;this.master.connect(c.destination);
  for(let m=0;m<4;m++)for(let harmonic=1;harmonic<=4;harmonic++){const o=c.createOscillator(),g=c.createGain();o.type=harmonic===1?'triangle':'sine';g.gain.value=.15/(harmonic*harmonic);o.connect(g).connect(this.master);o.start();this.motors.push({o,m,harmonic})}
  const b=c.createBuffer(1,c.sampleRate,c.sampleRate),data=b.getChannelData(0);let seed=78;for(let i=0;i<data.length;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;data[i]=(seed/2**32*2-1)*.18}const n=c.createBufferSource();n.buffer=b;n.loop=true;this.filter=c.createBiquadFilter();this.filter.type='bandpass';this.filter.Q.value=.7;n.connect(this.filter).connect(this.master);n.start();
 }await this.context.resume();this.enabled=true}
 update(rpm,distance,active){if(!this.context)return;const t=this.context.currentTime;if(!this.enabled||!active||document.hidden){this.master.gain.setTargetAtTime(0,t,.025);return}const v=targets(rpm,distance);for(const {o,m,harmonic}of this.motors)o.frequency.setTargetAtTime(v.frequencies[m]*harmonic,t,.025);this.filter.frequency.setTargetAtTime(700+Math.max(...rpm)/8,t,.05);this.master.gain.setTargetAtTime(v.gain,t,.05)}
 mute(){this.enabled=false;this.silence()}
 silence(){if(this.context)this.master.gain.setTargetAtTime(0,this.context.currentTime,.025)}
}
