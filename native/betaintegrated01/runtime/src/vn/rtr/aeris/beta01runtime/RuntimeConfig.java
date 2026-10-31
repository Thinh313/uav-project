package vn.rtr.aeris.beta01runtime;
import java.io.*;
import java.nio.charset.StandardCharsets;
import org.json.*;
import vn.rtr.aeris.betaintegrated01.*;
/** Root-owned launch observations are explicit local trust, not remote authenticity. */
public final class RuntimeConfig {
    public final ProviderDescriptor expected;public final ProviderDescriptor.Observation observed;
    public final RunLifecycle.Context context;public final long durationNs;public final boolean manualCapability;
    public RuntimeConfig(String expectedJSON,byte[] observedBytes,String expectedObservedSHA)throws Exception {
        if(expectedObservedSHA==null||!expectedObservedSHA.matches("[0-9a-f]{64}")||!Values.hash(observedBytes).equals(expectedObservedSHA))throw new IOException("OBSERVED_LAUNCH_SHA_REQUIRED");
        JSONObject e=new JSONObject(expectedJSON),o=new JSONObject(new String(observedBytes,StandardCharsets.UTF_8));
        if(e.getInt("version")!=1||o.getInt("version")!=1||!o.getBoolean("rootOwnedContainer")||o.getInt("targetSystem")!=42||!"CANDIDATE_EXTERNAL".equals(e.getString("mode"))||!"CANDIDATE_EXTERNAL".equals(o.getString("mode"))||!"NO_MEDIA_M1_RUNTIME".equals(e.getString("capabilityProfile")))throw new IOException("M1_PROFILE_VERSION_OBSERVATION");
        expected=new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,e.getString("profileId"),e.getString("binarySHA256"),e.getString("modelSHA256"),e.getString("configSHA256"),e.getString("endpoint"),e.getString("firmware"));
        if(!"tcp://10.0.2.2:5961".equals(expected.endpoint))throw new IOException("OWNED_EMULATOR_ENDPOINT_ONLY");
        observed=new ProviderDescriptor.Observation(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,o.getString("profileId"),o.getString("binarySHA256"),o.getString("modelSHA256"),o.getString("configSHA256"),o.getString("endpoint"),o.getString("firmware"),true);
        expected.validateObserved(observed);
        context=new RunLifecycle.Context(o.getString("run"),o.getString("epoch"),o.getString("boot"),o.getString("operator"),o.getString("generation"),expected.profileId);
        int seconds=e.getInt("durationSeconds");if(seconds<10||seconds>1800)throw new IOException("DURATION_BOUND");durationNs=seconds*1000000000L;
        manualCapability=e.getBoolean("manualCapability");
    }
}
