"""Read retained RGBA PNG bytes, no rendering/dependency install or Android claims."""
from pathlib import Path
import struct,zlib,json,hashlib
E=Path('evidence/field02/repair01');b=(E/'contrast-raster-mock02.png').read_bytes();offset=8;data=b'';profile=False
while offset<len(b):
 n=struct.unpack('>I',b[offset:offset+4])[0];kind=b[offset+4:offset+8];chunk=b[offset+8:offset+8+n];offset+=n+12
 if kind==b'IHDR':width,height,depth,color,*_=struct.unpack('>IIBBBBB',chunk);assert depth==8 and color==6
 if kind==b'IDAT':data+=chunk
 if kind==b'iCCP':profile=True
raw=zlib.decompress(data);stride=width*4;pixels=[];previous=bytearray(stride);off=0
for y in range(height):
 mode=raw[off];off+=1;row=bytearray(raw[off:off+stride]);off+=stride
 for x in range(stride):
  a=row[x-4]if x>=4 else 0;c=previous[x-4]if x>=4 else 0;v=previous[x]
  if mode==1:row[x]=(row[x]+a)&255
  elif mode==2:row[x]=(row[x]+v)&255
  elif mode==3:row[x]=(row[x]+((a+v)//2))&255
  elif mode==4:
   p=a+v-c;pa,pb,pc=abs(p-a),abs(p-v),abs(p-c);row[x]=(row[x]+(a if pa<=pb and pa<=pc else v if pb<=pc else c))&255
  else:assert mode==0
 pixels.append(row);previous=row
def pixel(x,y):return list(pixels[y][x*4:x*4+3])
def lum(c):
 s=[v/255 for v in c];l=[v/12.92 if v<=.04045 else((v+.055)/1.055)**2.4 for v in s];return sum(a*v for a,v in zip([.2126,.7152,.0722],l))
def ratio(a,b):return(max(lum(a),lum(b))+.05)/(min(lum(a),lum(b))+.05)
config=json.loads((E/'contrast-mock-input02.json').read_text());results=[]
for i,item in enumerate(config):
 # NSImage draw origin bottom-left, PNG rows top-left.
 y0=height-1-(i*84+20);bg=pixel(5,y0);best=(0,None)
 for y in range(height-(i*84+62),height-(i*84+26)):
  for x in range(18,850):
   v=pixel(x,y);r=ratio(v,bg)
   if r>best[0]:best=(r,v)
 results.append({'label':item['label'],'backgroundPixelRGB':bg,'strongestGlyphPixelRGB':best[1],'rasterContrastApprox':best[0],'pass':best[0]>=4.5})
report={'status':'PASS_RETAINED_RASTER_MOCK_CONTRAST'if all(r['pass']for r in results)else'FAIL_RASTER_MOCK','scope':'READONLY_RETAINED_APPKIT_PNG_SAMPLE_RGB_APPROX_NOT_BROWSER_ANDROID_OR_ICC_DISPLAY_CERTIFICATION','sha256':hashlib.sha256(b).hexdigest(),'iccProfilePresent':profile,'results':results,'passed':sum(r['pass']for r in results),'minimum':min(r['rasterContrastApprox']for r in results),'priorCriterionDisposition':'Closest exact RGB of calibrated AppKit glyph differs after ColorSync; report02 exact-match flags are harness mismatch, not a product PASS. This analysis measures actual stored glyph/background pixels and preserves that report.'}
(E/'contrast-png-analysis01.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'passed':report['passed'],'minimum':report['minimum']}))
