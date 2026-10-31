import{Takeoff01}from'./takeoff.mjs';
import{Decoder}from'../../services/mavlink.mjs';
export function initialTakeoffProof(rows,plan){const t=new Takeoff01(plan),rx=new Decoder(),tx=new Decoder();let begun=false,home=null;
 for(const row of rows){const meta={record:row.n,hostMonoMs:Number(BigInt(row.hostNs))/1e6};if(row.kind==='POST_ARM_HOME_REVIEW_REQUIRED')home=row.data.postArmHome;
 if(row.kind==='TX_RAW')for(const m of tx.push(Buffer.from(row.data.rawHex,'hex')))if(!begun&&m.id===76&&m.fields.command===176&&m.fields.param2===3){begun=true;t.begin(meta,home);}
 if(row.kind==='RX_RAW')for(const m of rx.push(Buffer.from(row.data.rawHex,'hex')))t.feed(m,meta);
 }return t.view();}
