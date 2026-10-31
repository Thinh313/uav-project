package vn.rtr.aeris.betaintegrated01;

import java.net.URI;
import java.util.Objects;

/** Structural binding only. No authentication, socket, aircraft state or grant. */
public final class ProviderDescriptor {
    public enum Mode { INTERNAL_REGRESSION, EXTERNAL_REGRESSION, CANDIDATE_EXTERNAL }
    public static final String INTERNAL_AP = "011627d41dd95640c3aca02d45283474be48721c8b1bb7a4b234d38b69063482";
    public static final String EXTERNAL_AP = "f2be1f349f84b4aedaa5912b3050f64f476f3218bc4f68b34ad4de11393c2d08";
    public final int version;
    public final Mode mode;
    public final String profileId, binarySHA256, modelSHA256, configSHA256, endpoint, firmware;

    public ProviderDescriptor(int version, Mode mode, String profileId, String binarySHA256,
                              String modelSHA256, String configSHA256, String endpoint,
                              String firmware) {
        if (version != 1 || mode == null) fail("PROVIDER_VERSION_MODE");
        identifier(profileId); hash(binarySHA256, true); hash(modelSHA256, true);
        hash(configSHA256, false); endpoint(endpoint);
        if (!"4.7.1".equals(firmware)) fail("DECLARED_FIRMWARE_REQUIRED");
        if (mode == Mode.INTERNAL_REGRESSION && (!INTERNAL_AP.equals(binarySHA256) || modelSHA256 != null))
            fail("INTERNAL_REGRESSION_BINDING");
        if (mode == Mode.EXTERNAL_REGRESSION && (!EXTERNAL_AP.equals(binarySHA256) || modelSHA256 == null))
            fail("EXTERNAL_REGRESSION_BINDING");
        if (mode == Mode.CANDIDATE_EXTERNAL && (INTERNAL_AP.equals(binarySHA256) || EXTERNAL_AP.equals(binarySHA256)))
            fail("BASELINE_BINARY_IS_NOT_NEW_CANDIDATE");
        this.version=version; this.mode=mode; this.profileId=profileId;
        this.binarySHA256=binarySHA256; this.modelSHA256=modelSHA256;
        this.configSHA256=configSHA256; this.endpoint=endpoint; this.firmware=firmware;
    }
    public Binding validateObserved(Observation observed) {
        if (binarySHA256 == null || (mode != Mode.INTERNAL_REGRESSION && modelSHA256 == null))
            fail("UNBUILT_OR_UNPINNED_CANDIDATE");
        if (observed == null || observed.version != version || observed.mode != mode ||
            !profileId.equals(observed.profileId) || !binarySHA256.equals(observed.binarySHA256) ||
            !Objects.equals(modelSHA256, observed.modelSHA256) || !configSHA256.equals(observed.configSHA256) ||
            !endpoint.equals(observed.endpoint) || !firmware.equals(observed.firmware) ||
            !observed.emulator) fail("OBSERVED_PROVIDER_BINDING_MISMATCH");
        return new Binding(this);
    }
    public static final class Observation {
        public final int version; public final Mode mode;
        public final String profileId,binarySHA256,modelSHA256,configSHA256,endpoint,firmware;
        public final boolean emulator;
        public Observation(int version, Mode mode, String profileId, String binarySHA256,
                           String modelSHA256, String configSHA256, String endpoint,
                           String firmware, boolean emulator) {
            this.version=version;this.mode=mode;this.profileId=profileId;this.binarySHA256=binarySHA256;
            this.modelSHA256=modelSHA256;this.configSHA256=configSHA256;this.endpoint=endpoint;
            this.firmware=firmware;this.emulator=emulator;
        }
    }
    public static final class Binding {
        public final ProviderDescriptor descriptor;
        public final String scope="STRUCTURAL_CALLER_OBSERVATION_NOT_AUTHENTICATION_OR_AIRCRAFT_SAFE";
        private Binding(ProviderDescriptor descriptor) { this.descriptor=descriptor; }
    }
    static void identifier(String s) { if(s==null||!s.matches("[A-Za-z0-9_.:-]{1,128}"))fail("IDENTIFIER_BOUND"); }
    static void hash(String s,boolean nullable) { if(s==null&&nullable)return; if(s==null||!s.matches("[0-9a-f]{64}"))fail("HASH_REQUIRED"); }
    private static void endpoint(String s) {
        try {
            URI u=new URI(s);
            if(!"tcp".equals(u.getScheme()) || !("127.0.0.1".equals(u.getHost()) || "10.0.2.2".equals(u.getHost())) ||
               u.getPort()<1024||u.getPort()>65535||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null||
               (u.getRawPath()!=null&&!u.getRawPath().isEmpty()))fail("LOOPBACK_EMULATOR_ENDPOINT_ONLY");
        } catch(Exception e) { throw new IllegalArgumentException("PROVIDER_ENDPOINT",e); }
    }
    private static void fail(String s) { throw new IllegalArgumentException(s); }
}
