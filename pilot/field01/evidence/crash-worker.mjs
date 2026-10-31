import { Store01 } from './store01.mjs';
import { fixture } from './fixtures.mjs';
const [root,stage]=process.argv.slice(2);
const store=await Store01({root,hooks:{at:async point=>{if(point===stage)process.exit(71);}}});
await store.commit('crash-capture',fixture('crash-capture'));
await store.close();
process.exitCode=72;
