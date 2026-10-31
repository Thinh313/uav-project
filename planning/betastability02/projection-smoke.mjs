import{fileURLToPath}from'node:url';import{createBetaMedia}from'../../pilot/betastability02/media-projection.mjs';import fs from'node:fs';
const m=await createBetaMedia({out:fileURLToPath(new URL('../../evidence/betastability02/projection-smoke01',import.meta.url)),port:0,schedule:false});try{console.log(await m.listen());console.log(m.state());console.log(m.projection);}finally{await m.close();}
