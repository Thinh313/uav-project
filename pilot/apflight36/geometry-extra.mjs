import{linearRange,intersection,merge}from'./vendor/geometry.mjs';
const sub=(a,b)=>[a[0]-b[0],a[1]-b[1]],dot=(a,b)=>a[0]*b[0]+a[1]*b[1],cross=(a,b)=>a[0]*b[1]-a[1]*b[0],E=1e-9;
function disk(a,b,c,r){const v=sub(b,a),w=sub(a,c),A=dot(v,v),B=2*dot(w,v),C=dot(w,w)-r*r;if(A<E)return C<=0?[[0,1]]:[];const D=B*B-4*A*C;if(D<0)return[];const q=Math.sqrt(D);return merge([[(-B-q)/(2*A),(-B+q)/(2*A)]])}
function edgeCapsule(a,b,c,d,r){const v=sub(d,c),n=Math.hypot(...v),w0=sub(a,c),w1=sub(b,c);return merge([...disk(a,b,c,r),...disk(a,b,d,r),...intersection(linearRange(dot(w0,v)/n,dot(w1,v)/n,0,n),linearRange(cross(v,w0)/n,cross(v,w1)/n,-r,r))])}
/** Exact interval subtraction for erosion confidence, no uniform path sampling. */
export function erodedInteriorExists(a,b,rings,radius,base){
 const near=merge(rings.flatMap(r=>r.slice(0,-1).flatMap((p,i)=>edgeCapsule(a,b,p,r[i+1],radius))));
 for(const[lo,hi]of base){let at=lo;for(const[x,y]of near){if(y<at)continue;if(x>hi)break;if(x-at>E)return true;at=Math.max(at,y);if(at>=hi)break;}if(hi-at>E)return true;}return false;
}
