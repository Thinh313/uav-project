/** A known stopped runtime failure is closable evidence, never flight success. */
export function runtimeDisposition(c){if(!c||c.stopped!==true||c.ownedIdentityValidated!==true)throw Error('RUNTIME_STOPPED_OWNERSHIP_UNKNOWN');return{stopped:true,completeAllowed:c.error===null,runtimeError:c.error??null,authorityRestorable:false};}
