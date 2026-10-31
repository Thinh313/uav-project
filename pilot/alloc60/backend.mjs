const BASE='http://127.0.0.1:8815';
export const ACTIONS=new Set(['start','refresh','verify-lease','claim','input','release','takeoff','land','end']);
export class FixedBackend{
 constructor(){this.token=null;this.mock=false}
 async get(route){if(!/^state$|^history(?:\/[a-zA-Z0-9]{1,24})?$/.test(route))throw Error('UPSTREAM_GET_ALLOWLIST');return this.request('/api/'+route)}
 async request(route,method='GET',body){let response;try{response=await fetch(BASE+route,{method,headers:{origin:BASE,...(method==='POST'?{'content-type':'application/json','x-sim-token':this.token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(method==='POST'?60000:4000)})}catch(e){throw Error((method==='POST'?'WRITE_OUTCOME_UNKNOWN_NO_RETRY:':'UPSTREAM_UNAVAILABLE:')+e.name)}const result=await response.json();if(!response.ok)throw Error(result.error??'UPSTREAM_'+response.status);return result}
 async post(route,body){if(!ACTIONS.has(route))throw Error('UPSTREAM_ACTION_ALLOWLIST');if(!this.token){const config=await this.request('/api/config');if(config.simulation!==true||typeof config.token!=='string')throw Error('SIMULATOR_CONFIG');this.token=config.token}return this.request('/api/'+route,'POST',body)}
}
