package vn.rtr.aeris.native94;
import java.io.*;import java.security.*;
/** Streaming bounded transport/checksum, no unbounded archive buffers. */
public final class BundleIO88{
 public static final long MAX=64L*1024*1024;
 public static String copy(InputStream in,OutputStream out,long expected,String sha)throws Exception{if(expected<1||expected>MAX||!sha.matches("[a-f0-9]{64}"))throw new IOException("BUNDLE_DESCRIPTOR_BOUND");MessageDigest m=MessageDigest.getInstance("SHA-256");byte[] b=new byte[16384];long total=0;int n;while((n=in.read(b))!=-1){total+=n;if(total>expected)throw new IOException("BUNDLE_LENGTH_OVERFLOW");m.update(b,0,n);if(out!=null)out.write(b,0,n);}StringBuilder s=new StringBuilder();for(byte v:m.digest())s.append(String.format("%02x",v&255));if(total!=expected||!s.toString().equals(sha))throw new IOException("BUNDLE_LENGTH_OR_SHA_MISMATCH");return s.toString();}
}
