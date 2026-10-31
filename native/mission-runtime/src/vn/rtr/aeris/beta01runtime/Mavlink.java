package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.nio.*;
import java.util.*;
import vn.rtr.aeris.native98.Dialect95;
/** Exact Native98 dialect; bounded independent telemetry view, never a second sender. */
public final class Mavlink {
    public interface Sink {void frame(int id,int sys,int comp,int sequence,byte[] payload)throws Exception;}
    private byte[] pending=new byte[0];private int noise;
    public static int u8(byte[] p,int o){return p[o]&255;}
    public static int u16(byte[] p,int o){return u8(p,o)|u8(p,o+1)<<8;}
    public static long u32(byte[]p,int o){return Integer.toUnsignedLong(ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).getInt(o));}
    public static int i32(byte[]p,int o){return ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).getInt(o);}
    public static float f32(byte[]p,int o){return ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN).getFloat(o);}
    public static int crc(byte[] b,int end,int extra){int c=65535;for(int i=1;i<=end;i++){int v=i==end?extra:u8(b,i),t=v^(c&255);t^=t<<4&255;c=(c>>8^t<<8^t<<3^t>>4)&65535;}return c;}
    public static byte[] packet(int id,byte[] payload,int sequence) {
        int[] d=Dialect95.D.get(id);if(d==null||payload.length!=d[1])throw new IllegalArgumentException("MAV_PAYLOAD");
        int len=payload.length;while(len>1&&payload[len-1]==0)len--;
        byte[] b=new byte[12+len];b[0]=(byte)253;b[1]=(byte)len;b[4]=(byte)sequence;b[5]=(byte)255;b[6]=(byte)190;b[7]=(byte)id;b[8]=(byte)(id>>8);b[9]=(byte)(id>>16);System.arraycopy(payload,0,b,10,len);int c=crc(b,10+len,d[2]);b[10+len]=(byte)c;b[11+len]=(byte)(c>>8);return b;
    }
    public static byte[] heartbeat(int sequence){byte[]p=new byte[9];p[4]=6;p[5]=8;p[7]=4;p[8]=3;return packet(0,p,sequence);}
    public static byte[] command(int seq,int command,float... values){byte[]p=new byte[33];ByteBuffer b=ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);for(int i=0;i<values.length&&i<7;i++)b.putFloat(i*4,values[i]);b.putShort(28,(short)command);p[30]=42;p[31]=1;return packet(76,p,seq);}
    public static byte[] parameter(int seq,String name){byte[]p=new byte[20];p[0]=(byte)255;p[1]=(byte)255;p[2]=42;p[3]=1;byte[]n=name.getBytes(java.nio.charset.StandardCharsets.US_ASCII);if(n.length>16)throw new IllegalArgumentException("PARAM_NAME");System.arraycopy(n,0,p,4,n.length);return packet(20,p,seq);}
    public static byte[] override(int seq,int roll,int pitch,int throttle,int yaw){byte[]p=new byte[38];ByteBuffer b=ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);b.putShort(0,(short)roll);b.putShort(2,(short)pitch);b.putShort(4,(short)throttle);b.putShort(6,(short)yaw);for(int i=8;i<16;i+=2)b.putShort(i,(short)65535);p[16]=42;p[17]=1;return packet(70,p,seq);}
    public void receive(byte[] raw,Sink sink)throws Exception {
        if(raw.length>8192)throw new IOException("RX_BLOCK_BOUND");byte[]b=new byte[pending.length+raw.length];System.arraycopy(pending,0,b,0,pending.length);System.arraycopy(raw,0,b,pending.length,raw.length);int o=0;
        while(o<b.length){int magic=u8(b,o);if(magic!=253&&magic!=254){if(++noise>1024)throw new IOException("BANNER_BOUND");o++;continue;}if(b.length-o<2)break;int h=magic==253?10:6;if(b.length-o<h)break;int len=u8(b,o+1),id=magic==253?u8(b,o+7)|u8(b,o+8)<<8|u8(b,o+9)<<16:u8(b,o+5),n=h+len+2;int[]d=Dialect95.D.get(id);if(d==null||len<1||len>d[1]||(magic==254&&len!=d[0])||(magic==253&&u8(b,o+2)!=0))throw new IOException("MAV_FLAGS_LENGTH");if(b.length-o<n)break;byte[]f=Arrays.copyOfRange(b,o,o+n);if(crc(f,h+len,d[2])!=u16(f,h+len))throw new IOException("MAV_CRC");byte[]p=new byte[d[1]];System.arraycopy(f,h,p,0,len);sink.frame(id,u8(f,magic==253?5:3),u8(f,magic==253?6:4),u8(f,magic==253?4:2),p);o+=n;}
        pending=Arrays.copyOfRange(b,o,b.length);if(pending.length>280)throw new IOException("MAV_PENDING_BOUND");
    }
    public int pendingBytes(){return pending.length;}
}
