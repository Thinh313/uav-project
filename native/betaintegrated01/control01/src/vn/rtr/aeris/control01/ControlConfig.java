package vn.rtr.aeris.control01;
import java.io.*;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.json.*;
import vn.rtr.aeris.betaintegrated01.*;
import vn.rtr.aeris.beta01runtime.Values;

public final class ControlConfig {
    public interface Asset {byte[] read(String name)throws Exception;}
    public final ProviderDescriptor expected;public final ProviderDescriptor.Observation observed;public final RunLifecycle.Context context;
    public final Map<String,int[]> typed=new LinkedHashMap<>();public final String provenance;public final long durationNs;
    public ControlConfig(byte[]expectedBytes,byte[]observedBytes,String expectedObservedSHA,Asset asset)throws Exception{
        if(expectedObservedSHA==null||!expectedObservedSHA.matches("[0-9a-f]{64}")||!Values.hash(observedBytes).equals(expectedObservedSHA))throw new IOException("ROOT_OBSERVED_BINDING_SHA_REQUIRED");
        JSONObject all=new JSONObject(new String(expectedBytes,StandardCharsets.UTF_8)),o=new JSONObject(new String(observedBytes,StandardCharsets.UTF_8));
        if(all.getInt("version")!=1||o.getInt("version")!=1||!o.getBoolean("rootOwnedContainer")||o.getInt("targetSystem")!=42)throw new IOException("CONTROL_ROOT_CONTEXT");
        String profileId=o.getString("profileId");JSONObject p=all.getJSONObject("profiles").getJSONObject(profileId);
        if(!"CANDIDATE_EXTERNAL".equals(p.getString("mode"))||!"M1_CONTROL01_NO_MEDIA".equals(p.getString("capabilityProfile"))||!p.getBoolean("manualCapability"))throw new IOException("CONTROL_PROFILE_REQUIRED");
        expected=new ProviderDescriptor(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,profileId,p.getString("binarySHA256"),p.getString("modelSHA256"),p.getString("configSHA256"),p.getString("endpoint"),p.getString("firmware"));
        if(!"tcp://10.0.2.2:5961".equals(expected.endpoint)||!"CANDIDATE_EXTERNAL".equals(o.getString("mode")))throw new IOException("CONTROL_EMULATOR_ENDPOINT");
        observed=new ProviderDescriptor.Observation(1,ProviderDescriptor.Mode.CANDIDATE_EXTERNAL,profileId,o.getString("binarySHA256"),o.getString("modelSHA256"),o.getString("configSHA256"),o.getString("endpoint"),o.getString("firmware"),true);expected.validateObserved(observed);
        context=new RunLifecycle.Context(o.getString("run"),o.getString("epoch"),o.getString("boot"),o.getString("operator"),o.getString("generation"),profileId);
        provenance=o.getString("inputProvenance");if(!Arrays.asList("ROOT_INJECTED_ANDROID_TOUCH","LOCAL_ANDROID_TOUCH_NOT_HID_ATTESTED").contains(provenance))throw new IOException("INPUT_PROVENANCE_REQUIRED");
        int seconds=p.getInt("durationSeconds");if(seconds<10||seconds>180)throw new IOException("CONTROL_DURATION_BOUND");durationNs=seconds*1000000000L;
        String file=p.getString("typedAsset");if(!file.matches("[a-z0-9-]+\\.json"))throw new IOException("TYPED_ASSET_PATH");byte[]bytes=asset.read(file);if(!Values.hash(bytes).equals(p.getString("typedSHA256")))throw new IOException("TYPED_PROFILE_SHA");JSONObject t=new JSONObject(new String(bytes,StandardCharsets.UTF_8));if(!profileId.equals(t.getString("id")))throw new IOException("TYPED_PROFILE_ID");JSONObject params=t.getJSONObject("parameters");Iterator<String>names=params.keys();while(names.hasNext()){String name=names.next();JSONObject spec=params.getJSONObject(name);String hex=spec.getString("float32Hex");if(!hex.matches("[a-f0-9]{8}"))throw new IOException("TYPED_FLOAT_BITS");byte[] b=new byte[4];for(int i=0;i<4;i++)b[i]=(byte)Integer.parseInt(hex.substring(i*2,i*2+2),16);typed.put(name,new int[]{spec.getInt("mavType"),ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).getInt()});}
        if(typed.size()!=39)throw new IOException("EXACT_CONTROL_TYPED_COUNT");
    }
}
