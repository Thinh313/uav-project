import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {receiveReport} from './core.mjs';
if(process.argv[1]===fileURLToPath(import.meta.url)){
 try{if(process.argv.length!==4)throw Error('Usage: node pilot/coach01/receiver.mjs report.json source-package.json');console.log(JSON.stringify(await receiveReport(fs.readFileSync(process.argv[2]),fs.readFileSync(process.argv[3])),null,2));}
 catch(e){console.error(JSON.stringify({status:'REJECTED',error:e.message,authorityRestorable:false}));process.exitCode=1;}
}
