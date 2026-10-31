package vn.rtr.aeris.crew02;
import java.io.*;import java.net.*;
/** One bounded frame with a deadline that cannot be extended by drip bytes. */
public final class FrameIO02{
 public interface Clock{long now();}
 public static byte[]read(Socket socket,Clock clock)throws IOException{InputStream in=socket.getInputStream();long first=-1;byte[]h=new byte[4];int p=0;while(p<4){if(first>=0&&clock.now()-first>=3000)throw new IOException("CREW_FRAME_DEADLINE");int b;socket.setSoTimeout(first<0?500:(int)Math.max(1,3000-(clock.now()-first)));try{b=in.read();}catch(SocketTimeoutException e){if(first<0)throw e;continue;}if(b<0)throw new EOFException("CREW_EOF");if(first<0)first=clock.now();h[p++]=(byte)b;}long n=((h[0]&255L)<<24)|((h[1]&255L)<<16)|((h[2]&255L)<<8)|(h[3]&255L);if(n<1||n>16384)throw new IOException("CREW_FRAME_BOUND");byte[]b=new byte[(int)n];p=0;while(p<n){if(clock.now()-first>=3000)throw new IOException("CREW_FRAME_DEADLINE");socket.setSoTimeout((int)Math.max(1,3000-(clock.now()-first)));try{int got=in.read(b,p,b.length-p);if(got<0)throw new EOFException("CREW_EOF");p+=got;}catch(SocketTimeoutException e){}}if(clock.now()-first>3000)throw new IOException("CREW_FRAME_DEADLINE");return b;}
 public static void write(Socket socket,byte[]b)throws IOException{if(b.length<1||b.length>32768)throw new IOException("CREW_RESPONSE_BOUND");OutputStream out=socket.getOutputStream();out.write(new byte[]{(byte)(b.length>>24),(byte)(b.length>>16),(byte)(b.length>>8),(byte)b.length});out.write(b);out.flush();}
 private FrameIO02(){}
}
