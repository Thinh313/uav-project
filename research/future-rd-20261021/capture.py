"""Bounded public documentation snapshots; no runtime/device or SDK operations."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,shutil,urllib.request,urllib.error
R=Path(__file__).resolve().parent
SOURCES=[
 ('sony-sdk','sony','https://support.d-imaging.sony.co.jp/app/sdk/en/index.html'),
 ('sony-ptp','sony','https://support.d-imaging.sony.co.jp/app/cameraremotecommand/en/index.html?id=portal'),
 ('sony-lr1','sony','https://pro.sony/en_GB/products/installable-cameras/ilx-lr1'),
 ('gremsy-pixylr','gremsy','https://gremsy.com/products/pixy-lr'),
 ('gremsy-vio','gremsy','https://gremsy.com/products/vio'),
 ('gremsy-integration','gremsy','https://docs.gremsy.com/gimbals/pixy-lr/airpixel-entire-set-installation-for-cube-pilot-pixhawk'),
 ('phaseone-p3','phaseone','https://www.phaseone.com/solutions/geospatial-solutions/uav-cameras/p3/'),
 ('phaseone-gs120','phaseone','https://www.phaseone.com/solutions/geospatial-solutions/components/ixm-gs120/'),
 ('phaseone-sdk','phaseone','https://developer.phaseone.com/sdk/index.html'),
 ('flir-hadron','flir','https://www.oem.flir.com/products/hadron-640/'),
 ('nvidia-orin','nvidia','https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/'),
 ('nvidia-thor','nvidia','https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-thor/'),
 ('qualcomm-iq9075','qualcomm','https://www.qualcomm.com/internet-of-things/products/iq9-series/iq-9075'),
 ('ark-v6x','ark','https://docs.arkelectron.com/products/flight-controller/arkv6x.md'),
 ('holybro-v6x','holybro','https://docs.holybro.com/autopilot/pixhawk-6x/technical-specification.md'),
 ('doodle-products','doodlelabs','https://doodlelabs.com/products/'),
 ('doodle-integration','doodlelabs','https://kb.doodlelabs.com/platform-integration-guide-voxl-and-skynode'),
 ('dji-h30','dji','https://www.dji.com/support/product/zenmuse-h30-series'),
 ('dji-m400','dji','https://enterprise.dji.com/matrice-400/specs'),
 ('mavlink-camera','mavlink','https://mavlink.io/en/services/camera.html'),
 ('mavlink-gimbal','mavlink','https://mavlink.io/en/services/gimbal_v2.html'),
 ('mavlink-timesync','mavlink','https://mavlink.io/en/services/timesync.html'),
 ('gstreamer-webrtc','gstreamer','https://gstreamer.freedesktop.org/documentation/webrtc/index.html'),
 ('rtp-rfc','ietf','https://www.rfc-editor.org/rfc/rfc3550.html'),
]
def one(item):
 key,origin,url=item;p=R/'snapshots'/(key+'.html');result={'id':key,'origin':origin,'url':url,'capturedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 if p.exists():return {**result,'status':'REFUSED_EXISTING_SNAPSHOT'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'AERIS-RD-Research/1.0 (public technical documentation)','Accept':'text/html,text/plain;q=0.9'})
  with urllib.request.urlopen(req,timeout=12) as response:
   content=response.headers.get('Content-Type','');data=response.read(2*2**20+1);final=response.url
  if len(data)>2*2**20:raise ValueError('CAPTURE_2MIB_BOUND')
  if not any(t in content for t in ['text/','json','xml']):raise ValueError('NOT_TEXT_DOCUMENT:'+content)
  data.decode('utf-8')
  p.write_bytes(data);return {**result,'status':'CAPTURED','resolvedUrl':final,'contentType':content,'snapshot':p.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 except Exception as e:return {**result,'status':'FAILED','error':str(e)}
def main():
 if shutil.disk_usage(R).free<20*2**30+64*2**20:raise ValueError('DISK_FLOOR')
 (R/'snapshots').mkdir(exist_ok=True)
 target=R/'sources.json'
 if target.exists():raise ValueError('MANIFEST_EXISTS_NO_OVERWRITE')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:results=list(pool.map(one,SOURCES))
 target.write_text(json.dumps({'scope':'public manufacturer/protocol claims; no hardware verification','sources':results},indent=2)+'\n')
 print(json.dumps({'captured':sum(x['status']=='CAPTURED' for x in results),'failed':[x for x in results if x['status']!='CAPTURED'],'bytes':sum(x.get('bytes',0) for x in results)},indent=2))
if __name__=='__main__':main()
