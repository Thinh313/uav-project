/** Explicit immutable reference assets. No network fetch or arbitrary file serving. */
import fs from 'node:fs';import path from 'node:path';import {createHash} from 'node:crypto';import {fileURLToPath} from 'node:url';
const REPO=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..');
const vendor='pilot/visual56/vendor/';
const names=['loaders/GLTFLoader.js','loaders/HDRLoader.js','objects/GroundedSkybox.js','postprocessing/EffectComposer.js','postprocessing/RenderPass.js','postprocessing/SSAOPass.js','postprocessing/OutputPass.js','postprocessing/Pass.js','postprocessing/ShaderPass.js','postprocessing/MaskPass.js','shaders/CopyShader.js','shaders/OutputShader.js','shaders/SSAOShader.js','utils/BufferGeometryUtils.js','utils/SkeletonUtils.js','math/SimplexNoise.js'];
export const ASSETS=Object.freeze({
 '/scene/display.mjs':'planning/betasim-integrated01/scene/display.mjs','/scene/observer.mjs':'planning/betasim-integrated01/scene/observer.mjs',
 '/scene/payload-surface.mjs':'planning/betasim-integrated01/scene/payload-surface.mjs',
 '/scene/publisher-scene.mjs':'planning/betasim-integrated01/scene/publisher-scene.mjs',
 '/scene/flight-scene.mjs':'pilot/visual56/scene.mjs','/scene/rotor-audio.mjs':'pilot/simhand01/audio.mjs',
 '/vendor/three.module.js':'pilot/sim32/viewer/vendor/three.module.js','/vendor/three.core.js':'pilot/sim32/viewer/vendor/three.core.js',
 ...Object.fromEntries(names.map(n=>['/vendor/addons/'+n,vendor+'addons/'+n])),
 ...Object.fromEntries(['cesium-drone.glb','outdoor.hdr','asphalt-color.jpg','asphalt-normal.jpg','asphalt-rough.jpg','outdoor-background.jpg'].map(n=>['/assets/'+n,'pilot/visual56/assets/'+n])),
 '/scene/font-medium.ttf':'native/betaintegrated01/cockpitio14/assets/fonts/Barlow-Medium.ttf',
 '/scene/font-semibold.ttf':'native/betaintegrated01/cockpitio14/assets/fonts/Barlow-SemiBold.ttf',
 '/scene/credits.html':'pilot/visual56/credits.html'
});
const types={'.mjs':'text/javascript','.js':'text/javascript','.jpg':'image/jpeg','.glb':'model/gltf-binary','.hdr':'application/octet-stream','.ttf':'font/ttf','.html':'text/html; charset=utf-8'};
export function assetManifest(){return Object.entries(ASSETS).map(([route,relativePath])=>{const p=path.join(REPO,relativePath),s=fs.lstatSync(p);if(!s.isFile()||s.isSymbolicLink()||s.size>32*2**20)throw Error('SCENE_REFERENCE_ASSET_SHAPE:'+relativePath);const b=fs.readFileSync(p);return{route,path:relativePath,bytes:b.length,sha256:createHash('sha256').update(b).digest('hex')};});}
export async function serveSceneAsset(route){const file=ASSETS[route];if(!file)return null;const p=path.join(REPO,file),s=await fs.promises.lstat(p);if(!s.isFile()||s.isSymbolicLink()||s.size>32*2**20)throw Error('SCENE_ASSET_BOUND');return{bytes:await fs.promises.readFile(p),type:types[path.extname(p)]};}
