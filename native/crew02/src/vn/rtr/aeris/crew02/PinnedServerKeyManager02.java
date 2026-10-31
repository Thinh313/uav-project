package vn.rtr.aeris.crew02;
import java.io.IOException;import java.net.Socket;import java.security.*;import java.security.cert.*;import java.util.*;import javax.net.ssl.*;
/** Retained historical keys are never offered as a fallback TLS server identity. */
public final class PinnedServerKeyManager02 extends X509ExtendedKeyManager{
 private final X509KeyManager delegate;private final byte[]certificate;
 private PinnedServerKeyManager02(X509KeyManager delegate,X509Certificate current)throws CertificateEncodingException{this.delegate=delegate;certificate=current.getEncoded();}
 public static PinnedServerKeyManager02 select(KeyManager[]managers,X509Certificate current)throws Exception{for(KeyManager m:managers)if(m instanceof X509KeyManager){PinnedServerKeyManager02 pin=new PinnedServerKeyManager02((X509KeyManager)m,current);String[]a=pin.getServerAliases("EC",null);if(a!=null&&a.length>0)return pin;}throw new IOException("CREW_CURRENT_TLS_KEY_UNAVAILABLE");}
 private boolean matches(String alias){if(alias==null)return false;try{X509Certificate[]c=delegate.getCertificateChain(alias);return c!=null&&c.length==1&&Arrays.equals(certificate,c[0].getEncoded());}catch(CertificateEncodingException e){return false;}}
 public String[]getServerAliases(String keyType,Principal[]issuers){String[]offered=delegate.getServerAliases(keyType,issuers);if(offered==null)return null;ArrayList<String>valid=new ArrayList<>();for(String a:offered)if(matches(a))valid.add(a);return valid.isEmpty()?null:valid.toArray(new String[0]);}
 public String chooseServerAlias(String keyType,Principal[]issuers,Socket socket){String[]a=getServerAliases(keyType,issuers);return a==null?null:a[0];}
 public String chooseEngineServerAlias(String keyType,Principal[]issuers,SSLEngine engine){return chooseServerAlias(keyType,issuers,null);}
 public X509Certificate[]getCertificateChain(String alias){if(!matches(alias))return null;return delegate.getCertificateChain(alias).clone();}
 public PrivateKey getPrivateKey(String alias){return matches(alias)?delegate.getPrivateKey(alias):null;}
 public String[]getClientAliases(String keyType,Principal[]issuers){return null;}public String chooseClientAlias(String[]keyType,Principal[]issuers,Socket socket){return null;}public String chooseEngineClientAlias(String[]keyType,Principal[]issuers,SSLEngine engine){return null;}
}
