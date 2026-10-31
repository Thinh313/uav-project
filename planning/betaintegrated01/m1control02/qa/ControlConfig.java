package vn.rtr.aeris.control01;
import java.util.*;import vn.rtr.aeris.betaintegrated01.*;
/** Test-only immutable config carrier; production JSON/Android parser is not tested here. */
public final class ControlConfig {
 public final RunLifecycle.Context context;public final ProviderDescriptor expected;public final ProviderDescriptor.Observation observed;public final Map<String,int[]>typed;public final String provenance="ROOT_INJECTED_ANDROID_TOUCH";public final long durationNs=10000000000L;
 public ControlConfig(String name,Map<String,int[]>typed){this.typed=typed;context=new RunLifecycle.Context(name,"epoch01","boot01","operator01","generation01","qa-profile");String a=String.join("",Collections.nCopies(64,"1")),b=String.join("",Collections.nCopies(64,"2")),c=String.join("",Collections.nCopies(64,"3"));expected=new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"qa-profile",a,b,c,"tcp://10.0.2.2:5961","4.7.1");observed=new ProviderDescriptor.Observation(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,"qa-profile",a,b,c,"tcp://10.0.2.2:5961","4.7.1",true);}
}
