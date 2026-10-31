// Exact missing generated dependencies only. Protected source is left untouched.
import {registerHooks} from 'node:module';import {fileURLToPath,pathToFileURL} from 'node:url';import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
export const aliases={
 'pilot/apstream40/definitions.mjs':'pilot/field02/flight/vendor/apstream40-definitions.mjs',
 'native/integration03/assets/mission-fixtures92.mjs':'native/crew02/assets/mission-fixtures92.mjs',
 ...Object.fromEntries(['auto','common','qgc','kml'].map(n=>['native/integration03/assets/offline94/'+n+'.mjs','native/crew02/assets/offline94/'+n+'.mjs']))
};
const urls=new Map(Object.entries(aliases).map(([a,b])=>[pathToFileURL(path.join(root,a)).href,pathToFileURL(path.join(root,b)).href]));
registerHooks({resolve(specifier,context,nextResolve){if(context.parentURL&&specifier.startsWith('.')){const target=urls.get(new URL(specifier,context.parentURL).href);if(target)return nextResolve(target,context);}return nextResolve(specifier,context);}});
