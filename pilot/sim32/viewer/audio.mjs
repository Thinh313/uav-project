// Engineering synthesis from estimated rotor RPM; no measured Hera/SPL claim.
export function rotorFrequency(rpm,blades=2){return Math.max(20,Math.min(1200,rpm*blades/60));}
export function attenuation(distance){return 1/(1+Math.max(0,distance)**2/100);}
export class RotorAudio{
 constructor(){this.context=null;this.nodes=[];this.enabled=false;}
 async enable(){if(!this.context){this.context=new AudioContext();this.master=this.context.createGain();this.master.gain.value=0;this.master.connect(this.context.destination);for(let i=0;i<4;i++)for(let h=1;h<=3;h++){const o=this.context.createOscillator(),g=this.context.createGain();o.type='sine';g.gain.value=.04/(h*h);o.connect(g).connect(this.master);o.start();this.nodes.push({o,rotor:i,h});}}await this.context.resume();this.enabled=true;}
 mute(){this.enabled=false;if(this.context)this.master.gain.setTargetAtTime(0,this.context.currentTime,.03);}
 update(rpm,distance,fresh){if(!this.context)return;const t=this.context.currentTime;if(!this.enabled||!fresh||document.hidden){this.master.gain.setTargetAtTime(0,t,.03);return;}for(const {o,rotor,h}of this.nodes)o.frequency.setTargetAtTime(rotorFrequency(rpm[rotor])*h,t,.02);const normalized=Math.max(...rpm)/6500;this.master.gain.setTargetAtTime(Math.min(.5,normalized*attenuation(distance)),t,.06);}
}
