/** Bounded, non-resolving XML/KML reader for offline planning. No URL/file/entity IO. */
import {sha} from './common.mjs';
const NS='http://www.opengis.net/kml/2.2',fail=x=>{throw Error(x)},bytes=s=>new TextEncoder().encode(s).length;
function chars(s){for(const c of s){const n=c.codePointAt(0);if(!(n===9||n===10||n===13||n>=32&&n<=0xD7FF||n>=0xE000&&n<=0xFFFD||n>=0x10000&&n<=0x10FFFF))fail('KML_XML_CHARACTER');}return s;}
function entities(s){if(/&(?!amp;|lt;|gt;|quot;|apos;|#\d+;|#x[0-9a-fA-F]+;)/.test(s))fail('KML_XML_ENTITY');return s.replace(/&([^;]+);/g,(_,v)=>{const t={amp:'&',lt:'<',gt:'>',quot:'"',apos:"'"};if(v in t)return t[v];const n=v.startsWith('#x')?parseInt(v.slice(2),16):Number(v.slice(1));if(!Number.isInteger(n)||n>0x10FFFF)fail('KML_XML_ENTITY');return chars(String.fromCodePoint(n));});}
function xml(raw){
 if(typeof raw!=='string'||bytes(raw)>262144)fail('KML_SIZE');
 if(/<!\s*(DOCTYPE|ENTITY)/i.test(raw)||raw.includes('<?xml-stylesheet'))fail('KML_EXTERNAL_DECLARATION');
 const decl=raw.match(/^\uFEFF?\s*<\?xml[^?]*encoding=["']([^"']+)/i);if(decl&&!['utf-8','utf8'].includes(decl[1].toLowerCase()))fail('KML_ENCODING_UTF8_REQUIRED');
 let s=chars(raw.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n')),at=0,root=null,count=0;const stack=[];
 const name=/^[A-Za-z_][A-Za-z0-9_.-]*(?::[A-Za-z_][A-Za-z0-9_.-]*)?$/;
 const text=(v,cdata=false)=>{if(!cdata&&v.includes(']]>'))fail('KML_XML_TEXT');v=cdata?v:entities(v);if(!stack.length){if(v.trim())fail('KML_XML_OUTSIDE_ROOT');}else stack.at(-1).parts.push(v);};
 while(at<s.length){
  if(s[at]!=='<'){const end=s.indexOf('<',at);text(s.slice(at,end<0?s.length:end));at=end<0?s.length:end;continue;}
  if(s.startsWith('<!--',at)){const end=s.indexOf('-->',at+4);if(end<0||s.slice(at+4,end).includes('--')||s[end-1]==='-')fail('KML_XML_COMMENT');at=end+3;continue;}
  if(s.startsWith('<![CDATA[',at)){const end=s.indexOf(']]>',at+9);if(end<0||!stack.length)fail('KML_XML_CDATA');text(s.slice(at+9,end),true);at=end+3;continue;}
  if(s.startsWith('<?',at)){const end=s.indexOf('?>',at+2);const pi=end<0?'':s.slice(at,end+2);if(at!==0||!/^<\?xml\s+version\s*=\s*(['"])1\.0\1(?:\s+encoding\s*=\s*(['"])[^'"]+\2)?(?:\s+standalone\s*=\s*(['"])(?:yes|no)\3)?\s*\?>$/.test(pi))fail('KML_XML_DECLARATION');at=end+2;continue;}
  if(s.startsWith('</',at)){const end=s.indexOf('>',at+2),close=s.slice(at+2,end).trim();if(end<0||!name.test(close)||stack.pop()?.qname!==close)fail('KML_XML_CLOSE');at=end+1;continue;}
  let end=at+1,quote=null;for(;end<s.length;end++){const c=s[end];if(quote){if(c===quote)quote=null;}else if(c==='"'||c==="'")quote=c;else if(c==='>')break;}if(end===s.length)fail('KML_XML_TAG');
  let tag=s.slice(at+1,end),empty=tag.endsWith('/');if(empty)tag=tag.slice(0,-1);const m=tag.match(/^([^\s]+)([\s\S]*)$/);if(!m||!name.test(m[1]))fail('KML_XML_NAME');const qname=m[1],attrs=Object.create(null),seen=new Set(),namespaces=Object.assign(Object.create(null),stack.at(-1)?.namespaces??{});let rest=m[2];
  while(rest.trim()){const a=rest.match(/^\s+([^\s=]+)\s*=\s*(["'])([^]*?)\2/);if(!a||!name.test(a[1])||seen.has(a[1])||a[3].includes('<'))fail('KML_XML_ATTRIBUTE');seen.add(a[1]);const k=a[1],v=entities(a[3].replace(/[\n\t]/g,' '));rest=rest.slice(a[0].length);if(k==='xmlns')namespaces['']=v;else if(k.startsWith('xmlns:')){if(['xml','xmlns'].includes(k.slice(6)))fail('KML_XML_NAMESPACE_DECLARATION');namespaces[k.slice(6)]=v;}else attrs[k]=v;}
  const parts=qname.split(':'),prefix=parts.length===2?parts[0]:'',tagName=parts.at(-1);if(namespaces[prefix]!==NS)fail(root?'KML_FOREIGN_NAMESPACE':'KML_NAMESPACE');
  const node={tag:tagName,qname,attrs,namespaces,children:[],parts:[]};if(++count>4096||stack.length>16)fail('KML_XML_BOUND');if(stack.length){stack.at(-1).children.push(node);stack.at(-1).parts.push(node);}else{if(root)fail('KML_XML_MULTIPLE_ROOTS');root=node;}if(!empty)stack.push(node);at=end+1;
 }
 if(stack.length||!root)fail('KML_XML_UNCLOSED');if(root.tag!=='kml')fail('KML_NAMESPACE');
 const inspect=n=>{if(['coordinates','altitudeMode','extrude','tessellate','visibility'].includes(n.tag)&&(n.children.length||Object.keys(n.attrs).length))fail('KML_SCALAR_CONTENT');n.children.forEach(inspect);};inspect(root);return root;
}
const full=n=>n?n.parts.map(p=>typeof p==='string'?p:full(p)).join(''):'';const txt=n=>full(n).trim();
function one(n,t,required=false){const a=n.children.filter(c=>c.tag===t);if(a.length>1||required&&!a.length)fail('KML_SINGLE_'+t);return a[0];}
function children(n,allowed){if(Object.keys(n.attrs).some(k=>k!=='id'))fail('KML_ATTRIBUTE');for(const c of n.children)if(!allowed.includes(c.tag))fail('KML_UNSUPPORTED_'+c.tag);}
export function parseKml94(text){
 const root=xml(text),features=[],ignored=new Set(),ids=new Set();let coordsCount=0;
 function ring(e,closed=false){children(e,['coordinates','tessellate','altitudeMode','extrude']);if(closed&&one(e,'altitudeMode'))fail('KML_NESTED_RING_ALTITUDE_UNSUPPORTED');one(e,'tessellate');one(e,'extrude');for(const c of e.children)if(['tessellate','extrude'].includes(c.tag)&&!['0','1'].includes(txt(c)))fail('KML_BOOLEAN');if(txt(one(e,'extrude'))==='1')fail('KML_EXTRUSION_UNSUPPORTED');
  const raw=txt(one(e,'coordinates',true)),points=[];for(const token of raw?raw.split(/\s+/):[]){const a=token.split(',');if(![2,3].includes(a.length)||a.some(v=>! /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(v)))fail('KML_COORDINATE');const p=a.map(Number),z=p.length===3?p[2]:null;if(!p.every(Number.isFinite)||Math.abs(p[0])>180||Math.abs(p[1])>70||z!==null&&Math.abs(z)>20000)fail('KML_COORDINATE_RANGE');points.push([p[0],p[1],z]);if(++coordsCount>1024)fail('KML_TOTAL_COORDINATES');}
  if(points.length<(closed?4:2)||points.length>(closed?65:32))fail('KML_VERTEX_COUNT');if(closed&&JSON.stringify(points[0])!==JSON.stringify(points.at(-1)))fail('KML_RING_NOT_CLOSED');return points;
 }
 function geometry(e,name,visible,pmid){const t=e.tag;if(t==='MultiGeometry'){children(e,['Polygon','LineString','MultiGeometry']);if(!e.children.length)fail('KML_EMPTY_MULTIGEOMETRY');for(const c of e.children)geometry(c,name,visible,pmid);return;}if(!['Polygon','LineString'].includes(t))fail('KML_UNSUPPORTED_'+t);if(features.length>=16)fail('KML_FEATURE_BOUND');const mode=txt(one(e,'altitudeMode'))||'clampToGround';if(!['clampToGround','relativeToGround','absolute'].includes(mode))fail('KML_ALTITUDE_MODE');const holes=[];for(const k of ['tessellate','extrude'])if(!['','0','1'].includes(txt(one(e,k))))fail('KML_BOOLEAN');let points;
  if(t==='Polygon'){children(e,['outerBoundaryIs','innerBoundaryIs','altitudeMode','tessellate','extrude']);if(!['','0'].includes(txt(one(e,'extrude'))))fail('KML_EXTRUSION_UNSUPPORTED');const outer=one(e,'outerBoundaryIs',true);children(outer,['LinearRing']);points=ring(one(outer,'LinearRing',true),true);for(const h of e.children.filter(c=>c.tag==='innerBoundaryIs')){if(holes.length>=8)fail('KML_HOLE_BOUND');children(h,['LinearRing']);holes.push(ring(one(h,'LinearRing',true),true));}}else points=ring(e);
  features.push({id:'f-'+String(features.length+1).padStart(4,'0'),name,placemarkId:pmid,kind:t,visible,altitudeMode:mode,altitudeModeDeclared:!!one(e,'altitudeMode'),coordinates:points,holes,inspectionOnly:!!holes.length||mode!=='clampToGround'||!visible});
 }
 const metadata=['name','description','Style','StyleMap','styleUrl','open'];
 function walk(e,visible=true){children(e,[...metadata,'Document','Folder','Placemark','visibility']);const vis=txt(one(e,'visibility'));if(!['','0','1'].includes(vis))fail('KML_VISIBILITY');visible=visible&&vis!=='0';for(const c of e.children){const t=c.tag;if(metadata.includes(t)){ignored.add(t);continue;}if(t==='visibility')continue;if(t!=='Placemark'){walk(c,visible);continue;}children(c,[...metadata,'visibility','Polygon','LineString','MultiGeometry']);const pmid=c.attrs.id??null,name=txt(one(c,'name'))||'Đối tượng chưa đặt tên';if([...name].length>200||pmid!==null&&([...pmid].length>200||ids.has(pmid)))fail('KML_NAME_OR_ID');if(pmid)ids.add(pmid);const cv=txt(one(c,'visibility'));if(!['','0','1'].includes(cv))fail('KML_VISIBILITY');const geoms=c.children.filter(x=>['Polygon','LineString','MultiGeometry'].includes(x.tag));if(geoms.length!==1)fail('KML_PLACEMARK_GEOMETRY');for(const x of c.children)if(metadata.includes(x.tag)&&x.tag!=='name')ignored.add(x.tag);geometry(geoms[0],name,visible&&cv!=='0',pmid);}}
 walk(root);if(!features.length)fail('KML_NO_FEATURE');return{format:'aeris-kml-aoi51',version:1,coordinateSystem:'WGS84',sourceSha256:sha(text),sourceBytes:bytes(text),features,ignoredPresentation:[...ignored].sort(),operational:false};
}
