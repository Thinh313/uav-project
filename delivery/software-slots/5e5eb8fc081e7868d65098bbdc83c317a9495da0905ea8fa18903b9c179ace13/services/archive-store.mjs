import {open,mkdir,link,unlink} from 'node:fs/promises';
import path from 'node:path';import {randomUUID} from 'node:crypto';
export class ArchiveStore {
 async syncDirectory(directory){const f=await open(directory,'r');try{await f.sync();}finally{await f.close();}}
 async append(file,bytes,{first=false}={}){const f=await open(file,first?'wx':'a');try{let at=0;while(at<bytes.length){const {bytesWritten}=await f.write(bytes,at,bytes.length-at);if(!bytesWritten)throw Error('Zero-byte journal write');at+=bytesWritten;}await f.sync();}finally{await f.close();}if(first)await this.syncDirectory(path.dirname(file));}
 async publish(file,bytes){const temp=file+'.pending-'+randomUUID();await this.append(temp,bytes,{first:true});await link(temp,file);await this.syncDirectory(path.dirname(file));await unlink(temp);await this.syncDirectory(path.dirname(file));}
 async promote(temp,file){await link(temp,file);await this.syncDirectory(path.dirname(file));await unlink(temp);await this.syncDirectory(path.dirname(file));}
 async lock(file,bytes){await this.append(file,bytes,{first:true});}
}
