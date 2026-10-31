class Probe extends AudioWorkletProcessor{
 constructor(){super();this.remaining=0;this.port.onmessage=e=>{if(e.data?.capture===true){this.remaining=Math.floor(sampleRate*2);this.port.postMessage({sampleRate,started:true});}};}
 process(inputs){if(this.remaining>0){const v=inputs[0]?.[0];if(v){const n=Math.min(v.length,this.remaining),copy=v.slice(0,n);this.remaining-=n;this.port.postMessage({samples:copy.buffer,done:this.remaining===0},[copy.buffer]);}}return true;}
}
registerProcessor('aeris-own-graph-pcm-probe',Probe);
