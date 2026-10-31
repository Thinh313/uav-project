import {PAYLOADS} from './fixtures.mjs';
export class SimulatorAdapter {
  kind='simulation'; pending=[]; fault='none';
  send(c,deliver) {this.pending.push({c:structuredClone(c),deliver});}
  step() {
    for(const item of this.pending.splice(0)) {
      const {c,deliver}=item,base={commandId:c.id,sessionId:c.sessionId,discoveryId:c.discoveryId,payloadId:c.payloadId,route:c.route,operation:c.operation};
      if(this.fault==='silent')continue;
      deliver({...base,type:'ack',result:this.fault==='denied'?'denied':'accepted'});
      if(this.fault==='none')deliver({...base,type:'observation',origin:'SIMULATION',values:c.args});
    }
  }
}
export function discoverFixtures(session) {for(const p of PAYLOADS)session.discover(p);}
