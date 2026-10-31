import vn.rtr.aeris.control01.*;
import vn.rtr.aeris.betaintegrated01.RunLifecycle;
import java.nio.*;
public final class ControlWireBuilderTest {
    static int checks;
    static void ok(boolean b){checks++;if(!b)throw new AssertionError("check"+checks);}
    static int channel(byte[]b,int n){return Short.toUnsignedInt(ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).getShort(10+(n<=8?(n-1)*2:18+(n-9)*2)));}
    static ControlAuthority.Input input(double...axes){return new ControlAuthority.Input(new RunLifecycle.Context("run","epoch","boot","operator","generation","profile"),"touch-00000000-0000-0000-0000-000000000000","ANDROID_UPTIME_NS_SAMPLER","ROOT_INJECTED_ANDROID_TOUCH",1,1000000,2000000,1000000,axes,2,2,false);}
    public static void main(String[]args){
        byte[]p=RcWire.pilot(0,input(1,1,1,1));ok(channel(p,1)==1625);ok(channel(p,2)==1375);ok(channel(p,3)==1625);ok(channel(p,4)==1625);
        p=RcWire.pilot(1,input(-1,-1,-1,-1));ok(channel(p,1)==1375);ok(channel(p,2)==1625);ok(channel(p,3)==1375);ok(channel(p,4)==1375);
        p=RcWire.neutral(2);for(int i=1;i<=4;i++)ok(channel(p,i)==1500);
        p=RcWire.release(3);for(int i=1;i<=8;i++)ok(channel(p,i)==0);for(int i=9;i<=18;i++)ok(channel(p,i)==65534);ok((p[26]&255)==42&&(p[27]&255)==1);
        boolean rejected=false;try{RcWire.pilot(4,input(Double.NaN,0,0,0));}catch(IllegalArgumentException expected){rejected=true;}ok(rejected);
        System.out.println("{\"status\":\"PASS\",\"checks\":"+checks+",\"scope\":\"EXPLICIT_FOUR_AXIS_PWM_AND_RELEASE_MAPPING_HOST_JVM\"}");
    }
}
