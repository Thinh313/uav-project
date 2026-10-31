package vn.rtr.aeris.native95;
public final class Json {private Json(){}public static String quote(String s){if(s==null)return "null";StringBuilder b=new StringBuilder("\"");for(char c:s.toCharArray()){if(c=='"'||c=='\\')b.append('\\').append(c);else if(c<32)b.append(String.format(java.util.Locale.ROOT,"\\u%04x",(int)c));else b.append(c);}return b.append('"').toString();}}
