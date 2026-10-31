/** Static ownership map: legacy painters never write native payload controls/captions. */
const owned=new Set(['payload','shutter','camera-settings','camera-meta','zoom-in','zoom-out','zoom-value','shot-count','camera-label','camera-format','gimbal-value','gimbal-meta','capture-meta','payload-freshness','my-session','owners','authority']);
export function payloadPresentationOwned01(selector){const m=String(selector).match(/^#([a-z0-9-]+)/i);return !!m&&owned.has(m[1]);}
export const nativePayloadPresentation01=true;
