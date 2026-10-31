import{groundRecoveryCheck}from'./flight/ground-recovery.mjs';
/** Validate exact owned request before touching payload rights, persist before any AP fault effect. */
export async function invalidateBeforeFlightEffect({flight,payload,client,q}){
 if(!['cut','reboot','abort','close','recover-ground'].includes(q.action))throw Error('FAULT_INVALIDATION_ACTION');
 client.assert(q);if(flight.busy)throw Error('ACTION_IN_PROGRESS');
 if(q.action!=='close'&&q.confirmSimulation!==true)throw Error('EXPLICIT_SIMULATION_FAULT_OR_ABORT');
 flight.scope(q,{connected:true});
 if(q.action==='close'&&!flight.current.link.completion().complete)throw Error('OBSERVED_AUTO_NAV_RTL_GROUND_DISARM_REQUIRED');
 if(q.action==='recover-ground')groundRecoveryCheck(flight.current.link,q);
 const invalidated=payload.invalidate('FLIGHT_'+q.action.toUpperCase(),{force:true,request:q});
 await payload.settled();client.assert(q);return invalidated;
}
