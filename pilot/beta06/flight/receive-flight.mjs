/** Namespace-neutral receiver reuses frozen canonical implementation exactly. */
import{receiveFlight}from'../../field02/flight/receive-flight.mjs';import{fileURLToPath}from'node:url';export{receiveFlight};
if(process.argv[1]===fileURLToPath(import.meta.url)){try{console.log(JSON.stringify(await receiveFlight(JSON.parse(process.argv[2]))));}catch(e){console.error(JSON.stringify({status:'REJECTED',error:e.message}));process.exitCode=1;}}
