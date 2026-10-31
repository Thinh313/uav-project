package vn.rtr.aeris.control01;
import java.util.*;import vn.rtr.aeris.betaintegrated01.*;
/** TEST-ONLY fixture for actual Owner loop; not packaged or Android config parsing proof. */
public final class ControlConfig {
 public final ProviderDescriptor expected;public final ProviderDescriptor.Observation observed;public final RunLifecycle.Context context;public final Map<String,int[]>typed;public final String provenance="ROOT_INJECTED_ANDROID_TOUCH";public final long durationNs=10000000000L;
 public ControlConfig(String run,Map<String,int[]>typed){String a=String.join("",Collections.nCopies(64,"1")),b=String.join("",Collections.nCopies(64,"2")),c=String.join("",Collections.nCopies(64,"3"));context=new RunLifecycle.Context(run,"epoch","boot","operator","generation","owner-close-test");expected=new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"owner-close-test",a,b,c,"tcp://10.0.2.2:5961","4.7.1");observed=new ProviderDescriptor.Observation(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"owner-close-test",a,b,c,"tcp://10.0.2.2:5961","4.7.1",true);this.typed=typed;}
}
