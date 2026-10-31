package vn.rtr.aeris.control01;
import java.nio.*;
import vn.rtr.aeris.beta01runtime.Mavlink;
/** FixedRCMAP1/2/3/4: roll-right+, pitch-forward+, throttle-up+, yaw-CW+. */
public final class RcWire {
    private static byte[] payload(int roll,int pitch,int throttle,int yaw){byte[]p=new byte[38];ByteBuffer b=ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);for(int o=0;o<38;o+=2)b.putShort(o,(short)65535);b.putShort(0,(short)roll);b.putShort(2,(short)pitch);b.putShort(4,(short)throttle);b.putShort(6,(short)yaw);p[16]=42;p[17]=1;return p;}
    public static byte[] pilot(int sequence,ControlAuthority.Input i){return Mavlink.packet(70,payload(pwm(i.axis(0)),pwm(-i.axis(1)),pwm(i.axis(2)),pwm(i.axis(3))),sequence);}
    private static int pwm(double a){if(!Double.isFinite(a)||a< -1||a>1)throw new IllegalArgumentException("RC_AXIS_DOMAIN");return (int)Math.round(1500+125*a);}
    public static byte[] neutral(int sequence){return Mavlink.packet(70,payload(1500,1500,1500,1500),sequence);}
    public static byte[] release(int sequence){byte[]p=payload(0,0,0,0);ByteBuffer b=ByteBuffer.wrap(p).order(ByteOrder.LITTLE_ENDIAN);for(int o=8;o<16;o+=2)b.putShort(o,(short)0);for(int o=18;o<38;o+=2)b.putShort(o,(short)65534);return Mavlink.packet(70,p,sequence);}
}
