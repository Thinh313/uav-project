package vn.rtr.aeris.operator01;
/** Byte-exact lower-case encoding with a fixed two chars per byte. */
public final class Hex98{private static final char[]DIGITS="0123456789abcdef".toCharArray();private Hex98(){}public static String encode(byte[]bytes){char[]out=new char[bytes.length*2];for(int i=0;i<bytes.length;i++){int value=bytes[i]&255;out[i*2]=DIGITS[value>>>4];out[i*2+1]=DIGITS[value&15];}return new String(out);}}
